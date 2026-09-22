# -*- coding: utf-8 -*-
import base64
import logging
import re
import time
from datetime import timedelta

import requests
from lxml import etree

from odoo import api, fields, models, modules
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

from odoo.addons.ai_agent_core.llm import catalog as llm_catalog
from odoo.addons.ai_agent_core.llm.errors import (
    CONFIG,
    CONTENT_FILTERED,
    COOLDOWN_KINDS,
    ERROR_KINDS,
    FALLBACK_KINDS,
    INVALID_RESPONSE,
    RATE_LIMITED,
    UNAVAILABLE,
    AiProviderError,
    backoff_delay,
    classify_http_error,
    error_text,
)
from odoo.addons.ai_agent_core.llm.registry import (
    ANTHROPIC,
    GEMINI,
    OLLAMA,
    OPENAI,
    PROVIDER_SELECTION,
    SVG_IMAGE_PROVIDERS,
    protocol_of,
    provider_spec,
)
from odoo.addons.ai_agent_core.llm.usage import LlmResult, parse_usage
from odoo.addons.ai_agent_core.llm.vault import AiVault, VaultDecryptError, mask

_logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODELS_URL = "https://api.anthropic.com/v1/models"
ANTHROPIC_VERSION = "2023-06-01"
GEMINI_API_URL_TMPL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
# Imagen (imagen-4.0-*) no usa generateContent sino :predict, con otro
# formato de petición y de respuesta.
GEMINI_PREDICT_URL_TMPL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:predict"
)
GEMINI_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_BILLING_URL = "https://aistudio.google.com/apikey"
OPENAI_BILLING_URL = "https://platform.openai.com/settings/organization/billing"
OLLAMA_CLOUD_BASE_URL = "https://ollama.com"
OLLAMA_TAGS_PATH = "/api/tags"
OLLAMA_CHAT_PATH = "/api/chat"
OPENROUTER_APP_TITLE = "ARIA (Odoo)"

HEALTH_CHECK_TIMEOUT = 15
BACKOFF_BASE_SECONDS = 1.0
BACKOFF_CAP_SECONDS = 8.0

IMAGE_CAPABLE_PROVIDERS = tuple(code for code, _label in PROVIDER_SELECTION)

# Gemini no marca en el catálogo qué modelos generan imágenes: se deduce del
# id. "nano-banana-*" es el nombre comercial y no lleva "image" en el id.
GEMINI_IMAGE_MARKERS = ('image', 'imagen', 'banana')

# Claude, Ollama y los compatibles con OpenAI salvo el propio OpenAI no
# tienen API de generación de imágenes en este módulo (Ollama rechaza los
# modelos de imagen en /api/generate con "image generation models are not
# currently supported"). Para ellos el modelo de TEXTO dibuja la imagen
# como SVG, que se sanea y se rasteriza con wkhtmltoimage.
SVG_IMAGE_SIZE = 1080
SVG_IMAGE_MAX_TOKENS = 8000
SVG_IMAGE_TIMEOUT = 300
SVG_SYSTEM_PROMPT = (
    "Eres un diseñador gráfico que crea imágenes para redes sociales "
    "dibujándolas en SVG.\n"
    "Responde ÚNICAMENTE con un documento SVG completo y válido, sin "
    "explicaciones ni bloques de código markdown.\n"
    "Requisitos:\n"
    "- Etiqueta raíz: <svg xmlns=\"http://www.w3.org/2000/svg\" "
    "viewBox=\"0 0 %(size)s %(size)s\">.\n"
    "- Composición cuadrada, llamativa y profesional: degradados, formas, "
    "ilustración vectorial y una jerarquía visual clara.\n"
    "- Si incluyes texto, que sea breve (un titular de pocas palabras), "
    "grande, legible, con font-family sans-serif y dentro del lienzo.\n"
    "- Prohibido: <script>, <foreignObject>, <image>, animaciones y cualquier "
    "recurso externo (fuentes, imágenes o url() que no apunte a un id interno).\n"
    "- Todo debe caber en una sola respuesta: prefiere formas simples a "
    "trazados con miles de puntos."
) % {'size': SVG_IMAGE_SIZE}
SVG_FORBIDDEN_TAGS = {
    'script', 'foreignobject', 'image', 'iframe', 'a', 'animate',
    'animatemotion', 'animatetransform', 'set', 'audio', 'video',
}
# url(...) que no apunta a un id del propio documento (#degradado).
SVG_EXTERNAL_URL_RE = re.compile(r"url\(\s*(?!['\"]?\s*#)", re.IGNORECASE)


class AiProviderConfig(models.Model):
    _name = 'ai.provider.config'
    _description = 'Proveedor de IA para generación de contenido'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    provider = fields.Selection(PROVIDER_SELECTION, required=True, default='anthropic')
    protocol = fields.Selection(
        [
            (OPENAI, 'Compatible con OpenAI'),
            (ANTHROPIC, 'Anthropic'),
            (GEMINI, 'Gemini'),
            (OLLAMA, 'Ollama'),
        ],
        string='Adaptador', compute='_compute_protocol',
        help='PROVIDER_REGISTRY[proveedor]["protocol"] (llm/registry.py): '
             'OpenAI, Groq, DeepSeek, Mistral, OpenRouter y Abacus comparten '
             'el adaptador compatible con OpenAI.',
    )
    free_tier_note = fields.Char(
        string='Tier gratuito', compute='_compute_protocol',
        help='PROVIDER_REGISTRY[proveedor]["free_tier_note"] (llm/registry.py).',
    )

    # Credencial: se guarda solo cifrada (llm/vault.py). "api_key" es de
    # solo escritura: se lee como vacío y lo que se escribe se cifra.
    api_key_encrypted = fields.Char(
        groups='ai_agent_core.group_ai_agent_manager', copy=False,
    )
    api_key = fields.Char(
        string='API Key', compute='_compute_api_key', inverse='_inverse_api_key',
        groups='ai_agent_core.group_ai_agent_manager',
        help='Siempre se muestra vacía: escribe una para reemplazar la guardada. '
             'Se guarda cifrada con la clave ORBYLS_AI_VAULT_KEY.',
    )
    api_key_masked = fields.Char(
        string='API Key guardada', compute='_compute_api_key_masked',
        groups='ai_agent_core.group_ai_agent_manager',
        help='Últimos 4 caracteres de la API Key descifrada.',
    )
    ollama_mode = fields.Selection(
        [
            ('local', 'Servidor local'),
            ('cloud', 'Ollama Cloud (ollama.com)'),
        ],
        string='Modo de Ollama', default='local',
        help='Servidor local: tu propio "ollama serve", sin API Key. '
             'Ollama Cloud: usa la API Key de https://ollama.com/settings/keys '
             'y los modelos alojados en ollama.com (ej. "gpt-oss:120b").',
    )
    base_url = fields.Char(
        string='URL base',
        help='Proveedores compatibles con OpenAI: raíz de la API (ej. '
             'https://api.groq.com/openai/v1); se rellena sola al elegir el '
             'proveedor y solo hace falta cambiarla para usar un proxy. '
             'Ollama local: dirección donde corre "ollama serve".',
    )
    model_name_id = fields.Many2one(
        'ai.provider.available.model', string='Modelo',
        domain="[('provider_config_id', '=', id), ('kind', '=', 'text')]",
        ondelete='set null',
        help='Usa "Actualizar modelos disponibles" para poblar esta lista '
             'con los modelos reales de tu cuenta.',
    )
    image_model_name_id = fields.Many2one(
        'ai.provider.available.model', string='Modelo de imagen',
        domain="[('provider_config_id', '=', id), ('kind', '=', 'image')]",
        ondelete='set null',
        help='Gemini (Google) y ChatGPT (OpenAI) generan la imagen con su '
             'modelo de imágenes (Gemini/Nano Banana, Imagen, gpt-image, '
             'DALL·E). El resto no tiene API de imágenes en este módulo: el '
             'modelo de texto elegido aquí la dibuja como SVG y Odoo la '
             'convierte en JPG de 1080x1080, así que salen ilustraciones y '
             'gráficos, no fotografías. Usa "Actualizar modelos disponibles" '
             'para poblar esta lista.',
    )
    available_model_ids = fields.One2many(
        'ai.provider.available.model', 'provider_config_id',
        string='Modelos disponibles',
    )
    available_model_count = fields.Integer(
        string='Nº modelos', compute='_compute_available_model_count',
    )
    system_prompt = fields.Text(
        string='Instrucción de sistema',
        default=(
            "Eres un asistente que redacta publicaciones para redes sociales. "
            "Responde únicamente con el texto final de la publicación, sin "
            "explicaciones ni comillas adicionales."
        ),
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    is_default = fields.Boolean(
        string='Proveedor por defecto',
        help="Usado cuando un agente (ai.agent) no especifica un proveedor concreto.",
    )

    # Resiliencia
    fallback_provider_id = fields.Many2one(
        'ai.provider.config', string='Si falla, usar',
        domain="[('id', '!=', id)]", ondelete='set null',
        help='Proveedor al que se degrada cuando este no puede atender la '
             'petición (sin red, credencial vencida, bloqueo por país, sin '
             'saldo o 429 tras agotar los reintentos). Encadenable. Los '
             'agentes que atienden a terceros externos solo degradan a '
             'proveedores Ollama locales: sus datos no salen a otra empresa.',
    )
    use_local_fallback = fields.Boolean(
        string='Ollama local como último recurso', default=True,
        help='Al final de la cadena se prueba el primer proveedor Ollama '
             'local activo de la compañía, si existe y no está ya en ella.',
    )
    max_retries = fields.Integer(
        string='Reintentos ante 429', default=3,
        help='Reintentos con backoff exponencial y jitter antes de degradar.',
    )
    retry_budget_seconds = fields.Integer(
        string='Espera máxima en pantalla (s)', default=15,
        help='Tope de espera acumulada entre reintentos cuando la llamada la '
             'hace una petición web: el worker HTTP queda bloqueado mientras '
             'espera.',
    )
    retry_budget_background_seconds = fields.Integer(
        string='Espera máxima en segundo plano (s)', default=120,
        help='Tope de espera acumulada entre reintentos en crons y procesos sin '
             'petición web.',
    )
    cooldown_minutes = fields.Integer(
        string='Pausa tras caída (min)', default=5,
        help='Tras un fallo de red, de credencial, de saldo o un bloqueo, la '
             'cadena salta este proveedor durante este tiempo.',
    )
    unavailable_until = fields.Datetime(string='En pausa hasta', readonly=True, copy=False)
    last_error_kind = fields.Selection(ERROR_KINDS, string='Último fallo', readonly=True, copy=False)
    last_error_message = fields.Char(string='Detalle del último fallo', readonly=True, copy=False)
    health_state = fields.Selection(
        [('unknown', 'Sin comprobar'), ('ok', 'Operativo'), ('error', 'Con error')],
        string='Estado', default='unknown', readonly=True, copy=False,
    )
    health_checked_at = fields.Datetime(string='Comprobado el', readonly=True, copy=False)
    health_message = fields.Char(string='Resultado de la comprobación', readonly=True, copy=False)

    @api.depends('provider')
    def _compute_protocol(self):
        for rec in self:
            spec = provider_spec(rec.provider)
            rec.protocol = spec.get('protocol') or False
            rec.free_tier_note = spec.get('free_tier_note') or False

    @api.constrains('provider', 'api_key_encrypted', 'base_url', 'ollama_mode')
    def _check_credentials(self):
        for rec in self:
            if rec.provider == 'ollama' and rec.ollama_mode == 'local':
                if not rec.base_url:
                    raise ValidationError(
                        'Configura la URL del servidor de "%s".' % rec.name
                    )
            elif not rec.sudo().api_key_encrypted:
                raise ValidationError(
                    'Configura la API Key del proveedor "%s".' % rec.name
                )

    @api.constrains('fallback_provider_id')
    def _check_fallback_not_self(self):
        for rec in self:
            if rec.fallback_provider_id == rec:
                raise ValidationError('Un proveedor no puede degradar a sí mismo.')

    @api.depends('available_model_ids.active')
    def _compute_available_model_count(self):
        available = self.env['ai.provider.available.model'].with_context(active_test=False)
        for rec in self:
            rec.available_model_count = available.search_count(
                [('provider_config_id', '=', rec.id)]
            )

    @api.onchange('provider')
    def _onchange_provider_base_url(self):
        self.base_url = provider_spec(self.provider).get('base_url') or False

    # ------------------------------------------------------------------
    # Credenciales cifradas
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        # La clave se cifra ANTES de crear: Odoo valida las constraints de
        # los campos almacenados antes de ejecutar los inverse, así que con
        # un inverse puro _check_credentials vería la credencial vacía.
        return super().create([self._encrypt_api_key_vals(vals) for vals in vals_list])

    def write(self, vals):
        return super().write(self._encrypt_api_key_vals(vals))

    def _encrypt_api_key_vals(self, vals):
        if 'api_key' not in vals:
            return vals
        vals = dict(vals)
        key = (vals.pop('api_key') or '').strip()
        if key:
            vals['api_key_encrypted'] = AiVault(self.env).encrypt(key)
        return vals

    def _compute_api_key(self):
        for rec in self:
            rec.api_key = False

    def _inverse_api_key(self):
        vault = AiVault(self.env)
        for rec in self:
            if rec.api_key:
                rec.sudo().api_key_encrypted = vault.encrypt(rec.api_key.strip())

    @api.depends('api_key_encrypted')
    def _compute_api_key_masked(self):
        vault = AiVault(self.env)
        for rec in self:
            token = rec.sudo().api_key_encrypted
            try:
                rec.api_key_masked = mask(vault.decrypt(token)) if token else False
            except VaultDecryptError:
                rec.api_key_masked = 'Ilegible: vuelve a escribirla'

    def _needs_api_key(self):
        self.ensure_one()
        return not (self.provider == 'ollama' and self.ollama_mode == 'local')

    def _get_api_key(self):
        self.ensure_one()
        if not self._needs_api_key():
            return False
        token = self.sudo().api_key_encrypted
        if not token:
            raise AiProviderError(
                'El proveedor de IA "%s" no tiene una API Key configurada.' % self.name,
                CONFIG, self.name,
            )
        try:
            return AiVault(self.env).decrypt(token)
        except VaultDecryptError as exc:
            raise AiProviderError('"%s": %s Vuelve a escribir la API Key.' % (self.name, exc),
                                  CONFIG, self.name) from exc

    def _ensure_call_credentials(self):
        self.ensure_one()
        if not self._needs_api_key():
            if not self.base_url:
                raise AiProviderError(
                    'Este proveedor de IA no tiene una URL de servidor configurada.',
                    CONFIG, self.name,
                )
            return
        self._get_api_key()

    # ------------------------------------------------------------------
    # Endpoint y transporte
    # ------------------------------------------------------------------

    def _effective_base_url(self):
        self.ensure_one()
        if self.provider == 'ollama' and self.ollama_mode == 'cloud':
            return OLLAMA_CLOUD_BASE_URL
        return (self.base_url or provider_spec(self.provider).get('base_url') or '').rstrip('/')

    def _ollama_base_url(self):
        return self._effective_base_url()

    def _ollama_headers(self):
        self.ensure_one()
        if self.ollama_mode == 'cloud':
            return {'Authorization': 'Bearer %s' % self._get_api_key()}
        return {}

    def _openai_headers(self):
        self.ensure_one()
        headers = {
            'Authorization': 'Bearer %s' % self._get_api_key(),
            'Content-Type': 'application/json',
        }
        if self.provider == 'openrouter':
            # Opcionales: identifican la app en el panel de OpenRouter.
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            if base_url:
                headers['HTTP-Referer'] = base_url
            headers['X-Title'] = OPENROUTER_APP_TITLE
        return headers

    def _request(self, method, url, model='', **kwargs):
        """Hace la petición y convierte cualquier fallo en AiProviderError
        clasificado. Devuelve el JSON de una respuesta 2xx."""
        self.ensure_one()
        try:
            response = getattr(requests, method)(url, **kwargs)
        except requests.exceptions.RequestException as exc:
            hint = ''
            if self.provider == 'ollama' and self.ollama_mode == 'local':
                hint = (' Verifica que "ollama serve" esté corriendo y sea accesible '
                        'desde Odoo.')
            raise AiProviderError(
                'No se pudo conectar con %s en "%s": %s.%s'
                % (self.name, url.split('?')[0], exc.__class__.__name__, hint),
                UNAVAILABLE, self.name,
            ) from exc
        if not 200 <= response.status_code < 300:
            self._raise_http_error(response, model)
        try:
            return response.json()
        except ValueError as exc:
            raise AiProviderError(
                '%s devolvió una respuesta que no es JSON (HTTP %s).'
                % (self.name, response.status_code),
                INVALID_RESPONSE, self.name, status=response.status_code,
            ) from exc

    def _raise_http_error(self, response, model):
        headers = getattr(response, 'headers', None)
        kind, retry_after = classify_http_error(response.status_code, response.text, headers)
        if self.protocol == GEMINI:
            message = self._gemini_error_message(response, model)
        elif self.provider == 'openai':
            message = self._openai_error_message(response, model)
        else:
            message = self._generic_error_message(response, model, kind)
        raise AiProviderError(message, kind, self.name, retry_after, response.status_code)

    # ------------------------------------------------------------------
    # Errores de API legibles
    # ------------------------------------------------------------------

    @staticmethod
    def _response_error(response):
        """Devuelve el objeto "error" del cuerpo JSON (Gemini y OpenAI lo
        envuelven igual), o {} si el cuerpo no es JSON."""
        try:
            error = response.json().get('error')
        except (ValueError, AttributeError):
            return {}
        return error if isinstance(error, dict) else {'message': str(error)}

    def _gemini_error_message(self, response, model):
        """Traduce un error de Gemini a un mensaje accionable, sin volcar el
        JSON entero. El caso que más confunde: una API key en el nivel
        gratuito, cuya cuota para modelos de imagen es 0 — la suscripción
        Gemini Plus / Google AI Pro es de la app y no cubre la API."""
        error = self._response_error(response)
        message = error.get('message') or response.text[:500]
        if response.status_code == 429:
            details = error.get('details') or []
            quota_metrics = [
                violation.get('quotaMetric') or ''
                for detail in details for violation in detail.get('violations') or []
            ]
            free_tier = any('free_tier' in metric for metric in quota_metrics)
            if free_tier and 'limit: 0' in message:
                return (
                    'Tu API key de Gemini está en el nivel gratuito, que no '
                    'incluye el modelo "%s" (cuota 0): no se arregla esperando '
                    'ni reintentando. La suscripción Gemini Plus / Google AI '
                    'Pro es de la app de Gemini y no cubre la API. Activa la '
                    'facturación del proyecto de esta API key en %s (botón '
                    '"Set up billing").' % (model, GEMINI_BILLING_URL)
                )
            retry = next((d.get('retryDelay') for d in details if d.get('retryDelay')), None)
            wait = ' Reintenta en %s.' % retry if retry else ''
            if free_tier:
                return (
                    'Alcanzaste el límite del nivel gratuito de Gemini con el '
                    'modelo "%s".%s Para límites mayores, activa la facturación '
                    'del proyecto en %s.' % (model, wait, GEMINI_BILLING_URL)
                )
            return 'Gemini rechazó la petición por límite de uso con el modelo "%s".%s' % (model, wait)
        return 'Error de Gemini (%s) con el modelo "%s": %s' % (response.status_code, model, message)

    def _openai_error_message(self, response, model):
        error = self._response_error(response)
        message = error.get('message') or response.text[:500]
        if error.get('code') == 'insufficient_quota':
            return (
                'La cuenta de API de OpenAI no tiene saldo. La suscripción '
                'ChatGPT Plus no cubre la API: añade crédito en %s.' % OPENAI_BILLING_URL
            )
        if 'must be verified' in message:
            return (
                'OpenAI exige verificar la organización para usar "%s". '
                'Hazlo en https://platform.openai.com/settings/organization/general '
                'o elige otro modelo de imagen (ej. dall-e-3).' % model
            )
        return 'Error de OpenAI (%s) con el modelo "%s": %s' % (response.status_code, model, message)

    def _generic_error_message(self, response, model, kind):
        detail = error_text(response)
        key_url = provider_spec(self.provider).get('key_url') or ''
        on_model = ' con el modelo "%s"' % model if model else ''
        messages = {
            'auth': 'La API Key de "%s" no es válida o venció%s (%s). Genera otra en %s.'
                    % (self.name, on_model, detail, key_url),
            'geoblocked': '"%s" rechaza las peticiones desde la red o el país de este '
                          'servidor: %s' % (self.name, detail),
            'quota_exhausted': '"%s" no tiene saldo o cuota%s: %s' % (self.name, on_model, detail),
            'rate_limited': '"%s" rechazó la petición por límite de uso%s: %s'
                            % (self.name, on_model, detail),
            'model_unavailable': 'El modelo "%s" no está disponible en "%s": %s'
                                 % (model, self.name, detail),
            'unavailable': '"%s" no está disponible ahora (HTTP %s): %s'
                           % (self.name, response.status_code, detail),
        }
        return messages.get(kind) or 'Error de %s (HTTP %s)%s: %s' % (
            self.name, response.status_code, on_model, detail)

    # ------------------------------------------------------------------
    # Catálogo de modelos disponibles
    # ------------------------------------------------------------------

    def action_refresh_available_models(self):
        for rec in self:
            rec._fetch_available_models()
        return True

    def _fetch_available_models(self):
        self.ensure_one()
        try:
            self._ensure_call_credentials()
        except AiProviderError as exc:
            raise UserError(
                'Configura el proveedor "%s" antes de actualizar sus modelos '
                'disponibles: %s' % (self.name, exc)
            ) from exc
        try:
            fetched = self._list_models()
        except AiProviderError as exc:
            raise UserError(
                'No se pudo obtener la lista de modelos de %s: %s' % (self.name, exc)
            ) from exc
        self.env['ai.model.spec'].sudo()._upsert_from_api(self.provider, fetched)
        if self.provider in SVG_IMAGE_PROVIDERS:
            fetched = self._with_svg_image_variants(fetched)
        self._sync_available_models(fetched)
        return fetched

    def _list_models(self):
        catalog = provider_spec(self.provider).get('catalog')
        if catalog == 'anthropic':
            return self._list_anthropic_models()
        if catalog == 'gemini':
            return self._list_gemini_models()
        if catalog == 'ollama':
            return self._list_ollama_models()
        if catalog in llm_catalog.PARSERS:
            data = self._request(
                'get', self._effective_base_url() + '/models',
                headers=self._openai_headers(), timeout=30,
            )
            return llm_catalog.PARSERS[catalog](data)
        raise UserError('Proveedor de IA no soportado: %s' % self.provider)

    @staticmethod
    def _with_svg_image_variants(fetched):
        """Registra cada modelo de texto también como modelo de imagen, para
        los proveedores que generan la imagen dibujándola en SVG. Ambas
        entradas conviven: la unicidad es (proveedor, modelo, tipo)."""
        variants = [
            dict(f, kind='image', display_name='%s (ilustración SVG)' % f['display_name'])
            for f in fetched if f['kind'] == 'text'
        ]
        return fetched + variants

    def _list_anthropic_models(self):
        headers = {'x-api-key': self._get_api_key(), 'anthropic-version': ANTHROPIC_VERSION}
        data = self._request('get', ANTHROPIC_MODELS_URL, headers=headers,
                             params={'limit': 1000}, timeout=30)
        return [
            {'model_id': m['id'], 'display_name': m.get('display_name') or m['id'], 'kind': 'text'}
            for m in data.get('data', [])
        ]

    def _list_gemini_models(self):
        fetched = []
        params = {'key': self._get_api_key(), 'pageSize': 1000}
        while True:
            data = self._request('get', GEMINI_MODELS_URL, params=params, timeout=30)
            for m in data.get('models', []):
                model_id = (m.get('name') or '').split('/')[-1]
                if not model_id:
                    continue
                methods = m.get('supportedGenerationMethods', [])
                is_image = any(marker in model_id.lower() for marker in GEMINI_IMAGE_MARKERS)
                # :predict solo interesa para Imagen; el resto de modelos
                # con ese método (y los de video, predictLongRunning) no
                # son utilizables desde este módulo.
                if 'generateContent' not in methods and not (is_image and 'predict' in methods):
                    continue
                fetched.append({
                    'model_id': model_id,
                    'display_name': m.get('displayName') or model_id,
                    'kind': 'image' if is_image else 'text',
                })
            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break
            params = dict(params, pageToken=next_page_token)
        return fetched

    def _list_ollama_models(self):
        data = self._request('get', self._effective_base_url() + OLLAMA_TAGS_PATH,
                             headers=self._ollama_headers(), timeout=15)
        return [
            {'model_id': m['model'], 'display_name': m.get('name') or m['model'], 'kind': 'text'}
            for m in data.get('models', [])
        ]

    def _sync_available_models(self, fetched):
        """Reemplaza el catálogo local por el que reporta la API ahora
        mismo: lo que ya no aparece se considera deprecado y se elimina.
        No toca el campo "Seleccionable" (active) de los que sí siguen
        existiendo: es una elección manual del usuario, no algo que el
        refresco deba pisar."""
        self.ensure_one()
        available = self.env['ai.provider.available.model'].with_context(active_test=False)
        existing = available.search([('provider_config_id', '=', self.id)])
        fetched_by_key = {(f['model_id'], f['kind']): f for f in fetched}
        existing_by_key = {(m.model_id, m.kind): m for m in existing}

        stale = existing.filtered(lambda m: (m.model_id, m.kind) not in fetched_by_key)
        if stale:
            _logger.info(
                'Eliminando modelos deprecados de "%s": %s',
                self.name, stale.mapped('model_id'),
            )
            stale.unlink()

        to_create = []
        for key, f in fetched_by_key.items():
            rec = existing_by_key.get(key)
            if rec:
                if rec.name != f['display_name']:
                    rec.name = f['display_name']
            else:
                to_create.append({
                    'provider_config_id': self.id,
                    'model_id': f['model_id'],
                    'name': f['display_name'],
                    'kind': f['kind'],
                })
        if to_create:
            available.create(to_create)

    def action_view_available_models(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Modelos disponibles',
            'res_model': 'ai.provider.available.model',
            'view_mode': 'list',
            'domain': [('provider_config_id', '=', self.id)],
            'context': {
                'default_provider_config_id': self.id,
                'active_test': False,
            },
        }

    @api.model
    def cron_refresh_available_models(self):
        """Refresca semanalmente el catálogo de modelos de todos los
        proveedores activos y elimina los que ya no ofrece la API
        (deprecados/retirados)."""
        domain = ['|', ('api_key_encrypted', '!=', False), ('base_url', '!=', False)]
        for config in self.sudo().search(domain):
            try:
                config._fetch_available_models()
            except Exception:
                _logger.exception(
                    'No se pudo actualizar el catálogo de modelos de "%s"', config.name
                )

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def action_health_check(self):
        results = [rec._run_health_check() for rec in self]
        failed = [rec for rec, ok in zip(self, results) if not ok]
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Comprobación de proveedores de IA',
                'message': (
                    'Credencial y conexión correctas.' if not failed
                    else '; '.join('%s: %s' % (rec.name, rec.health_message) for rec in failed)
                ),
                'type': 'success' if not failed else 'danger',
                'sticky': bool(failed),
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
            },
        }

    def _run_health_check(self):
        """Verifica credencial y conectividad con un endpoint que NO genera
        (listado de modelos, saldo o datos de la clave): no consume tokens.

        Límite honesto: listar modelos prueba la clave y la red, no que la
        inferencia no esté bloqueada; eso solo lo detecta una llamada real,
        y la cubre la cadena de fallback."""
        self.ensure_one()
        started = time.monotonic()
        try:
            self._ensure_call_credentials()
            self._health_probe()
        except AiProviderError as exc:
            message = str(exc)[:250]
            vals = {'health_state': 'error', 'health_message': message}
            self._record_failure(exc, extra_vals=vals)
            self._audit_llm_call('llm.health_check', '', 'error', started, error=exc,
                                 event_type='health_check')
            return False
        now = fields.Datetime.now()
        self._write_state({
            'health_state': 'ok', 'health_checked_at': now,
            'health_message': 'Credencial y conexión correctas.',
            'unavailable_until': False, 'last_error_kind': False, 'last_error_message': False,
        })
        self._audit_llm_call('llm.health_check', '', 'success', started, event_type='health_check')
        return True

    def _health_probe(self):
        protocol = self.protocol
        if protocol == ANTHROPIC:
            self._list_anthropic_models_probe()
        elif protocol == GEMINI:
            self._request('get', GEMINI_MODELS_URL,
                          params={'key': self._get_api_key(), 'pageSize': 1},
                          timeout=HEALTH_CHECK_TIMEOUT)
        elif protocol == OLLAMA:
            self._request('get', self._effective_base_url() + OLLAMA_TAGS_PATH,
                          headers=self._ollama_headers(), timeout=HEALTH_CHECK_TIMEOUT)
        else:
            path, auth = provider_spec(self.provider).get('health') or ('/models', 'bearer')
            url = path if path.startswith('http') else self._effective_base_url() + path
            key = self._get_api_key()
            headers = {'apiKey': key} if auth == 'apikey' else {'Authorization': 'Bearer %s' % key}
            data = self._request('get', url, headers=headers, timeout=HEALTH_CHECK_TIMEOUT)
            # Abacus responde 200 con success=false en algunos rechazos.
            if isinstance(data, dict) and data.get('success') is False:
                raise AiProviderError(
                    'La API Key de "%s" fue rechazada: %s' % (self.name, data.get('error') or data),
                    'auth', self.name,
                )

    def _list_anthropic_models_probe(self):
        headers = {'x-api-key': self._get_api_key(), 'anthropic-version': ANTHROPIC_VERSION}
        self._request('get', ANTHROPIC_MODELS_URL, headers=headers,
                      params={'limit': 1}, timeout=HEALTH_CHECK_TIMEOUT)

    @api.model
    def cron_health_check(self):
        for config in self.sudo().search([]):
            try:
                config._run_health_check()
            except Exception:
                _logger.exception('Health check de "%s" falló de forma inesperada', config.name)

    # ------------------------------------------------------------------
    # Estado persistente fuera de la transacción
    # ------------------------------------------------------------------

    def _isolated_env(self):
        """Cursor propio para la AUDITORÍA, que confirma aunque la transacción
        de la petición termine en rollback. Sin esto, justo las llamadas
        fallidas —las que más interesa auditar— desaparecerían con el
        UserError que las sigue. En tests se usa el cursor del test, que no
        puede ver lo que otro cursor escribe ni al revés."""
        if modules.module.current_test:
            return None
        return self.env.registry.cursor()

    def _write_state(self, vals):
        """Estado del proveedor (pausa, último fallo, health check): en la
        transacción de la petición, NO en un cursor aparte.

        Se probó con cursor aparte y contra una base real salió mal por dos
        lados: la transacción de la petición, abierta antes, seguía leyendo
        los valores viejos (la notificación del health check salía vacía), y
        cualquier write posterior sobre la misma fila en esa transacción
        chocaba con la escritura ya confirmada ("could not serialize access
        due to concurrent update"): Odoo reintenta la petición entera y
        volvería a llamar al proveedor. Coste asumido: si toda la cadena
        falla y la petición termina en error, la pausa no se guarda (la
        auditoría sí)."""
        self.sudo().write(vals)

    def _record_failure(self, exc, extra_vals=None):
        vals = dict(extra_vals or {})
        vals.update({
            'last_error_kind': exc.kind,
            'last_error_message': str(exc)[:250],
        })
        if 'health_state' in vals:
            vals['health_checked_at'] = fields.Datetime.now()
        pause = None
        if exc.kind in COOLDOWN_KINDS:
            pause = timedelta(minutes=max(self.cooldown_minutes, 0))
        elif exc.kind == RATE_LIMITED and exc.retry_after:
            pause = timedelta(seconds=exc.retry_after)
        if pause:
            vals['unavailable_until'] = fields.Datetime.now() + pause
        self._write_state(vals)

    def _clear_failure_state(self):
        if self.unavailable_until or self.last_error_kind:
            self._write_state({
                'unavailable_until': False, 'last_error_kind': False, 'last_error_message': False,
            })

    def _audit_llm_call(self, tool_name, model, status, started, result=None, error=None,
                        attempt=1, fallback_from=None, event_type='llm_call'):
        """Una fila de ai.audit.log por llamada HTTP al proveedor. Nunca
        guarda la API Key ni el prompt: solo proveedor, modelo, tokens,
        costo y resultado."""
        input_tokens = result.input_tokens if result else 0
        output_tokens = result.output_tokens if result else 0
        cost, cost_source = None, False
        if result:
            if result.reported_cost is not None:
                cost, cost_source = result.reported_cost, 'provider'
            else:
                spec = self.env['ai.model.spec'].sudo()._lookup(self.provider, model)
                cost = spec._estimate_cost(input_tokens, output_tokens)
                cost_source = 'spec' if cost is not None else 'unknown'
        agent_id = self.env.context.get('ai_agent_id')
        vals = {
            'event_type': event_type,
            'tool_name': tool_name,
            'agent_id': agent_id or False,
            'user_id': self.env.uid,
            'company_id': (self.company_id or self.env.company).id,
            'status': status,
            'duration_ms': int((time.monotonic() - started) * 1000),
            'provider_config_id': self.id,
            'provider_code': self.provider,
            'model_name': model or False,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost_usd': cost or 0.0,
            'cost_source': cost_source,
            'attempt': attempt,
            'fallback_from_id': fallback_from.id if fallback_from else False,
            'error_kind': error.kind if error else False,
            'error_type': type(error).__name__ if error else False,
            'error_message': str(error)[:2000] if error else False,
        }
        try:
            cursor = self._isolated_env()
            if cursor is None:
                self.env['ai.audit.log'].sudo().create(vals)
                return
            with cursor as cr:
                self.env(cr=cr, su=True)['ai.audit.log'].create(vals)
        except Exception:
            _logger.exception('No se pudo escribir la auditoría de la llamada a "%s"', self.name)

    # ------------------------------------------------------------------
    # Generación de texto: reintentos y cadena de fallback
    # ------------------------------------------------------------------

    def generate_content(self, prompt, system_prompt=None):
        """Genera texto con este proveedor y, si no puede atender, con el
        siguiente de su cadena de fallback (ver _fallback_chain).

        :param prompt: instrucción / tema.
        :param system_prompt: instrucción de sistema opcional (si no se
            indica, se usa la de cada proveedor que atienda).
        :return: str con el contenido generado.
        """
        self.ensure_one()
        return self._generate_text_resilient(prompt, system_prompt).text

    def _fallback_chain(self):
        """Proveedores a probar, en orden: este, los que encadena
        fallback_provider_id (sin repetir y sin ciclos) y, si
        use_local_fallback, un Ollama local como último recurso.

        Con el contexto ai_external_facing (agentes que atienden a terceros)
        los eslabones que no son Ollama local se saltan: la petición de un
        cliente no se reenvía a otra empresa sin que nadie lo haya decidido.
        """
        self.ensure_one()
        external = self.env.context.get('ai_external_facing')
        ordered, seen = [self.id], {self.id}
        node = self.fallback_provider_id
        while node and node.id not in seen:
            seen.add(node.id)
            if node.active and (not external or node._is_local()):
                ordered.append(node.id)
            node = node.fallback_provider_id
        if self.use_local_fallback:
            last_resort = self.search([
                ('provider', '=', 'ollama'), ('ollama_mode', '=', 'local'),
                ('company_id', 'in', [self.company_id.id, False]),
                ('id', 'not in', ordered),
            ], limit=1)
            ordered.extend(last_resort.ids)
        return self.browse(ordered)

    def _is_local(self):
        self.ensure_one()
        return self.provider == 'ollama' and self.ollama_mode == 'local'

    def _generate_text_resilient(self, prompt, system_prompt=None):
        chain = self._fallback_chain()
        now = fields.Datetime.now()
        ready = chain.filtered(lambda p: not p.unavailable_until or p.unavailable_until <= now)
        # Si todos están en pausa, se prueban igual: peor que un intento
        # extra es no intentar nada.
        candidates = ready or chain
        errors = []
        for provider in candidates:
            try:
                result = provider._generate_text_with_retries(
                    prompt, system_prompt,
                    fallback_from=self if provider != self else None,
                )
            except AiProviderError as exc:
                errors.append((provider, exc))
                provider._record_failure(exc)
                if exc.kind not in FALLBACK_KINDS:
                    raise
                _logger.warning('Proveedor de IA "%s" no disponible (%s); se degrada.',
                                provider.name, exc.kind)
                continue
            provider._clear_failure_state()
            return result
        if len(errors) == 1:
            raise errors[0][1]
        raise AiProviderError(
            'Ningún proveedor de IA pudo atender la petición. %s'
            % ' | '.join('%s: %s' % (provider.name, exc) for provider, exc in errors),
            errors[-1][1].kind, self.name,
        )

    def _retry_budget(self):
        return self.retry_budget_seconds if request else self.retry_budget_background_seconds

    def _sleep(self, seconds):
        time.sleep(seconds)

    def _text_model(self):
        return self.model_name_id.model_id or provider_spec(self.provider).get('default_model')

    def _generate_text_with_retries(self, prompt, system_prompt=None, model=None,
                                    fallback_from=None, tool_name='llm.generate_content',
                                    **call_kwargs):
        """Llama al proveedor reintentando SOLO los 429 transitorios, con
        backoff exponencial y jitter, hasta max_retries o hasta agotar la
        espera permitida. Audita cada intento."""
        self.ensure_one()
        model = model or self._text_model()
        system_prompt = system_prompt or self.system_prompt or ''
        budget = self._retry_budget()
        waited = 0.0
        attempt = 0
        while True:
            started = time.monotonic()
            try:
                self._ensure_call_credentials()
                result = self._call_text(prompt, system_prompt, model, **call_kwargs)
            except AiProviderError as exc:
                self._audit_llm_call(tool_name, model, 'error', started, error=exc,
                                     attempt=attempt + 1, fallback_from=fallback_from)
                if exc.kind != RATE_LIMITED or attempt >= self.max_retries:
                    raise
                delay = backoff_delay(attempt, exc.retry_after,
                                      base=BACKOFF_BASE_SECONDS, cap=BACKOFF_CAP_SECONDS)
                if waited + delay > budget:
                    raise
                self._sleep(delay)
                waited += delay
                attempt += 1
                continue
            self._audit_llm_call(tool_name, model, 'success', started, result=result,
                                 attempt=attempt + 1, fallback_from=fallback_from)
            return result

    def _call_text(self, prompt, system_prompt, model, max_tokens=None, timeout=60):
        protocol = self.protocol
        if protocol == OPENAI:
            return self._generate_openai_compatible(prompt, system_prompt, model, max_tokens, timeout)
        if protocol == ANTHROPIC:
            return self._generate_anthropic(prompt, system_prompt, model,
                                            max_tokens=max_tokens or 1024, timeout=timeout)
        if protocol == GEMINI:
            return self._generate_gemini(prompt, system_prompt, model, timeout=timeout)
        if protocol == OLLAMA:
            return self._generate_ollama(prompt, system_prompt, model, timeout=max(timeout, 120))
        raise AiProviderError('Proveedor de IA no soportado: %s' % self.provider, CONFIG, self.name)

    def _generate_openai_compatible(self, prompt, system_prompt, model, max_tokens=None, timeout=60):
        """Un solo adaptador para OpenAI, Groq, DeepSeek, Mistral, OpenRouter
        y Abacus: POST {base_url}/chat/completions."""
        messages = [{'role': 'user', 'content': prompt}]
        if system_prompt:
            messages.insert(0, {'role': 'system', 'content': system_prompt})
        payload = {'model': model, 'messages': messages}
        if max_tokens:
            payload['max_tokens'] = max_tokens
        data = self._request(
            'post', self._effective_base_url() + '/chat/completions', model=model,
            headers=self._openai_headers(), json=payload, timeout=timeout,
        )
        try:
            choice = data['choices'][0]
            text = choice['message']['content']
        except (IndexError, KeyError, TypeError) as exc:
            raise AiProviderError('Respuesta inesperada de %s: %s' % (self.name, str(data)[:300]),
                                  INVALID_RESPONSE, self.name) from exc
        if not text:
            kind = CONTENT_FILTERED if choice.get('finish_reason') == 'content_filter' else INVALID_RESPONSE
            raise AiProviderError('%s no devolvió texto (finish_reason: %s).'
                                  % (self.name, choice.get('finish_reason')), kind, self.name)
        return LlmResult(text.strip(), *parse_usage(OPENAI, data))

    def _generate_anthropic(self, prompt, system_prompt, model, max_tokens=1024, timeout=60):
        headers = {
            'x-api-key': self._get_api_key(),
            'anthropic-version': ANTHROPIC_VERSION,
            'content-type': 'application/json',
        }
        payload = {
            'model': model,
            'max_tokens': max_tokens,
            'messages': [{'role': 'user', 'content': prompt}],
        }
        if system_prompt:
            payload['system'] = system_prompt
        data = self._request('post', ANTHROPIC_API_URL, model=model, headers=headers,
                             json=payload, timeout=timeout)
        text = ''.join(
            block.get('text', '') for block in data.get('content', [])
            if block.get('type') == 'text'
        ).strip()
        return LlmResult(text, *parse_usage(ANTHROPIC, data))

    def _generate_gemini(self, prompt, system_prompt, model, timeout=60):
        payload = {'contents': [{'role': 'user', 'parts': [{'text': prompt}]}]}
        if system_prompt:
            payload['system_instruction'] = {'parts': [{'text': system_prompt}]}
        data = self._request(
            'post', GEMINI_API_URL_TMPL.format(model=model), model=model,
            headers={'content-type': 'application/json'},
            params={'key': self._get_api_key()}, json=payload, timeout=timeout,
        )
        try:
            candidate = data['candidates'][0]
            parts = (candidate.get('content') or {}).get('parts') or []
        except (IndexError, KeyError, TypeError) as exc:
            reason = (data.get('promptFeedback') or {}).get('blockReason')
            kind = CONTENT_FILTERED if reason else INVALID_RESPONSE
            raise AiProviderError('Respuesta inesperada de Gemini%s.'
                                  % (' (bloqueada: %s)' % reason if reason else ''),
                                  kind, self.name) from exc
        text = ''.join(part.get('text', '') for part in parts).strip()
        return LlmResult(text, *parse_usage(GEMINI, data))

    def _generate_ollama(self, prompt, system_prompt, model, timeout=120):
        messages = [{'role': 'user', 'content': prompt}]
        if system_prompt:
            messages.insert(0, {'role': 'system', 'content': system_prompt})
        data = self._request(
            'post', self._effective_base_url() + OLLAMA_CHAT_PATH, model=model,
            headers=self._ollama_headers(),
            json={'model': model, 'stream': False, 'messages': messages}, timeout=timeout,
        )
        try:
            text = data['message']['content'].strip()
        except (KeyError, TypeError, AttributeError) as exc:
            raise AiProviderError('Respuesta inesperada de Ollama: %s' % str(data)[:300],
                                  INVALID_RESPONSE, self.name) from exc
        return LlmResult(text, *parse_usage(OLLAMA, data))

    # ------------------------------------------------------------------
    # Generación de imágenes (sin cadena de fallback: la imagen depende del
    # modelo de imagen elegido en ESTE proveedor)
    # ------------------------------------------------------------------

    def generate_image(self, prompt):
        """Genera una imagen a partir de un prompt.

        Gemini y OpenAI usan su API de imágenes. El resto no tiene una en
        este módulo: el modelo dibuja un SVG que se sanea y se rasteriza a
        JPG (ver _generate_svg_image).

        :param prompt: instrucción / tema para la imagen.
        :return: tupla (imagen_base64, nombre_de_archivo).
        """
        self.ensure_one()
        self._ensure_call_credentials()
        if self.provider not in IMAGE_CAPABLE_PROVIDERS:
            raise UserError(
                'El proveedor "%s" no soporta generación de imágenes con este '
                'módulo.' % self.name
            )
        if not self.image_model_name_id:
            raise UserError(
                'Configura el campo "Modelo de imagen" en el proveedor de IA "%s" '
                '(ej. gemini-3.1-flash-image o gpt-image-1; en el resto, el '
                'modelo que dibujará la imagen en SVG).' % self.name
            )
        model = self.image_model_name_id.model_id
        if self.provider in SVG_IMAGE_PROVIDERS:
            return self._generate_svg_image(prompt, model)
        started = time.monotonic()
        try:
            if self.provider == 'google':
                if model.startswith('imagen'):
                    image = self._generate_imagen_image(prompt, model)
                else:
                    image = self._generate_gemini_image(prompt, model)
            else:
                image = self._generate_openai_image(prompt, model)
        except AiProviderError as exc:
            self._audit_llm_call('llm.generate_image', model, 'error', started, error=exc)
            raise
        self._audit_llm_call('llm.generate_image', model, 'success', started,
                             result=LlmResult('', 0, 0, None))
        return image

    def _generate_gemini_image(self, prompt, model):
        payload = {
            'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
            'generationConfig': {'responseModalities': ['IMAGE', 'TEXT']},
        }
        data = self._request(
            'post', GEMINI_API_URL_TMPL.format(model=model), model=model,
            headers={'content-type': 'application/json'},
            params={'key': self._get_api_key()}, json=payload, timeout=60,
        )
        candidates = data.get('candidates') or [{}]
        parts = (candidates[0].get('content') or {}).get('parts') or []
        for part in parts:
            inline = part.get('inlineData') or part.get('inline_data')
            if inline and inline.get('data'):
                mime = inline.get('mimeType') or inline.get('mime_type') or 'image/png'
                ext = mime.split('/')[-1].split('+')[0] or 'png'
                return inline['data'], 'ai_generated.%s' % ext
        # Sin imagen: suele ser el filtro de seguridad (finishReason
        # IMAGE_SAFETY / PROHIBITED_CONTENT) o que el modelo solo respondió texto.
        reason = candidates[0].get('finishReason') or (data.get('promptFeedback') or {}).get('blockReason')
        text = ' '.join(part.get('text', '') for part in parts).strip()
        raise AiProviderError(
            'Gemini no devolvió ninguna imagen con el modelo "%s"%s%s' % (
                model,
                ' (motivo: %s)' % reason if reason else '',
                ': %s' % text[:300] if text else '.',
            ),
            CONTENT_FILTERED if reason else INVALID_RESPONSE, self.name,
        )

    def _generate_imagen_image(self, prompt, model):
        """Imagen (imagen-4.0-*) va por :predict: pide "instances" y devuelve
        "predictions" con la imagen en bytesBase64Encoded."""
        payload = {
            'instances': [{'prompt': prompt}],
            'parameters': {'sampleCount': 1, 'aspectRatio': '1:1'},
        }
        data = self._request(
            'post', GEMINI_PREDICT_URL_TMPL.format(model=model), model=model,
            headers={'content-type': 'application/json'},
            params={'key': self._get_api_key()}, json=payload, timeout=120,
        )
        for prediction in data.get('predictions') or []:
            b64 = prediction.get('bytesBase64Encoded')
            if b64:
                mime = prediction.get('mimeType') or 'image/png'
                return b64, 'ai_generated.%s' % (mime.split('/')[-1] or 'png')
        raise AiProviderError(
            'Imagen no devolvió ninguna imagen con el modelo "%s" (lo más '
            'probable es que el filtro de seguridad la bloqueara).' % model,
            CONTENT_FILTERED, self.name,
        )

    def _generate_openai_image(self, prompt, model):
        payload = {'model': model, 'prompt': prompt, 'n': 1, 'size': '1024x1024'}
        if not model.startswith('gpt-image'):
            # gpt-image-1 siempre devuelve base64 y no acepta este parámetro;
            # dall-e-2/3 sí lo requieren para no devolver solo una URL temporal.
            payload['response_format'] = 'b64_json'
        data = self._request(
            'post', self._effective_base_url() + '/images/generations', model=model,
            headers=self._openai_headers(), json=payload, timeout=120,
        )
        try:
            b64 = data['data'][0].get('b64_json')
        except (IndexError, KeyError, TypeError) as exc:
            raise AiProviderError('Respuesta inesperada de OpenAI: %s' % str(data)[:300],
                                  INVALID_RESPONSE, self.name) from exc
        if not b64:
            raise AiProviderError('OpenAI no devolvió la imagen en base64.',
                                  INVALID_RESPONSE, self.name)
        return b64, 'ai_generated.png'

    def _generate_svg_image(self, prompt, model):
        """El modelo de texto dibuja la imagen en SVG, se sanea y se
        rasteriza a JPG con el wkhtmltoimage de Odoo."""
        result = self._generate_text_with_retries(
            'Crea la imagen para esta publicación: %s' % prompt, SVG_SYSTEM_PROMPT,
            model=model, tool_name='llm.generate_image_svg',
            max_tokens=SVG_IMAGE_MAX_TOKENS, timeout=SVG_IMAGE_TIMEOUT,
        )
        svg = self._sanitize_svg(result.text, model)
        html = (
            '<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
            'html,body{margin:0;padding:0;overflow:hidden;background:white}'
            'svg{display:block}</style></head><body>%s</body></html>' % svg
        )
        image = self.env['ir.actions.report']._run_wkhtmltoimage(
            [html], SVG_IMAGE_SIZE, SVG_IMAGE_SIZE, image_format='jpg',
        )[0]
        if not image:
            raise UserError(
                'El modelo "%s" dibujó la imagen, pero no se pudo convertir a '
                'JPG con wkhtmltoimage (revisa el log del servidor).' % model
            )
        return base64.b64encode(image).decode(), 'ai_generated.jpg'

    @api.model
    def _sanitize_svg(self, raw, model=''):
        """Extrae el <svg> de la respuesta del modelo y quita todo lo que
        podría ejecutar código o pedir recursos al rasterizarlo (scripts,
        manejadores on*, enlaces y url() externos, foreignObject, image).

        wkhtmltoimage ya corre sin JavaScript ni acceso a archivos locales,
        pero sí tiene red: sin este saneado, un SVG podría hacer que el
        servidor pida URLs internas. El prompt viene del usuario, así que
        la salida del modelo no es de fiar.
        """
        match = re.search(r'<svg\b.*</svg\s*>', raw or '', re.DOTALL | re.IGNORECASE)
        if not match:
            if re.search(r'<svg\b', raw or '', re.IGNORECASE):
                raise UserError(
                    'La respuesta del modelo "%s" quedó cortada antes de cerrar '
                    'el SVG. Prueba con una instrucción más simple o con un '
                    'modelo más capaz.' % model
                )
            raise UserError(
                'El modelo "%s" no devolvió un SVG. Respuesta: %s' % (model, (raw or '')[:300])
            )
        source = match.group(0).replace('&nbsp;', '&#160;')
        parser = etree.XMLParser(
            resolve_entities=False, no_network=True, remove_comments=True,
            remove_pis=True, recover=False,
        )
        try:
            root = etree.fromstring(source.encode('utf-8'), parser=parser)
        except etree.XMLSyntaxError as exc:
            raise UserError(
                'El modelo "%s" devolvió un SVG mal formado (%s). Vuelve a '
                'intentarlo o elige un modelo más capaz.' % (model, exc)
            )

        doomed = []
        for element in root.iter():
            if not isinstance(element.tag, str):
                continue
            tag = etree.QName(element).localname.lower()
            if tag in SVG_FORBIDDEN_TAGS:
                doomed.append(element)
                continue
            if tag == 'style' and re.search(r'@import', element.text or '', re.IGNORECASE):
                doomed.append(element)
                continue
            if tag == 'style' and SVG_EXTERNAL_URL_RE.search(element.text or ''):
                doomed.append(element)
                continue
            for name in list(element.attrib):
                local = etree.QName(name).localname.lower()
                value = element.attrib[name]
                if (
                    local.startswith('on')
                    or (local == 'href' and not value.strip().startswith('#'))
                    or SVG_EXTERNAL_URL_RE.search(value)
                ):
                    del element.attrib[name]
        for element in doomed:
            if element is root:
                raise UserError('El modelo "%s" no devolvió un SVG válido.' % model)
            element.getparent().remove(element)

        if not root.get('viewBox'):
            width = re.match(r'^\s*(\d+(?:\.\d+)?)\s*(px)?\s*$', root.get('width') or '')
            height = re.match(r'^\s*(\d+(?:\.\d+)?)\s*(px)?\s*$', root.get('height') or '')
            if width and height:
                root.set('viewBox', '0 0 %s %s' % (width.group(1), height.group(1)))
            else:
                root.set('viewBox', '0 0 %s %s' % (SVG_IMAGE_SIZE, SVG_IMAGE_SIZE))
        root.set('width', str(SVG_IMAGE_SIZE))
        root.set('height', str(SVG_IMAGE_SIZE))
        return etree.tostring(root, encoding='unicode')

    # ------------------------------------------------------------------
    # Resolución del proveedor
    # ------------------------------------------------------------------

    @api.model
    def get_default_provider(self):
        provider = self.search([('is_default', '=', True), ('active', '=', True)], limit=1)
        if not provider:
            provider = self.search([('active', '=', True)], limit=1)
        return provider

    @api.model
    def get_configured_provider(self, config_key):
        """Resuelve el proveedor de IA para un módulo de dominio que guarda
        su elección en un ir.config_parameter (ej. 'ai_customer_agent.ai_provider_id'):
        usa el explícito si está seteado y activo, si no cae al proveedor
        por defecto. Centralizado acá para que cualquier agente futuro
        resuelva su proveedor de la misma forma, tanto desde Python como
        desde una expresión QWeb."""
        provider_id = self.env['ir.config_parameter'].sudo().get_param(config_key)
        if provider_id:
            provider = self.sudo().browse(int(provider_id))
            if provider.exists() and provider.active:
                return provider
        return self.get_default_provider()
