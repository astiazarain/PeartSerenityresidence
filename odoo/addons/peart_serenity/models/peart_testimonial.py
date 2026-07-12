from odoo import fields, models


class PeartTestimonial(models.Model):
    _name = 'peart.testimonial'
    _description = 'Family Testimonial'
    _order = 'featured desc, create_date desc'

    author_name = fields.Char(required=True)
    relation = fields.Char(required=True, help='e.g. Daughter, Son, Referring Physician')
    location = fields.Char()
    content = fields.Text(required=True)
    rating = fields.Integer(default=5)
    approved = fields.Boolean(default=True, help='Only approved testimonials are shown on the website.')
    featured = fields.Boolean(help='Featured testimonials are shown first.')
