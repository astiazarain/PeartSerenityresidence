from odoo import api, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def peart_find_or_create(self, name, email=None, phone=None):
        """Find a contact by email, or create one. Used by both the website
        quote form and account registration so the same family doesn't end
        up with duplicate contacts in Odoo.
        """
        partner = self.browse()
        if email:
            partner = self.search([('email', '=', email)], limit=1)
        if not partner:
            partner = self.create({'name': name, 'email': email, 'phone': phone})
        return partner
