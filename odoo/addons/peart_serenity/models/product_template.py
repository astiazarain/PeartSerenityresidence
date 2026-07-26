from odoo import fields, models


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'website.published.mixin']

    website_features = fields.Text(
        string='Website Features',
        help='One bullet point per line. Shown as a checklist on the public Services page.')
    website_price_period = fields.Selection([
        ('day', 'Per Day'),
        ('week', 'Per Week'),
        ('month', 'Per Month'),
        ('custom', 'Custom Pricing (price hidden, "Custom" shown instead)'),
    ], string='Website Price Period', default='day',
        help='How the price is billed, used to format the price shown on the public Services page.')
