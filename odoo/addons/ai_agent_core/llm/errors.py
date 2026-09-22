# -*- coding: utf-8 -*-
"""Clasificación de los fallos de un proveedor y política de reintento.

Cada fallo se reduce a un *tipo*, y el tipo decide qué pasa después:

* reintentar con backoff (solo ``rate_limited``);
* degradar al siguiente proveedor de la cadena (``FALLBACK_KINDS``);
* dejar al proveedor en pausa unos minutos para no insistir sobre algo
  caído (``COOLDOWN_KINDS``);
* o devolver el error tal cual, porque otro proveedor fallaría igual y el
  fallback solo taparía el problema (``bad_request``, ``content_filtered``).

Los marcadores de texto salen de respuestas reales: una API no distingue
con el código HTTP una clave inválida de un bloqueo por país (las dos son
403 en Groq y en Abacus), ni una cuota agotada de un pico de uso (las dos
son 429 en Gemini y en OpenAI).
"""
import email.utils
import json
import random
import re
import time
from collections.abc import Mapping

from odoo.exceptions import UserError

RATE_LIMITED = 'rate_limited'
QUOTA_EXHAUSTED = 'quota_exhausted'
AUTH = 'auth'
GEOBLOCKED = 'geoblocked'
UNAVAILABLE = 'unavailable'
MODEL_UNAVAILABLE = 'model_unavailable'
BAD_REQUEST = 'bad_request'
CONTENT_FILTERED = 'content_filtered'
INVALID_RESPONSE = 'invalid_response'
CONFIG = 'config'

ERROR_KINDS = [
    (RATE_LIMITED, 'Límite de uso (429)'),
    (QUOTA_EXHAUSTED, 'Sin saldo o cuota'),
    (AUTH, 'Credencial inválida o vencida'),
    (GEOBLOCKED, 'Bloqueo por red o país'),
    (UNAVAILABLE, 'Sin conexión o servicio caído'),
    (MODEL_UNAVAILABLE, 'Modelo no disponible'),
    (BAD_REQUEST, 'Petición rechazada'),
    (CONTENT_FILTERED, 'Bloqueado por filtro de contenido'),
    (INVALID_RESPONSE, 'Respuesta inesperada'),
    (CONFIG, 'Configuración incompleta'),
]

# Tipos ante los que otro proveedor sí puede resolver la petición.
FALLBACK_KINDS = frozenset({
    RATE_LIMITED, QUOTA_EXHAUSTED, AUTH, GEOBLOCKED, UNAVAILABLE,
    MODEL_UNAVAILABLE, INVALID_RESPONSE, CONFIG,
})
# Tipos que no se arreglan en segundos: el proveedor se salta durante su
# pausa. CONFIG no, porque detectarlo no cuesta ninguna llamada de red.
COOLDOWN_KINDS = frozenset({QUOTA_EXHAUSTED, AUTH, GEOBLOCKED, UNAVAILABLE})

GEOBLOCK_MARKERS = (
    'unsupported_country', 'country, region, or territory',
    'user location is not supported', 'location is not supported',
    'not available in your region', 'not available in your country',
    'region is not supported', 'check your network settings',
)
QUOTA_MARKERS = (
    'insufficient_quota', 'insufficient balance', 'insufficient credits',
    'credit balance is too low', 'limit: 0', 'billing_hard_limit',
)
AUTH_MARKERS = (
    'invalid api key', 'invalid_api_key', 'api key not valid',
    'incorrect api key', 'authentication fails', 'unauthorized',
)
MODEL_MARKERS = (
    'model_not_found', 'model not found', 'does not exist', 'decommissioned',
    'is not a valid model', 'invalid model', 'no endpoints found',
)
CONTENT_MARKERS = ('content_policy_violation', 'content_filter')

RETRY_DELAY_BODY_RES = (
    re.compile(r'"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"'),
    re.compile(r'retry in (\d+(?:\.\d+)?)\s*s', re.IGNORECASE),
)


class AiProviderError(UserError):
    """Fallo de un proveedor de IA, ya clasificado.

    Hereda de UserError para que, si llega a la interfaz, se vea como un
    aviso legible y no como un traceback.
    """

    def __init__(self, message, kind, provider_name='', retry_after=None, status=None):
        super().__init__(message)
        self.kind = kind
        self.provider_name = provider_name
        self.retry_after = retry_after
        self.status = status


def _lower_headers(headers):
    if not isinstance(headers, Mapping):
        return {}
    return {str(k).lower(): v for k, v in headers.items()}


def parse_retry_after(headers=None, body_text=''):
    """Segundos que el proveedor pide esperar, o None.

    Primero la cabecera estándar ``Retry-After`` (segundos o fecha HTTP);
    si no está, el ``retryDelay`` que Gemini mete en el cuerpo.
    """
    value = _lower_headers(headers).get('retry-after')
    if value not in (None, ''):
        try:
            return max(0.0, float(value))
        except (TypeError, ValueError):
            try:
                parsed = email.utils.parsedate_to_datetime(str(value))
                return max(0.0, parsed.timestamp() - time.time())
            except (TypeError, ValueError, IndexError):
                pass
    for regex in RETRY_DELAY_BODY_RES:
        match = regex.search(body_text or '')
        if match:
            return float(match.group(1))
    return None


def classify_http_error(status, body_text='', headers=None):
    """Devuelve (tipo, segundos_de_espera_o_None) para una respuesta HTTP
    de error. El orden importa: el bloqueo por país y la cuota agotada se
    miran antes que el código, porque llegan con 403, 400 o 429."""
    text = (body_text or '').lower()
    retry_after = parse_retry_after(headers, body_text)
    if status == 451 or any(marker in text for marker in GEOBLOCK_MARKERS):
        return GEOBLOCKED, None
    if status == 402 or any(marker in text for marker in QUOTA_MARKERS):
        return QUOTA_EXHAUSTED, retry_after
    if status == 429:
        return RATE_LIMITED, retry_after
    if status in (401, 403) or any(marker in text for marker in AUTH_MARKERS):
        return AUTH, None
    if status == 404 or any(marker in text for marker in MODEL_MARKERS):
        return MODEL_UNAVAILABLE, None
    if status in (408, 409, 425) or status >= 500:
        return UNAVAILABLE, retry_after
    if any(marker in text for marker in CONTENT_MARKERS):
        return CONTENT_FILTERED, None
    return BAD_REQUEST, None


def backoff_delay(attempt, retry_after=None, base=1.0, cap=8.0, rng=random.random):
    """Espera antes del reintento número ``attempt`` (0 = primer reintento).

    Backoff exponencial con *full jitter* (espera al azar entre 0 y
    base·2^intento, con tope): reparte los reintentos de varios workers en
    vez de sincronizarlos contra el mismo límite. Si el proveedor dijo
    cuánto esperar, se respeta, más un jitter pequeño por el mismo motivo.
    """
    if retry_after is not None:
        return retry_after + rng() * base
    return rng() * min(cap, base * (2 ** attempt))


def error_text(response):
    """Mensaje de error legible de una respuesta, sea cual sea el formato:
    ``{"error": {"message"}}`` (OpenAI, Gemini, Groq), ``{"error": "..."}``
    (Abacus), ``{"detail": "..."}`` (Mistral) o texto plano."""
    try:
        data = response.json()
    except (ValueError, AttributeError, TypeError):
        data = None
    if isinstance(data, dict):
        error = data.get('error')
        if isinstance(error, dict) and error.get('message'):
            return str(error['message'])
        if isinstance(error, str):
            return error
        for key in ('detail', 'message'):
            if data.get(key):
                value = data[key]
                return value if isinstance(value, str) else json.dumps(value)[:500]
    return (getattr(response, 'text', '') or '')[:500]
