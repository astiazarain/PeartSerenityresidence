from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    hud_bed_capacity = fields.Integer(
        string='Bed capacity', config_parameter='ops_hud_clinical.bed_capacity')
