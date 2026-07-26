from odoo import fields, models


class PeartNomenclatorMixin(models.AbstractModel):
    _name = 'peart.nomenclator.mixin'
    _description = 'Nomenclator Mixin'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, help='Technical key used by the website and internal logic. Keep stable once in use.')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True, help='Inactive values are hidden from the website and cannot be selected.')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'This code is already used by another value.'),
    ]
