from odoo import _, api, fields, models


class PeartClinicalAssistantWizard(models.TransientModel):
    """'Ask ARIA' popup, opened from a resident or a shift log. Deliberately
    a plain question/answer form (not a full chat) for phase 3 - the model
    behind it (ai.clinical.assistant) is the same one the HUD chat and the
    Coordinator use, so all three surfaces answer identically and audit the
    same way."""
    _name = 'peart.clinical.assistant.wizard'
    _description = 'Ask ARIA Clínica'

    resident_id = fields.Many2one('peart.resident')
    resident_name = fields.Char(related='resident_id.name', readonly=True)
    message = fields.Text()
    reply = fields.Text(readonly=True)
    route = fields.Char(readonly=True)
    history = fields.Text(default='[]', readonly=True)  # JSON [{role, content}, ...]

    def action_ask(self):
        self.ensure_one()
        import json
        history = json.loads(self.history or '[]')
        result = self.env['ai.clinical.assistant'].ask(
            self.message, resident_id=self.resident_id.id, history=history,
            lang=(self.env.user.lang or '')[:2] or None)
        history += [{'role': 'user', 'content': self.message}, {'role': 'agent', 'content': result['reply']}]
        self.write({'reply': result['reply'], 'route': result['route'],
                    'history': json.dumps(history), 'message': ''})
        return {
            'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': self.id,
            'view_mode': 'form', 'target': 'new',
        }

    @api.model
    def action_open_for_resident(self, resident_id):
        wizard = self.create({'resident_id': resident_id})
        return {
            'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': wizard.id,
            'view_mode': 'form', 'target': 'new', 'name': _('Ask ARIA Clínica'),
        }
