import base64
import os

from . import models
from . import controllers


def _set_company_branding(env):
    """Brand the default company record so the redesigned PDF layout (logo,
    colors, address) renders correctly. base.main_company ships noupdate=1,
    so this can't be done through a data XML record -- it would silently be
    skipped on every module update.
    """
    company = env.ref('base.main_company', raise_if_not_found=False)
    if not company:
        return

    logo_path = os.path.join(os.path.dirname(__file__), 'static', 'src', 'img', 'logo.jpg')
    with open(logo_path, 'rb') as logo_file:
        logo_b64 = base64.b64encode(logo_file.read())

    layout = env.ref('peart_serenity.external_layout_peart', raise_if_not_found=False)

    company.write({
        'name': 'Peart Serenity Residence',
        'logo': logo_b64,
        'street': 'St. James Parish',
        'city': 'Montego Bay',
        'country_id': env.ref('base.jm').id,
        'email': 'care@peartserenity.com',
        'phone': '+1 (876) 555-0192',
        'website': 'https://peartserenityresidence.com',
        'primary_color': '#C8920A',
        'secondary_color': '#0D0D0D',
        'font': 'Montserrat',
        'external_report_layout_id': layout.id if layout else False,
        'report_footer': '<p>Peart Serenity Residence &#8226; Montego Bay, St. James, Jamaica &#8226; care@peartserenity.com</p>',
    })
