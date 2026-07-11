{
    'name': 'Peart Serenity - Care Services',
    'version': '19.0.1.0.0',
    'category': 'Services/Care Management',
    'summary': 'Care service catalog and website quotation flow for Peart Serenity Residence',
    'description': """
Peart Serenity Residence - Care Services
=========================================

Provides the default catalog of care services/plans as sellable products,
a dedicated sales team for care admissions, and a quotation template used
to flag quotations that originate from the public website's care request
flow. Intake/assessment automation and the website API are added in later
releases of this module.
""",
    'author': 'Peart Serenity Residence',
    'website': 'https://peartserenityresidence.com',
    'license': 'LGPL-3',
    'depends': ['sale_management', 'crm', 'website'],
    'data': [
        'data/crm_team_data.xml',
        'data/sale_order_template_data.xml',
        'data/product_data.xml',
    ],
    'installable': True,
    'application': True,
}
