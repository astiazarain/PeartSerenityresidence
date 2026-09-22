# -*- coding: utf-8 -*-
"""Cifrado de las credenciales de los proveedores de IA.

Alcance, dicho sin adornos
--------------------------
Es cifrado simétrico Fernet (AES-128-CBC + HMAC), el mismo método que
``orbyls_rumbo_registry/models/vault.py``, con clave propia: este módulo es
compartido por todas las líneas de producto y no puede depender de Rumbo.
No tiene relación con el "Vault — Aprobaciones" del menú, que es la cola
de ``ai.approval.request``.

Qué protege: un volcado o una copia de la base robados no revelan las API
Keys, ni tampoco un acceso de solo lectura a PostgreSQL.

Qué NO protege: a quien tenga a la vez la base y el servidor (tendrá la
clave), ni al código de Odoo, que descifra para llamar a la API.

De dónde sale la clave
----------------------
De la variable de entorno ``ORBYLS_AI_VAULT_KEY``. Si no está definida, se
genera una y se guarda en ``ir.config_parameter`` para que la instalación
funcione, pero entonces la clave viaja en el mismo volcado que los datos y
la protección contra el robo del volcado se pierde. Se avisa en el log.

**Perder la clave es perder las API Keys guardadas**: habría que volver a
escribirlas. Cambiarla exige re-cifrar.
"""
import base64
import hashlib
import logging
import os

from cryptography.fernet import Fernet, InvalidToken

_logger = logging.getLogger(__name__)

ENV_VAR = 'ORBYLS_AI_VAULT_KEY'
PARAM_KEY = 'ai_agent_core.vault_key'


class VaultDecryptError(Exception):
    """El valor guardado no se descifra con la clave actual."""


class AiVault:
    """Cifra y descifra cadenas cortas. Sin estado entre llamadas."""

    def __init__(self, env):
        self.env = env

    def _key(self):
        key = os.environ.get(ENV_VAR)
        if key:
            return self._normalise(key), True
        params = self.env['ir.config_parameter'].sudo()
        stored = params.get_param(PARAM_KEY)
        if not stored:
            stored = Fernet.generate_key().decode()
            params.set_param(PARAM_KEY, stored)
            _logger.warning(
                "ai_agent_core: no está definida la variable de entorno %s, así "
                "que se generó una clave de cifrado y se guardó en la base. Las "
                "API Keys quedan cifradas, pero la clave viaja en el mismo "
                "volcado que ellas. Define %s en producción.", ENV_VAR, ENV_VAR)
        return self._normalise(stored), False

    @staticmethod
    def _normalise(key):
        """Acepta una clave Fernet o cualquier frase: de una frase se deriva
        una clave válida de 32 bytes."""
        raw = key.encode() if isinstance(key, str) else key
        try:
            Fernet(raw)
            return raw
        except (ValueError, TypeError):
            return base64.urlsafe_b64encode(hashlib.sha256(raw).digest())

    def key_comes_from_env(self):
        return self._key()[1]

    def encrypt(self, value):
        if not value:
            return False
        key, _from_env = self._key()
        return Fernet(key).encrypt(value.encode()).decode()

    def decrypt(self, token):
        """Descifra o lanza VaultDecryptError. A diferencia del vault de
        Rumbo, no devuelve un marcador: un marcador acabaría enviado como
        API Key a un tercero."""
        if not token:
            return False
        key, _from_env = self._key()
        try:
            return Fernet(key).decrypt(token.encode()).decode()
        except InvalidToken as exc:
            raise VaultDecryptError(
                'No se pudo descifrar la API Key guardada. ¿Cambió la clave %s?' % ENV_VAR
            ) from exc


def mask(value, visible=4):
    if not value:
        return ''
    clean = value.strip()
    if len(clean) <= visible:
        return '•' * len(clean)
    return '•' * 8 + clean[-visible:]
