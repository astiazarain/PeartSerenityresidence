from odoo import models


class PeartUrgencyLevel(models.Model):
    _name = 'peart.urgency.level'
    _description = 'Urgency Level'
    _inherit = 'peart.nomenclator.mixin'
