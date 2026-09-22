# -*- coding: utf-8 -*-
"""Cifra las API Keys existentes y corrige la base_url heredada.

Sin pérdida de configuración: proveedor, modelo elegido, catálogo, modelo
de imagen, compañía y valor por defecto no se tocan. Si alguna clave no se
re-descifra igual, la migración lanza y la actualización entera se revierte
con la columna en claro intacta.
"""
from odoo import SUPERUSER_ID, api

from odoo.addons.ai_agent_core.llm.migration import (
    encrypt_legacy_api_keys,
    reset_legacy_base_urls,
)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    encrypt_legacy_api_keys(env)
    reset_legacy_base_urls(cr)
