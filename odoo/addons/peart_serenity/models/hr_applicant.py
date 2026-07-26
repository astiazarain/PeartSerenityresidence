from odoo import fields, models


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    years_experience = fields.Integer(string='Years of Experience')
    nursing_license_number = fields.Char(string='Nursing License Number')
    references = fields.Text(string='References')
