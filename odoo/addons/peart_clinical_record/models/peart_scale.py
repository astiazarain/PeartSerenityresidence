from odoo import fields, models


class PeartScale(models.Model):
    _name = 'peart.scale'
    _description = 'Assessment Scale'
    _order = 'name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    active = fields.Boolean(default=True)
    frequency_days = fields.Integer(
        string='Repeat every (days)', help='How often this assessment should be repeated.')
    item_ids = fields.One2many('peart.scale.item', 'scale_id')
    band_ids = fields.One2many('peart.scale.band', 'scale_id')
    max_score = fields.Integer(compute='_compute_max_score')

    _code_uniq = models.Constraint('unique(code)', 'Scale code must be unique.')

    def _compute_max_score(self):
        for scale in self:
            scale.max_score = sum(
                max(item.option_ids.mapped('points') or [0]) for item in scale.item_ids)

    def band_for(self, total):
        self.ensure_one()
        return self.band_ids.filtered(lambda b: b.score_min <= total <= b.score_max)[:1]


class PeartScaleItem(models.Model):
    _name = 'peart.scale.item'
    _description = 'Assessment Scale Item'
    _order = 'scale_id, sequence, id'

    scale_id = fields.Many2one('peart.scale', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True, translate=True)
    option_ids = fields.One2many('peart.scale.option', 'item_id')


class PeartScaleOption(models.Model):
    _name = 'peart.scale.option'
    _description = 'Assessment Scale Answer Option'
    _order = 'item_id, sequence, id'

    item_id = fields.Many2one('peart.scale.item', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True, translate=True)
    points = fields.Integer(required=True)


class PeartScaleBand(models.Model):
    _name = 'peart.scale.band'
    _description = 'Assessment Scale Interpretation Band'
    _order = 'scale_id, score_min'

    scale_id = fields.Many2one('peart.scale', required=True, ondelete='cascade')
    name = fields.Char(string='Interpretation', required=True, translate=True)
    score_min = fields.Integer(required=True)
    score_max = fields.Integer(required=True)
    severity = fields.Selection(
        [('ok', 'OK'), ('warn', 'Watch'), ('danger', 'High concern')], required=True, default='ok')
