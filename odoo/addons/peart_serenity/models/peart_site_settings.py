from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PeartSiteSettings(models.Model):
    _name = 'peart.site.settings'
    _description = 'Public Website Settings (social links, WhatsApp)'

    name = fields.Char(default='Website Settings', required=True)

    whatsapp_number = fields.Char(
        required=True,
        help='Full number in international format, digits only (e.g. 18765550192). '
             'Used to build the wa.me link on the public website.')
    whatsapp_message = fields.Char(
        required=True, default="Hello! I'm interested in learning more about Peart Serenity Residence.",
        help='Pre-filled message opened in WhatsApp when a visitor clicks the button.')

    facebook_url = fields.Char()
    instagram_url = fields.Char()
    tiktok_url = fields.Char()
    linkedin_url = fields.Char()

    @api.model_create_multi
    def create(self, vals_list):
        if self.search_count([]):
            raise ValidationError('Only one Website Settings record is allowed. Edit the existing one instead.')
        return super().create(vals_list)
