# -*- coding: utf-8 -*-
"""Migración a 19.0.2.0.0: credenciales cifradas y base_url por proveedor.

Está aquí y no dentro del script de migrations/ para poder probarla con un
test sobre una columna en texto plano recreada a mano.
"""
import logging

from odoo.tools.sql import column_exists

from .registry import LEGACY_BASE_URL_DEFAULT, PROVIDER_REGISTRY
from .vault import AiVault

_logger = logging.getLogger(__name__)

TABLE = 'ai_provider_config'
LEGACY_COLUMN = 'api_key_legacy'


def rename_plaintext_column(cr):
    """pre-migrate: aparta la columna en texto plano antes de que el ORM
    cargue el campo api_key nuevo (ya no almacenado)."""
    if column_exists(cr, TABLE, 'api_key') and not column_exists(cr, TABLE, LEGACY_COLUMN):
        cr.execute('ALTER TABLE %s RENAME COLUMN api_key TO %s' % (TABLE, LEGACY_COLUMN))


def encrypt_legacy_api_keys(env):
    """post-migrate: cifra cada clave, comprueba que al descifrar sale la
    misma, y SOLO si todas coinciden borra la columna en texto plano. Ante
    cualquier discrepancia lanza, y la actualización del módulo se revierte
    entera sin haber tocado nada."""
    cr = env.cr
    if not column_exists(cr, TABLE, LEGACY_COLUMN):
        return 0
    vault = AiVault(env)
    cr.execute(
        "SELECT id, %s FROM %s WHERE COALESCE(%s, '') != ''"
        % (LEGACY_COLUMN, TABLE, LEGACY_COLUMN)
    )
    rows = cr.fetchall()
    for record_id, plaintext in rows:
        clean = plaintext.strip()
        token = vault.encrypt(clean)
        if vault.decrypt(token) != clean:
            raise RuntimeError(
                'ai_agent_core: la API Key del proveedor %s no se re-descifra igual; '
                'se aborta la migración sin borrar nada.' % record_id
            )
        cr.execute('UPDATE %s SET api_key_encrypted = %%s WHERE id = %%s' % TABLE, (token, record_id))
    cr.execute('ALTER TABLE %s DROP COLUMN %s' % (TABLE, LEGACY_COLUMN))
    if rows and not vault.key_comes_from_env():
        _logger.warning(
            'ai_agent_core: %s API Keys cifradas con una clave guardada en la base; '
            'define ORBYLS_AI_VAULT_KEY para que un volcado no las revele.', len(rows))
    _logger.info('ai_agent_core: %s API Keys migradas a almacenamiento cifrado.', len(rows))
    return len(rows)


def reset_legacy_base_urls(cr):
    """base_url tenía por defecto la URL de Ollama en TODOS los proveedores.
    Ahora el adaptador OpenAI la usa: sin esto, OpenAI llamaría a Ollama.
    Solo se toca el valor por defecto viejo o vacío; una URL puesta a mano
    (un proxy, un gateway) se respeta."""
    for code, spec in PROVIDER_REGISTRY.items():
        if code == 'ollama':
            continue
        cr.execute(
            'UPDATE %s SET base_url = %%s WHERE provider = %%s '
            'AND (base_url IS NULL OR base_url = %%s)' % TABLE,
            (spec.get('base_url'), code, LEGACY_BASE_URL_DEFAULT),
        )
