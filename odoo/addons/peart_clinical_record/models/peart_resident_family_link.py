from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PeartResidentFamilyLink(models.Model):
    _name = 'peart.resident.family.link'
    _description = 'Resident Family Access Link'
    _inherit = ['mail.thread']
    _order = 'resident_id, id'

    resident_id = fields.Many2one('peart.resident', required=True, ondelete='cascade', index=True)
    user_id = fields.Many2one(
        'res.users', string='Portal User', required=True, ondelete='cascade', index=True,
        domain=[('share', '=', True)])
    relationship = fields.Char(tracking=True)
    is_primary = fields.Boolean(string='Primary contact')
    access_enabled = fields.Boolean(
        default=False, tracking=True,
        help='Family can only see the record while this is enabled. It can only be enabled '
             'once a family-access consent is on file.')
    granted_by_id = fields.Many2one('res.users', readonly=True)
    granted_date = fields.Datetime(readonly=True)

    _resident_user_uniq = models.Constraint(
        'unique(resident_id, user_id)', 'This user is already linked to the resident.')

    @api.constrains('user_id')
    def _check_portal_user(self):
        for rec in self:
            if not rec.user_id.share:
                raise ValidationError(_('Only portal (family) users can be linked; staff already have their own roles.'))

    @api.constrains('access_enabled')
    def _check_consent(self):
        for rec in self.filtered('access_enabled'):
            if not rec.resident_id.has_consent('family_access'):
                raise ValidationError(_(
                    'Record a family-access consent for %s before enabling family access.',
                    rec.resident_id.name))

    def write(self, vals):
        if vals.get('access_enabled'):
            vals = dict(vals, granted_by_id=self.env.uid, granted_date=fields.Datetime.now())
        return super().write(vals)
