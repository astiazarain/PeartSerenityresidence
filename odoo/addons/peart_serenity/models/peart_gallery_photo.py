from odoo import fields, models


class PeartGalleryPhoto(models.Model):
    _name = 'peart.gallery.photo'
    _description = 'Gallery Photo'
    _order = 'sequence, id'

    title = fields.Char(required=True)
    category = fields.Selection([
        ('facility', 'Facility'),
        ('activities', 'Activities'),
        ('events', 'Events'),
    ], required=True, default='facility')
    image = fields.Image(required=True, max_width=1920, max_height=1920)
    image_512 = fields.Image(string='Thumbnail', related='image', max_width=512, max_height=512, store=True)
    sequence = fields.Integer(default=10)
    published = fields.Boolean(default=True, help='Only published photos are shown on the website.')
