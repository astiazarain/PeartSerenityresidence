"""Level-2 "sensitive" ARIA Clínica actions: they mutate data, so unlike the
level-0/1 tools in ai_clinical_assistant.py they only ever run once approved
- see peart.clinical.action.request, the only caller of these two methods.
Calling them directly bypasses nothing that a developer console couldn't
already bypass; the actual gate is that no UI in this module calls them
except through an approved request.
"""
from odoo import _, api, models
from odoo.exceptions import AccessError, UserError

from .ai_clinical_assistant import CLINICAL_ROLES

# model key (used in the UI/JSON payload) -> (model name, resident field)
FAMILY_VISIBLE_TARGETS = {
    'daily_log': ('peart.daily.log', 'resident_id'),
    'incident': ('peart.incident', 'resident_id'),
    'condition': ('peart.resident.condition', 'resident_id'),
    'allergy': ('peart.resident.allergy', 'resident_id'),
    'medication': ('peart.resident.medication', 'resident_id'),
    'care_plan': ('peart.resident.care.plan', 'resident_id'),
    'assessment': ('peart.resident.assessment', 'resident_id'),
    'document': ('peart.resident.document', 'resident_id'),
}


class AiClinicalActions(models.AbstractModel):
    _name = 'ai.clinical.actions'
    _description = 'ARIA Clínica - approval-gated actions (level 2)'

    def _check_role(self):
        if not any(self.env.user.has_group(g) for g in CLINICAL_ROLES):
            raise AccessError(_('This action is only available to Doctor, Nurse and CEO.'))

    @api.model
    def create_nursing_task(self, resident_id, title, note=False, assignee_login=False):
        """Creates ONE follow-up activity, linked to the resident, for a
        specific nurse (assignee_login) or broadcast to every active nurse
        if none was given."""
        self._check_role()
        resident = self.env['peart.resident'].browse(resident_id).exists()
        if not resident:
            raise UserError(_('Resident not found.'))
        resident.check_access('read')
        if not (title or '').strip():
            raise UserError(_('A task needs a title.'))

        nurse_group = self.env.ref('peart_clinical_record.group_clinical_nurse')
        nurses = self.env['res.users'].sudo().search([('group_ids', 'in', nurse_group.id)])
        if assignee_login:
            assignees = nurses.filtered(lambda u: u.login == assignee_login)
            if not assignees:
                raise UserError(_('%s is not an active nurse.', assignee_login))
        else:
            assignees = nurses
        if not assignees:
            raise UserError(_('There is no active nurse to assign this task to.'))

        created = self.env['mail.activity']
        for user in assignees:
            created |= resident.sudo().activity_schedule(
                'peart_clinical_record.mail_activity_type_clinical_task',
                user_id=user.id, summary=title, note=note or False)
        return {'created': len(created), 'resident': resident.name, 'assignees': assignees.mapped('name')}

    @api.model
    def mark_family_visible(self, model_key, record_id):
        """Sets family_visible=True on one whitelisted clinical record."""
        self._check_role()
        if model_key not in FAMILY_VISIBLE_TARGETS:
            raise UserError(_('Unknown record type.'))
        model_name, resident_field = FAMILY_VISIBLE_TARGETS[model_key]
        record = self.env[model_name].browse(record_id).exists()
        if not record:
            raise UserError(_('Record not found.'))
        record.check_access('write')
        record.write({'family_visible': True})
        return {'model': model_name, 'record_id': record_id, 'resident': record[resident_field].name}
