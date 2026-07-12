from odoo import api, fields, models


class PeartTourBooking(models.Model):
    _name = 'peart.tour.booking'
    _description = 'Facility Tour Booking'
    _order = 'create_date desc'

    name = fields.Char(required=True, string='Visitor Name')
    email = fields.Char(required=True)
    phone = fields.Char()
    partner_id = fields.Many2one('res.partner', readonly=True)
    preferred_date = fields.Date(required=True)
    preferred_time = fields.Selection([
        ('morning', 'Morning (9am - 12pm)'),
        ('afternoon', 'Afternoon (1pm - 5pm)'),
    ], default='morning', required=True)
    party_size = fields.Integer(default=1)
    message = fields.Text()
    status = fields.Selection([
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='pending', required=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        Partner = self.env['res.partner']
        for rec in records:
            if not rec.partner_id:
                rec.partner_id = Partner.peart_find_or_create(rec.name, email=rec.email, phone=rec.phone)
        return records
