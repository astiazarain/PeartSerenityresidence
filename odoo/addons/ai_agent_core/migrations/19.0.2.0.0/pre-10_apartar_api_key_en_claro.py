# -*- coding: utf-8 -*-
"""Aparta la columna api_key (texto plano) antes de que cargue el modelo.

En 19.0.2.0.0 el campo api_key deja de guardarse: la credencial vive
cifrada en api_key_encrypted. Se renombra en vez de borrarla para que el
post-migrate la cifre y solo entonces la elimine.
"""
from odoo.addons.ai_agent_core.llm.migration import rename_plaintext_column


def migrate(cr, version):
    if not version:
        return
    rename_plaintext_column(cr)
