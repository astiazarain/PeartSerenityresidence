from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    peart_staff_ai_provider_id = fields.Many2one(
        'ai.provider.config', string='ARIA Clínica provider (staff)',
        config_parameter='peart_clinical_record.staff_ai_provider_id',
        domain=[('active', '=', True)],
        help='AI provider that answers staff (Doctor/Nurse/CEO) questions about residents. Resident data is '
             'sent to this provider (pseudonymised), so pick one approved for health data. There is no '
             'fallback: while this is empty, ARIA Clínica does not answer.')

    peart_family_ai_provider_id = fields.Many2one(
        'ai.provider.config', string='ARIA provider for families',
        config_parameter='peart_clinical_record.ai_provider_id',
        domain=[('active', '=', True)],
        help='AI provider that answers family questions about a resident. Resident data is sent '
             'to this provider, so pick one that is approved for health data. There is no '
             'fallback: while this is empty, ARIA does not answer families.')
