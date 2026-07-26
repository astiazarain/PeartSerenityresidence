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
    care_type = fields.Many2one(
        'peart.care.type', required=True, domain=[('active', '=', True)],
        default=lambda self: self.env.ref('peart_serenity.care_type_long_term', raise_if_not_found=False))
    urgency = fields.Many2one(
        'peart.urgency.level', required=True, domain=[('active', '=', True)],
        default=lambda self: self.env.ref('peart_serenity.urgency_medium', raise_if_not_found=False))
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
