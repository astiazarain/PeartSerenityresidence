from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class PeartResidentAssessment(models.Model):
    _name = 'peart.resident.assessment'
    _description = 'Resident Assessment'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    resident_id = fields.Many2one('peart.resident', required=True, ondelete='cascade', index=True)
    scale_id = fields.Many2one('peart.scale', required=True, tracking=True)
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    assessor_id = fields.Many2one('res.users', string='Assessed by', default=lambda s: s.env.user, required=True)
    line_ids = fields.One2many('peart.resident.assessment.line', 'assessment_id')
    total = fields.Integer(compute='_compute_result', store=True)
    max_score = fields.Integer(related='scale_id.max_score')
    band_id = fields.Many2one('peart.scale.band', compute='_compute_result', store=True)
    severity = fields.Selection(related='band_id.severity', store=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Completed')], default='draft', tracking=True)
    notes = fields.Text()
    family_visible = fields.Boolean(string='Visible to family', default=False)
    name = fields.Char(compute='_compute_name')

    @api.depends('scale_id', 'date')
    def _compute_name(self):
        for rec in self:
            rec.name = '%s - %s' % (rec.scale_id.name or '', fields.Date.to_string(rec.date) if rec.date else '')

    @api.depends('line_ids.points', 'scale_id')
    def _compute_result(self):
        for rec in self:
            rec.total = sum(rec.line_ids.mapped('points'))
            rec.band_id = rec.scale_id.band_for(rec.total) if rec.scale_id else False

    @api.onchange('scale_id')
    def _onchange_scale_id(self):
        self.line_ids = [(5, 0, 0)] + [
            (0, 0, {'item_id': item.id}) for item in self.scale_id.item_ids]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if not rec.line_ids and rec.scale_id.item_ids:
                rec.line_ids = [(0, 0, {'item_id': item.id}) for item in rec.scale_id.item_ids]
        return records

    def write(self, vals):
        # A completed assessment is part of the legal record: locked.
        if any(rec.state == 'done' for rec in self) and set(vals) - {'family_visible'}:
            raise UserError(_('A completed assessment cannot be modified. Record a new assessment instead.'))
        return super().write(vals)

    def unlink(self):
        if any(rec.state == 'done' for rec in self):
            raise UserError(_('A completed assessment cannot be deleted.'))
        return super().unlink()

    def action_confirm(self):
        for rec in self:
            missing = rec.line_ids.filtered(lambda l: not l.option_id)
            if missing or not rec.line_ids:
                raise UserError(_('Answer every item before completing the assessment.'))
        self.write({'state': 'done'})


class PeartResidentAssessmentLine(models.Model):
    _name = 'peart.resident.assessment.line'
    _description = 'Resident Assessment Answer'
    _order = 'assessment_id, item_sequence, id'

    assessment_id = fields.Many2one('peart.resident.assessment', required=True, ondelete='cascade')
    item_id = fields.Many2one('peart.scale.item', required=True)
    item_sequence = fields.Integer(related='item_id.sequence', store=True)
    option_id = fields.Many2one('peart.scale.option', domain="[('item_id', '=', item_id)]")
    points = fields.Integer(related='option_id.points', store=True)

    @api.constrains('item_id', 'option_id')
    def _check_option(self):
        for line in self:
            if line.option_id and line.option_id.item_id != line.item_id:
                raise ValidationError(_('The selected answer does not belong to this item.'))

    def _check_unlocked(self):
        if any(line.assessment_id.state == 'done' for line in self):
            raise UserError(_('A completed assessment cannot be modified.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            assessment = self.env['peart.resident.assessment'].browse(vals.get('assessment_id'))
            if assessment.state == 'done':
                raise UserError(_('A completed assessment cannot be modified.'))
        return super().create(vals_list)

    def write(self, vals):
        self._check_unlocked()
        return super().write(vals)

    def unlink(self):
        self._check_unlocked()
        return super().unlink()
