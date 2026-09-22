import re
from datetime import datetime, time, timedelta

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

# Default administration times when the order does not list any.
DEFAULT_TIMES = {
    'od': ['08:00'],
    'bid': ['08:00', '20:00'],
    'tid': ['08:00', '14:00', '20:00'],
    'qid': ['06:00', '12:00', '18:00', '22:00'],
    'q8h': ['06:00', '14:00', '22:00'],
    'weekly': ['08:00'],
}
TIME_RE = re.compile(r'^([01]?\d|2[0-3]):([0-5]\d)$')
FINAL_STATES = ('given', 'refused', 'omitted', 'held', 'cancelled')
NEEDS_REASON = ('refused', 'omitted', 'held')


class PeartMedicationAdministration(models.Model):
    _name = 'peart.medication.administration'
    _description = 'Medication Administration Record (MAR) entry'
    _order = 'scheduled_datetime, resident_id'

    medication_id = fields.Many2one(
        'peart.resident.medication', required=True, ondelete='cascade', index=True)
    resident_id = fields.Many2one(related='medication_id.resident_id', store=True, index=True)
    drug = fields.Char(related='medication_id.name')
    dose = fields.Char(related='medication_id.dose')
    route = fields.Selection(related='medication_id.route')
    scheduled_datetime = fields.Datetime(required=True, default=fields.Datetime.now, index=True)
    state = fields.Selection([
        ('pending', 'Pending'), ('given', 'Given'), ('refused', 'Refused'),
        ('omitted', 'Omitted'), ('held', 'Held'), ('cancelled', 'Cancelled'),
    ], default='pending', required=True, index=True)
    given_at = fields.Datetime(readonly=True)
    given_by_id = fields.Many2one('res.users', string='Recorded by', readonly=True)
    reason = fields.Char(help='Required when the dose is refused, omitted or held (or the PRN indication).')
    notes = fields.Text()
    is_late = fields.Boolean(compute='_compute_is_late')

    _dose_uniq = models.Constraint(
        'unique(medication_id, scheduled_datetime)', 'This dose is already scheduled.')

    @api.depends('resident_id.name', 'medication_id.name', 'scheduled_datetime')
    def _compute_display_name(self):
        for rec in self:
            when = fields.Datetime.context_timestamp(rec, rec.scheduled_datetime).strftime('%d/%m %H:%M') \
                if rec.scheduled_datetime else ''
            rec.display_name = '%s - %s %s' % (rec.resident_id.name or '', rec.medication_id.name or '', when)

    @api.depends('state', 'scheduled_datetime')
    def _compute_is_late(self):
        limit = fields.Datetime.now() - timedelta(minutes=60)
        for rec in self:
            rec.is_late = rec.state == 'pending' and rec.scheduled_datetime < limit

    @api.constrains('state', 'reason')
    def _check_reason(self):
        for rec in self:
            if rec.state in NEEDS_REASON and not rec.reason:
                raise ValidationError(_('Enter the reason the dose was %s.', rec.state))

    def write(self, vals):
        locked = self.filtered(lambda r: r.state in FINAL_STATES)
        if locked and set(vals) - {'notes'}:
            raise UserError(_('A recorded dose cannot be changed.'))
        return super().write(vals)

    def unlink(self):
        if any(rec.state in ('given', 'refused', 'omitted', 'held') for rec in self):
            raise UserError(_('A recorded dose cannot be deleted.'))
        return super().unlink()

    def _record(self, state):
        for rec in self:
            if rec.state != 'pending':
                raise UserError(_('This dose has already been recorded.'))
        self.write({'state': state, 'given_at': fields.Datetime.now(), 'given_by_id': self.env.uid})

    def action_give(self):
        self._record('given')

    def action_refuse(self):
        self._record('refused')

    def action_omit(self):
        self._record('omitted')

    def action_hold(self):
        self._record('held')


class PeartResidentMedication(models.Model):
    _inherit = 'peart.resident.medication'

    administration_ids = fields.One2many('peart.medication.administration', 'medication_id')

    @api.constrains('schedule_times')
    def _check_schedule_times(self):
        for rec in self.filtered('schedule_times'):
            for token in re.split(r'[,\s;]+', rec.schedule_times.strip()):
                if token and not TIME_RE.match(token):
                    raise ValidationError(_('Invalid time "%s". Use 24-hour HH:MM, e.g. 08:00, 20:00.', token))

    def _times_list(self):
        self.ensure_one()
        if self.schedule_times and self.schedule_times.strip():
            tokens = [t for t in re.split(r'[,\s;]+', self.schedule_times.strip()) if t]
        else:
            tokens = DEFAULT_TIMES.get(self.frequency, [])
        out = []
        for token in tokens:
            match = TIME_RE.match(token)
            if match:
                out.append(time(int(match.group(1)), int(match.group(2))))
        return sorted(set(out))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        today = fields.Date.context_today(records)
        records._generate_administrations(today, fields.Date.add(today, days=1), only_future=True)
        return records

    def action_stop(self):
        res = super().action_stop()
        self.env['peart.medication.administration'].sudo().search([
            ('medication_id', 'in', self.ids), ('state', '=', 'pending'),
            ('scheduled_datetime', '>=', fields.Datetime.now()),
        ]).write({'state': 'cancelled'})
        return res

    def _generate_administrations(self, date_from, date_to, only_future=False):
        """Create the pending MAR entries for active orders between two local
        dates (inclusive). Idempotent thanks to the unique constraint check."""
        Admin = self.env['peart.medication.administration'].sudo()
        tz = pytz.timezone(self.env.company.partner_id.tz or 'America/Jamaica')
        now = fields.Datetime.now()
        vals_list = []
        for med in self.filtered(lambda m: m.state == 'active' and m.frequency != 'prn'
                                 and m.resident_id.state == 'active'):
            existing = set(Admin.search([('medication_id', '=', med.id)]).mapped('scheduled_datetime'))
            day = date_from
            while day <= date_to:
                in_window = day >= med.start_date and (not med.end_date or day <= med.end_date)
                weekly_ok = med.frequency != 'weekly' or (day - med.start_date).days % 7 == 0
                if in_window and weekly_ok:
                    for at in med._times_list():
                        local = tz.localize(datetime.combine(day, at))
                        utc = local.astimezone(pytz.utc).replace(tzinfo=None)
                        if utc in existing or (only_future and utc < now):
                            continue
                        vals_list.append({'medication_id': med.id, 'scheduled_datetime': utc})
                day += timedelta(days=1)
        if vals_list:
            Admin.create(vals_list)
        return len(vals_list)

    @api.model
    def _cron_generate_administrations(self):
        today = fields.Date.context_today(self)
        meds = self.search([('state', '=', 'active')])
        return meds._generate_administrations(today, fields.Date.add(today, days=1))

    @api.model
    def action_generate_mar(self):
        count = self._cron_generate_administrations()
        return {
            'type': 'ir.actions.client', 'tag': 'display_notification',
            'params': {'title': _('Medication round'), 'type': 'success', 'sticky': False,
                       'message': _('%s new doses scheduled.', count),
                       'next': {'type': 'ir.actions.act_window_close'}},
        }
