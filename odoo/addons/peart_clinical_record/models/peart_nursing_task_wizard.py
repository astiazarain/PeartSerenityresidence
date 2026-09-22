from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PeartNursingTaskWizard(models.TransientModel):
    """Collects title/note/assignee, then files a
    peart.clinical.action.request for a Doctor to approve - it never
    creates the activity itself."""
    _name = 'peart.nursing.task.wizard'
    _description = 'Request a nursing task (ARIA Clínica, needs approval)'

    resident_id = fields.Many2one('peart.resident', required=True)
    title = fields.Char(required=True)
    note = fields.Text()
    assignee_id = fields.Many2one(
        'res.users', string='Assign to (optional)',
        domain=lambda self: [('group_ids', 'in', self.env.ref('peart_clinical_record.group_clinical_nurse').id)],
        help='Leave empty to notify every nurse.')

    def action_request(self):
        self.ensure_one()
        if not (self.title or '').strip():
            raise UserError(_('A task needs a title.'))
        payload = {'resident_id': self.resident_id.id, 'title': self.title, 'note': self.note or False,
                   'assignee_login': self.assignee_id.login if self.assignee_id else False}
        preview = _('Nursing task for %(resident)s: %(title)s', resident=self.resident_id.name, title=self.title)
        self.env['peart.clinical.action.request'].request('nursing_task', self.resident_id.id, preview, payload)
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def action_open_for_resident(self, resident_id):
        wizard = self.create({'resident_id': resident_id})
        return {
            'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': wizard.id,
            'view_mode': 'form', 'target': 'new', 'name': _('Request a nursing task'),
        }
