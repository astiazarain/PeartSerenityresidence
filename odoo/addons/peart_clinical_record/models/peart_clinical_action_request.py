"""A small, self-contained approval flow for ARIA Clínica's level-2 actions.

Deliberately NOT built on ai_agent_core's ai.approval.request/Vault: that
model's ACL requires group_ai_agent_user/manager, which clinical staff do
not have and should not be granted just for this - it would also hand them
ORM access to every OTHER agent's approvals and conversations (Social Media,
Customer Service), which is unrelated data outside clinical governance.
The ai.agent.tool catalog rows still exist for these two actions (so they
show up in the Skills panel), but they are only ever executed through a
peart.clinical.action.request that a Doctor has approved.
"""
import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PeartClinicalActionRequest(models.Model):
    _name = 'peart.clinical.action.request'
    _description = 'ARIA Clínica - Pending Action (approval required)'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(compute='_compute_name')
    kind = fields.Selection(
        [('nursing_task', 'Create nursing task'), ('family_visible', 'Mark visible to family')],
        required=True)
    resident_id = fields.Many2one('peart.resident', required=True, ondelete='cascade', index=True)
    preview = fields.Char(required=True, help='Human-readable summary shown to the approver.')
    payload_json = fields.Text(required=True)

    state = fields.Selection(
        [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'),
         ('executed', 'Executed'), ('error', 'Error')],
        default='pending', required=True, tracking=True)
    requested_by_id = fields.Many2one('res.users', default=lambda s: s.env.user, readonly=True)
    approved_by_id = fields.Many2one('res.users', readonly=True)
    result_text = fields.Char(readonly=True)
    error_message = fields.Char(readonly=True)

    def _compute_name(self):
        for rec in self:
            rec.name = '%s - %s' % (dict(rec._fields['kind'].selection).get(rec.kind, ''), rec.resident_id.name)

    def get_payload(self):
        self.ensure_one()
        return json.loads(self.payload_json or '{}')

    @api.model
    def request(self, kind, resident_id, preview, payload):
        """Creates a pending request and notifies the Doctor(s) who can
        approve it. `payload` is passed as-is to ai.clinical.actions on
        approval - build it, don't trust it, at the call site."""
        record = self.create({
            'kind': kind, 'resident_id': resident_id, 'preview': preview,
            'payload_json': json.dumps(payload),
        })
        record._notify_doctors()
        return record

    def _notify_doctors(self):
        self.ensure_one()
        doctors = self.env['res.users'].sudo().search(
            [('group_ids', 'in', self.env.ref('peart_clinical_record.group_clinical_doctor').id)])
        if not doctors:
            return
        self.message_notify(
            partner_ids=doctors.partner_id.ids,
            subject=_('Pending approval: %s', self.name),
            body=_('%(who)s requests: %(what)s. Review it under Residents > Pending Actions.',
                   who=self.requested_by_id.name, what=self.preview),
            subtype_xmlid='mail.mt_note',
        )

    def action_approve(self):
        for rec in self:
            if rec.state != 'pending':
                raise UserError(_('Only pending requests can be approved.'))
            if not self.env.user.has_group('peart_clinical_record.group_clinical_doctor'):
                raise UserError(_('Only a Doctor can approve this.'))
            if self.env.user == rec.requested_by_id:
                raise UserError(_('You cannot approve your own request.'))
            rec.write({'state': 'approved', 'approved_by_id': self.env.uid})
            rec._execute()

    def action_reject(self):
        for rec in self:
            if rec.state != 'pending':
                raise UserError(_('Only pending requests can be rejected.'))
            is_doctor = self.env.user.has_group('peart_clinical_record.group_clinical_doctor')
            if not (is_doctor or self.env.user == rec.requested_by_id):
                raise UserError(_('Only a Doctor, or the person who asked for it, can reject this.'))
            rec.write({'state': 'rejected', 'approved_by_id': self.env.uid})

    def _execute(self):
        self.ensure_one()
        Actions = self.env['ai.clinical.actions']
        method = {'nursing_task': Actions.create_nursing_task,
                  'family_visible': Actions.mark_family_visible}[self.kind]
        try:
            result = method(**self.get_payload())
            self.write({'state': 'executed', 'result_text': str(result)[:250]})
        except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
            self.write({'state': 'error', 'error_message': str(exc)[:250]})
            # Flush now: we are about to re-raise, and a caller that catches
            # this and immediately re-reads `state` (as tests, and a human
            # retrying from the UI, both do) must see 'error', not a write
            # that never made it past the ORM's in-memory cache because the
            # exception unwound before anything else triggered a flush.
            self.flush_recordset(['state', 'error_message'])
            raise
