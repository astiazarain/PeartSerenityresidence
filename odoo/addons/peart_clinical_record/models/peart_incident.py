from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

SEVERE = ('moderate', 'serious', 'sentinel')


class PeartIncident(models.Model):
    _name = 'peart.incident'
    _description = 'Resident Incident Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'occurred_at desc'

    name = fields.Char(string='Reference', readonly=True, copy=False, default='New')
    resident_id = fields.Many2one('peart.resident', required=True, ondelete='restrict', index=True, tracking=True)
    occurred_at = fields.Datetime(default=fields.Datetime.now, required=True, tracking=True)
    kind = fields.Selection([
        ('fall', 'Fall'), ('injury', 'Injury'), ('medication', 'Medication error'),
        ('behaviour', 'Behaviour'), ('skin', 'Skin / pressure injury'), ('choking', 'Choking'),
        ('elopement', 'Wandering / elopement'), ('infection', 'Infection / illness'),
        ('other', 'Other')], required=True, tracking=True)
    severity = fields.Selection([
        ('minor', 'Minor - no harm'), ('moderate', 'Moderate - first aid / monitoring'),
        ('serious', 'Serious - medical treatment'), ('sentinel', 'Sentinel - hospital / death')],
        required=True, default='minor', tracking=True)
    location = fields.Char()
    description = fields.Text(required=True)
    immediate_action = fields.Text()
    injury_description = fields.Text()
    witnesses = fields.Char()
    reported_by_id = fields.Many2one('res.users', default=lambda s: s.env.user, readonly=True)

    physician_notified = fields.Boolean(tracking=True)
    physician_notified_at = fields.Datetime()
    family_notified = fields.Boolean(tracking=True)
    family_notified_at = fields.Datetime()
    family_notified_method = fields.Selection(
        [('phone', 'Phone'), ('in_person', 'In person'), ('email', 'Email'), ('whatsapp', 'WhatsApp')])
    follow_up = fields.Text()
    family_visible = fields.Boolean(string='Share with family', default=False)
    family_summary = fields.Text(
        help='Plain-language account for the family portal. Only shown when "Share with family" is on.')

    state = fields.Selection(
        [('open', 'Open'), ('review', 'Under review'), ('closed', 'Closed')], default='open', tracking=True)
    closed_by_id = fields.Many2one('res.users', readonly=True)
    closed_date = fields.Datetime(readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('peart.incident') or 'New'
        records = super().create(vals_list)
        records.filtered(lambda r: r.severity in ('serious', 'sentinel'))._notify_doctors()
        return records

    def _notify_doctors(self):
        group = self.env.ref('peart_clinical_record.group_clinical_doctor')
        doctors = self.env['res.users'].sudo().search([('group_ids', 'in', group.id)])
        for rec in self:
            for doctor in doctors:
                rec.sudo().activity_schedule(
                    'mail.mail_activity_data_todo', user_id=doctor.id,
                    summary=_('Review %(severity)s incident: %(resident)s', severity=rec.severity, resident=rec.resident_id.name))

    def write(self, vals):
        if any(rec.state == 'closed' for rec in self):
            raise UserError(_('A closed incident cannot be modified.'))
        res = super().write(vals)
        if vals.get('severity') in ('serious', 'sentinel'):
            self.filtered(lambda r: not r.activity_ids)._notify_doctors()
        return res

    def unlink(self):
        raise UserError(_('Incident reports cannot be deleted.'))

    def action_review(self):
        self.write({'state': 'review'})

    def action_draft_family_summary(self):
        self.ensure_one()
        return self.env['peart.family.note.draft.wizard'].action_open_for_incident(self.id)

    def action_request_family_visible(self):
        self.ensure_one()
        preview = _('Mark visible to family: incident %(ref)s of %(resident)s',
                    ref=self.name, resident=self.resident_id.name)
        self.env['peart.clinical.action.request'].request(
            'family_visible', self.resident_id.id, preview, {'model_key': 'incident', 'record_id': self.id})

    def action_close(self):
        for rec in self:
            if rec.severity in SEVERE:
                if not rec.physician_notified:
                    raise ValidationError(_('Record that the physician was notified before closing.'))
                if not rec.family_notified:
                    raise ValidationError(_('Record that the family was notified before closing.'))
            if not rec.follow_up:
                raise ValidationError(_('Describe the follow-up before closing.'))
        self.write({'state': 'closed', 'closed_by_id': self.env.uid, 'closed_date': fields.Datetime.now()})
        self.sudo().activity_ids.action_feedback()


class PeartResident(models.Model):
    _inherit = 'peart.resident'

    incident_ids = fields.One2many('peart.incident', 'resident_id')
