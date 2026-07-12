from odoo import api, fields, models


class PeartWaitlist(models.Model):
    _name = 'peart.waitlist'
    _description = 'Care Waitlist Entry'
    _order = 'create_date desc'

    name = fields.Char(required=True)
    email = fields.Char(required=True)
    phone = fields.Char()
    partner_id = fields.Many2one('res.partner', readonly=True)
    country = fields.Char(default='Jamaica')
    care_type = fields.Selection([
        ('long_term', 'Long-Term Residential'),
        ('private_suite', 'Private Suite'),
        ('respite', 'Respite Care'),
        ('recovery', 'Post-Surgical Recovery'),
        ('specialized', 'Specialized Care'),
    ], default='long_term', required=True)
    urgency = fields.Selection([
        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High'),
    ], default='medium', required=True)
    notes = fields.Text()
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        Partner = self.env['res.partner']
        for rec in records:
            if not rec.partner_id:
                rec.partner_id = Partner.peart_find_or_create(rec.name, email=rec.email, phone=rec.phone)
        return records
