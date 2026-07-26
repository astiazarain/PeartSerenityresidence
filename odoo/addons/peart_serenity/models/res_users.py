from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    # Lets family portal users sign in with a memorable handle instead of
    # their email, in addition to email/phone (see _get_login_domain below).
    peart_username = fields.Char(string='Username', copy=False)

    _sql_constraints = [
        ('peart_username_uniq', 'unique(peart_username)', 'This username is already taken.'),
    ]

    @api.model
    def _get_login_domain(self, login):
        # Allow authenticating with the account email, phone or username
        # (project/src/pages/Auth.tsx sends whichever one the visitor typed).
        return ['|', '|', '|',
                ('login', '=', login),
                ('partner_id.email', '=', login),
                ('partner_id.phone', '=', login),
                ('peart_username', '=', login),
                ]
