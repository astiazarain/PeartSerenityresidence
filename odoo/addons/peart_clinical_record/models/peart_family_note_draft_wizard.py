from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PeartFamilyNoteDraftWizard(models.TransientModel):
    """'Draft with ARIA' popup: generates a family-facing rewrite of an
    internal note and shows it for review. Nothing is written to the source
    record (daily log's family_note / incident's family_summary) until the
    user reviews the draft and clicks Save - this is the level-1
    "preparation" pattern: the model prepares, a human decides."""
    _name = 'peart.family.note.draft.wizard'
    _description = 'Draft a family note with ARIA Clínica'

    source_kind = fields.Selection(
        [('daily_log', 'Shift log'), ('incident', 'Incident')], required=True)
    daily_log_id = fields.Many2one('peart.daily.log')
    incident_id = fields.Many2one('peart.incident')
    resident_name = fields.Char(compute='_compute_resident_name')
    source_text = fields.Text(compute='_compute_source_text', readonly=True)
    draft = fields.Text(string='Draft for the family')
    route = fields.Char(readonly=True)
    info = fields.Char(readonly=True)

    @api.depends('daily_log_id', 'incident_id')
    def _compute_resident_name(self):
        for rec in self:
            rec.resident_name = (rec.daily_log_id or rec.incident_id).resident_id.name

    @api.depends('daily_log_id.notes', 'incident_id.description')
    def _compute_source_text(self):
        for rec in self:
            rec.source_text = rec.daily_log_id.notes if rec.source_kind == 'daily_log' else rec.incident_id.description

    def _record_id(self):
        self.ensure_one()
        return (self.daily_log_id if self.source_kind == 'daily_log' else self.incident_id).id

    def action_generate(self):
        self.ensure_one()
        result = self.env['ai.clinical.assistant'].draft_family_text(self.source_kind, self._record_id())
        self.write({'draft': result['draft'] or self.draft, 'route': result['route'],
                    'info': result.get('reply') or False})
        return self._reopen()

    def action_save(self):
        self.ensure_one()
        if not (self.draft or '').strip():
            raise UserError(_('Write or generate a draft first.'))
        target_field = 'family_note' if self.source_kind == 'daily_log' else 'family_summary'
        target = self.daily_log_id if self.source_kind == 'daily_log' else self.incident_id
        target.write({target_field: self.draft})
        return {'type': 'ir.actions.act_window_close'}

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': self.id,
            'view_mode': 'form', 'target': 'new',
        }

    @api.model
    def action_open_for_daily_log(self, daily_log_id):
        wizard = self.create({'source_kind': 'daily_log', 'daily_log_id': daily_log_id})
        return wizard._reopen()

    @api.model
    def action_open_for_incident(self, incident_id):
        wizard = self.create({'source_kind': 'incident', 'incident_id': incident_id})
        return wizard._reopen()
