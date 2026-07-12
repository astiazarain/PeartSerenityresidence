{
    'name': 'Peart Serenity - Care Services',
    'version': '19.0.1.0.0',
    'category': 'Services/Care Management',
    'summary': 'Care intake, service catalog and website backend for Peart Serenity Residence',
    'description': """
Peart Serenity Residence - Care Services
=========================================

Odoo is the sole backend for peartserenityresidence.com: the website talks
to it exclusively through the public JSON API in this module (no other
datastore involved).

Provides:

- The default catalog of care services/plans as sellable products, a
  dedicated sales team for care admissions, and a quotation template used
  to flag quotations that originate from the public website.
- The Care Admission Request model (peart.admission), mirroring the
  Admission Form sections A-G, with automatic contact and CRM lead
  creation and a New -> Assessed -> Quoted -> Admitted pipeline.
- Tour bookings, waitlist entries and family testimonials as their own
  models, all manageable from the Care Admissions backend menu.
- Account sign-up/login backed by real Odoo portal users, and a family
  portal API scoped to the logged-in user's own records.
""",
    'author': 'Peart Serenity Residence',
    'website': 'https://peartserenityresidence.com',
    'license': 'LGPL-3',
    'depends': ['sale_management', 'crm', 'website', 'mail', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'data/crm_team_data.xml',
        'data/crm_stage_data.xml',
        'data/sale_order_template_data.xml',
        'data/product_data.xml',
        'data/testimonial_data.xml',
        'views/peart_admission_views.xml',
        'views/peart_content_views.xml',
    ],
    'installable': True,
    'application': True,
}
