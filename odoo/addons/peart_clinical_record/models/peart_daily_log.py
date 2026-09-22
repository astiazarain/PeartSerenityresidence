from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

# Vital-sign ranges that raise a flag on the shift log. These are common adult
# thresholds and MUST be reviewed by the clinical lead before go-live.
VITAL_LIMITS = {
    # field: (low, high, label, unit) - flagged if value < low or value > high
    'bp_systolic': (90, 159, 'Systolic BP', 'mmHg'),
    'bp_diastolic': (50, 99, 'Diastolic BP', 'mmHg'),
    'heart_rate': (50, 110, 'Heart rate', 'bpm'),
    'resp_rate': (10, 24, 'Respiratory rate', '/min'),
    'temperature': (35.5, 37.9, 'Temperature', '°C'),
    'spo2': (92, 100, 'SpO2', '%'),
    'glucose': (70, 250, 'Glucose', 'mg/dL'),
    'pain_score': (0, 6, 'Pain', '/10'),
}


def current_shift(env):
    """(date, 'day'|'night') for now, in the company's timezone.

    Day 07:00-19:00, night 19:00-07:00. A night shift belongs to the date on
    which it started, so 02:00 counts as the previous date's night shift.
    """
    now = fields.Datetime.context_timestamp(env['res.users'].with_context(
        tz=env.company.partner_id.tz or 'America/Jamaica'), fields.Datetime.now())
    if 7 <= now.hour < 19:
        return now.date(), 'day'
    if now.hour >= 19:
        return now.date(), 'night'
    return fields.Date.subtract(now.date(), days=1), 'night'


class PeartDailyLog(models.Model):
    _name = 'peart.daily.log'
    _description = 'Resident Shift Log'
    _inherit = ['mail.thread']
    _order = 'date desc, shift desc, resident_id'

    resident_id = fields.Many2one('peart.resident', required=True, ondelete='cascade', index=True)
    date = fields.Date(required=True, default=lambda s: current_shift(s.env)[0], index=True)
    shift = fields.Selection(
        [('day', 'Day (07:00-19:00)'), ('night', 'Night (19:00-07:00)')],
        required=True, default=lambda s: current_shift(s.env)[1])
    author_id = fields.Many2one('res.users', string='Recorded by', default=lambda s: s.env.user, readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('closed', 'Closed')], default='draft', tracking=True)
    name = fields.Char(compute='_compute_name')

    # Vital signs
    bp_systolic = fields.Integer(string='Systolic BP')
    bp_diastolic = fields.Integer(string='Diastolic BP')
    heart_rate = fields.Integer()
    resp_rate = fields.Integer(string='Respiratory rate')
    temperature = fields.Float(string='Temperature (°C)', digits=(4, 1))
    spo2 = fields.Integer(string='SpO2 (%)')
    glucose = fields.Integer(string='Glucose (mg/dL)')
    weight = fields.Float(string='Weight (kg)', digits=(5, 1))
    pain_score = fields.Integer(string='Pain (0-10)', default=-1, help='-1 = not assessed')

    # Care
    intake_pct = fields.Selection(
        [('0', '0%'), ('25', '25%'), ('50', '50%'), ('75', '75%'), ('100', '100%')], string='Meals eaten')
    fluids_ml = fields.Integer(string='Fluids (ml)')
    hygiene = fields.Selection(
        [('full', 'Completed'), ('partial', 'Partial'), ('refused', 'Refused')])
    incontinence_episodes = fields.Integer()
    bowel_movements = fields.Integer()
    mobility = fields.Selection(
        [('independent', 'Independent'), ('assisted', 'Assisted'), ('bed', 'Bed / chair-bound')])
    repositioned = fields.Boolean(string='Repositioned as per plan')
    sleep = fields.Selection([('good', 'Slept well'), ('fair', 'Restless'), ('poor', 'Poor / awake')])
    mood = fields.Selection([
        ('cheerful', 'Cheerful'), ('calm', 'Calm'), ('anxious', 'Anxious'), ('agitated', 'Agitated'),
        ('sad', 'Sad'), ('withdrawn', 'Withdrawn'), ('confused', 'Confused')])
    activities = fields.Char()
    visitors = fields.Char()

    notes = fields.Text(string='Internal notes', help='Staff only - never shown to the family.')
    family_note = fields.Text(string='Note for the family', help='Plain-language summary the family can read.')
    family_visible = fields.Boolean(
        string='Share with family', default=True,
        help='When the log is closed, the family sees the vitals, care summary and the family note. '
             'Internal notes are never shared.')

    alert_flags = fields.Char(compute='_compute_alerts', store=True)
    has_alert = fields.Boolean(compute='_compute_alerts', store=True)
    addendum_ids = fields.One2many('peart.daily.log.addendum', 'log_id')

    _resident_shift_uniq = models.Constraint(
        'unique(resident_id, date, shift)', 'There is already a log for this resident and shift.')

    @api.depends('resident_id', 'date', 'shift')
    def _compute_name(self):
        for rec in self:
            rec.name = '%s - %s %s' % (rec.resident_id.name or '', rec.date or '', rec.shift or '')

    @api.depends(*VITAL_LIMITS)
    def _compute_alerts(self):
        for rec in self:
            flags = []
            for fname, (low, high, label, unit) in VITAL_LIMITS.items():
                value = rec[fname]
                if fname == 'pain_score':
                    if value < 0:
                        continue
                elif not value:
                    continue
                if value < low or value > high:
                    flags.append('%s %s%s' % (label, value, unit))
            rec.alert_flags = '; '.join(flags)
            rec.has_alert = bool(flags)

    @api.constrains('pain_score', 'spo2', 'bp_systolic', 'bp_diastolic', 'heart_rate', 'temperature')
    def _check_ranges(self):
        for rec in self:
            if rec.pain_score > 10 or rec.pain_score < -1:
                raise ValidationError(_('Pain score must be between 0 and 10.'))
            if not 0 <= rec.spo2 <= 100:
                raise ValidationError(_('SpO2 must be between 0 and 100.'))
            for fname in ('bp_systolic', 'bp_diastolic', 'heart_rate', 'temperature'):
                if rec[fname] < 0:
                    raise ValidationError(_('Vital signs cannot be negative.'))

    def write(self, vals):
        if any(rec.state == 'closed' for rec in self) and set(vals) - {'family_visible'}:
            raise UserError(_('A closed log cannot be modified. Add an addendum instead.'))
        return super().write(vals)

    def unlink(self):
        if any(rec.state == 'closed' for rec in self):
            raise UserError(_('A closed log cannot be deleted.'))
        return super().unlink()

    def action_close(self):
        recorded = ('bp_systolic', 'heart_rate', 'temperature', 'spo2', 'intake_pct', 'notes', 'family_note')
        for rec in self:
            if not any(rec[f] for f in recorded):
                raise UserError(_('Record at least one observation for %s before closing.', rec.resident_id.name))
        self.write({'state': 'closed'})
        for rec in self.filtered('has_alert'):
            rec.resident_id.message_post(
                body=_('Shift log %(shift)s %(date)s flagged: %(flags)s',
                       shift=rec.shift, date=rec.date, flags=rec.alert_flags),
                subtype_xmlid='mail.mt_note')

    def action_ask_aria(self):
        self.ensure_one()
        return self.env['peart.clinical.assistant.wizard'].action_open_for_resident(self.resident_id.id)

    def action_draft_family_note(self):
        self.ensure_one()
        return self.env['peart.family.note.draft.wizard'].action_open_for_daily_log(self.id)

    def action_request_family_visible(self):
        self.ensure_one()
        preview = _('Mark visible to family: shift log of %(resident)s (%(date)s %(shift)s)',
                    resident=self.resident_id.name, date=self.date, shift=self.shift)
        self.env['peart.clinical.action.request'].request(
            'family_visible', self.resident_id.id, preview, {'model_key': 'daily_log', 'record_id': self.id})

    @api.model
    def action_generate_current_shift(self):
        """Create an empty draft log for every resident in residence for the
        current shift (idempotent), then open them for quick entry."""
        date, shift = current_shift(self.env)
        residents = self.env['peart.resident'].search([('state', '=', 'active')])
        existing = self.search([('date', '=', date), ('shift', '=', shift)]).resident_id
        self.create([
            {'resident_id': r.id, 'date': date, 'shift': shift} for r in residents - existing])
        action = self.env['ir.actions.act_window']._for_xml_id('peart_clinical_record.peart_daily_log_action')
        action['domain'] = [('date', '=', date), ('shift', '=', shift)]
        action['context'] = {'default_date': date, 'default_shift': shift}
        action['name'] = _('Shift Log - %(date)s %(shift)s', date=date, shift=shift)
        return action


class PeartDailyLogAddendum(models.Model):
    _name = 'peart.daily.log.addendum'
    _description = 'Shift Log Addendum'
    _order = 'create_date'

    log_id = fields.Many2one('peart.daily.log', required=True, ondelete='cascade')
    text = fields.Text(required=True)
    author_id = fields.Many2one('res.users', default=lambda s: s.env.user, readonly=True)
    create_date = fields.Datetime(readonly=True)


class PeartResident(models.Model):
    _inherit = 'peart.resident'

    daily_log_ids = fields.One2many('peart.daily.log', 'resident_id')
