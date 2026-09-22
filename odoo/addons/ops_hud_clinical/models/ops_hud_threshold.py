from odoo import api, fields, models

STATUS_RANK = {'none': -1, 'info': 0, 'ok': 1, 'warn': 2, 'danger': 3}


def worst(*statuses):
    """The most severe of several statuses (ok < warn < danger)."""
    return max(statuses, key=lambda s: STATUS_RANK.get(s, 0))


class OpsHudThreshold(models.Model):
    _name = 'ops.hud.threshold'
    _description = 'HUD indicator threshold (traffic light)'
    _order = 'id'

    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True, translate=True)
    unit = fields.Char()
    warn = fields.Float(string='Yellow from')
    danger = fields.Float(string='Red from')
    higher_is_worse = fields.Boolean(default=True)
    direction = fields.Char(compute='_compute_direction')

    _code_uniq = models.Constraint('unique(code)', 'Threshold code must be unique.')

    @api.depends('higher_is_worse')
    def _compute_direction(self):
        for rec in self:
            rec.direction = 'higher is worse' if rec.higher_is_worse else 'lower is worse'

    @api.model
    def status(self, code, value):
        """ok / warn / danger for `value` against the threshold `code`.
        Thresholds are configuration, not patient data, so any role that
        can open the panel reads them (sudo)."""
        th = self.sudo().search([('code', '=', code)], limit=1)
        if not th:
            return 'ok'
        if th.higher_is_worse:
            return 'danger' if value >= th.danger else 'warn' if value >= th.warn else 'ok'
        return 'danger' if value < th.danger else 'warn' if value < th.warn else 'ok'
