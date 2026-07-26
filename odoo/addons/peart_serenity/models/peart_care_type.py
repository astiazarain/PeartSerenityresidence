from odoo import models


class PeartCareType(models.Model):
    _name = 'peart.care.type'
    _description = 'Care Type'
    _inherit = 'peart.nomenclator.mixin'
