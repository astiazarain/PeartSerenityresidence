{
    'name': 'Peart Serenity - Care Services',
    'version': '19.0.1.0.0',
    'category': 'Services/Care Management',
    'summary': 'Care intake, service catalog and website quotation flow for Peart Serenity Residence',
    'description': """
Peart Serenity Residence - Care Services
=========================================

Provides the default catalog of care services/plans as sellable products,
a dedicated sales team for care admissions, and a quotation template used
to flag quotations that originate from the public website's care request
flow.

Also provides:

- The Care Admission Request model (peart.admission), mirroring the
  Admission Form sections A-G, with automatic contact and CRM lead
  creation and a New -> Assessed -> Quoted -> Admitted pipeline.
- A public JSON API consumed by the website to submit quote requests and
  register contacts on account sign-up.
""",
    'author': 'Peart Serenity Residence',
    'website': 'https://peartserenityresidence.com',
    'license': 'LGPL-3',
    'depends': ['sale_management', 'crm', 'website', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/crm_team_data.xml',
        'data/crm_stage_data.xml',
        'data/sale_order_template_data.xml',
        'data/product_data.xml',
        'views/peart_admission_views.xml',
    ],
    'installable': True,
    'application': True,
}
