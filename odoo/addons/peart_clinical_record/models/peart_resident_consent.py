from odoo import api, fields, models


class PeartResidentConsent(models.Model):
    _name = 'peart.resident.consent'
    _description = 'Resident Consent'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    resident_id = fields.Many2one('peart.resident', required=True, ondelete='cascade', index=True)
    kind = fields.Selection([
        ('data_processing', 'Health data processing'),
        ('family_access', 'Family access to the record'),
        ('ai_assistant', 'AI assistant (ARIA) processing'),
        ('treatment', 'Care and treatment'),
        ('photo', 'Photos / media'),
    ], required=True, tracking=True)
    state = fields.Selection(
        [('granted', 'Granted'), ('revoked', 'Revoked')], default='granted', required=True, tracking=True)
    date = fields.Date(default=fields.Date.context_today, required=True)
    revoked_date = fields.Date(readonly=True)
    signed_by = fields.Char(required=True, help='Resident, or legal representative if the resident cannot sign.')
    signer_relationship = fields.Char(string='Signer relationship')
    document = fields.Binary(string='Signed document', attachment=True)
    document_filename = fields.Char()
    notes = fields.Text()

    def action_revoke(self):
        self.write({'state': 'revoked', 'revoked_date': fields.Date.context_today(self)})
        # Losing family-access consent immediately cuts the family's access.
        for rec in self.filtered(lambda c: c.kind == 'family_access'):
            if not rec.resident_id.has_consent('family_access'):
                rec.resident_id.family_link_ids.write({'access_enabled': False})
