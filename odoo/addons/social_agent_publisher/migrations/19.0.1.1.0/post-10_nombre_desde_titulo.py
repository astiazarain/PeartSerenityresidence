# -*- coding: utf-8 -*-
"""Recalcula `name` de las publicaciones existentes.

`name` es un compute almacenado que antes salía de `topic` (la instrucción)
y ahora sale de `title`. Odoo no recalcula un campo almacenado solo porque
cambie su `@api.depends`: sin esto, el tablero seguiría mostrando la
instrucción de las publicaciones creadas antes del campo Título.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    posts = env['social.media.post'].search([])
    env.add_to_compute(posts._fields['name'], posts)
    env.flush_all()
