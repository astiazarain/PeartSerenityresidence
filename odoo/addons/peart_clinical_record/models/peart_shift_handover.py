"""Shift handover digest: a rule-based, point-in-time snapshot generated
twice a day (06:45 and 18:45 Jamaica time - see data/handover_cron_data.xml),
one per (date, shift). Deliberately NOT an LLM narrative: it is what the
outgoing shift needs to hand to the incoming one, and it must be exact, fast
and reproducible - see the phase-4 decision (rules first, LLM optional
later). It complements, but does not replace, the HUD's live attention
queue: this one is a timestamped record kept for continuity and audit
("what was known at 06:45"), the HUD queue is always current.

No resident data is ever pushed outside Odoo: the Inbox notification sent on
generation carries no PHI, only a pointer to open this record.
"""
from datetime import datetime, time, timedelta

import pytz

from odoo import _, api, fields, models

CLINICAL_GROUPS = ('peart_clinical_record.group_clinical_doctor,'
                   'peart_clinical_record.group_clinical_nurse,'
                   'peart_clinical_record.group_clinical_ceo')


class PeartShiftHandover(models.Model):
    _name = 'peart.shift.handover'
    _description = 'Shift Handover Digest'
    _inherit = ['mail.thread']
    _order = 'date desc, shift desc'

    # Not stored: a stored compute would freeze the shift's selection label
    # (e.g. "Day"/"Día") in whatever language the record happened to be
    # created under, instead of the viewer's own language.
    name = fields.Char(compute='_compute_name')
    date = fields.Date(required=True, index=True)
    shift = fields.Selection(
        [('day', 'Day (07:00-19:00)'), ('night', 'Night (19:00-07:00)')], required=True)
    generated_at = fields.Datetime(default=fields.Datetime.now, readonly=True)

    overdue_doses_count = fields.Integer(readonly=True)
    overdue_doses_detail = fields.Text(readonly=True)
    unclosed_logs_count = fields.Integer(readonly=True)
    unclosed_logs_detail = fields.Text(readonly=True)
    open_incidents_count = fields.Integer(readonly=True)
    open_incidents_detail = fields.Text(readonly=True)
    vital_alerts_count = fields.Integer(readonly=True)
    vital_alerts_detail = fields.Text(readonly=True)
    family_questions_count = fields.Integer(readonly=True)
    family_questions_detail = fields.Text(readonly=True)

    _date_shift_uniq = models.Constraint(
        'unique(date, shift)', 'A handover already exists for this date and shift.')

    @api.depends('date', 'shift')
    def _compute_name(self):
        for rec in self:
            rec.name = '%s - %s' % (rec.date or '', dict(self._fields['shift'].selection).get(rec.shift, ''))

    # ------------------------------------------------------------------
    # Time (Jamaica-local; no DST, so a fixed UTC offset is safe - see
    # data/handover_cron_data.xml)
    # ------------------------------------------------------------------

    @api.model
    def _clock(self):
        tz = pytz.timezone(self.env.company.partner_id.tz or 'America/Jamaica')
        return {'tz': tz, 'local': pytz.utc.localize(fields.Datetime.now()).astimezone(tz)}

    @api.model
    def _due_shift(self, clock):
        """The shift that just ended, for a handover generated a bit after
        07:00/19:00. Mirrors ops_hud_clinical's _res_due_shift; kept as an
        independent copy here since peart_clinical_record must not depend on
        the HUD module (dependency runs the other way)."""
        local, today = clock['local'], clock['local'].date()
        if local.time() >= time(12, 0):
            return today, 'day'
        return today - timedelta(days=1), 'night'

    def _bounds(self, clock, date):
        start = clock['tz'].localize(datetime.combine(date, time.min))
        return (start.astimezone(pytz.utc).replace(tzinfo=None),
                (start + timedelta(days=1)).astimezone(pytz.utc).replace(tzinfo=None))

    # ------------------------------------------------------------------
    # Generation (plain facts, no interpretation)
    # ------------------------------------------------------------------

    def _lines(self, items, fmt):
        return '\n'.join(fmt(i) for i in items) if items else _('None.')

    @api.model
    def _generate(self, date, shift):
        existing = self.search([('date', '=', date), ('shift', '=', shift)], limit=1)
        if existing:
            return existing
        clock = self._clock()
        now = fields.Datetime.now()

        overdue = self.env['peart.medication.administration'].search([
            ('state', '=', 'pending'), ('scheduled_datetime', '<', now - timedelta(minutes=60))],
            order='scheduled_datetime')
        logs = self.env['peart.daily.log'].search([('date', '=', date), ('shift', '=', shift)])
        unclosed = logs.filtered(lambda l: l.state == 'draft')
        expected = self.env['peart.resident'].search([('state', '=', 'active')]) - logs.resident_id
        incidents = self.env['peart.incident'].search([('state', '!=', 'closed')], order='occurred_at desc')
        since = now - timedelta(hours=24)
        alerts = self.env['peart.daily.log'].search(
            [('has_alert', '=', True), ('create_date', '>=', since)], order='date desc')
        act_type = self.env.ref('peart_clinical_record.mail_activity_type_family_question', raise_if_not_found=False)
        questions = self.env['mail.activity'].sudo().search(
            [('activity_type_id', '=', act_type.id)]) if act_type else self.env['mail.activity']

        vals = {
            'date': date, 'shift': shift,
            'overdue_doses_count': len(overdue),
            'overdue_doses_detail': self._lines(overdue, lambda d: '- %s: %s %s (%d min late)' % (
                d.resident_id.name, d.drug, d.dose or '',
                int((now - d.scheduled_datetime).total_seconds() // 60))),
            'unclosed_logs_count': len(unclosed) + len(expected),
            'unclosed_logs_detail': self._lines(
                [(l.resident_id.name, 'draft') for l in unclosed]
                + [(r.name, 'no log at all') for r in expected],
                lambda item: '- %s: %s' % item),
            'open_incidents_count': len(incidents),
            'open_incidents_detail': self._lines(incidents, lambda i: '- %s (%s, %s): %s' % (
                i.resident_id.name, i.kind, i.severity, i.name)),
            'vital_alerts_count': len(alerts),
            'vital_alerts_detail': self._lines(alerts, lambda l: '- %s (%s %s): %s' % (
                l.resident_id.name, l.date, l.shift, l.alert_flags)),
            'family_questions_count': len(questions),
            'family_questions_detail': self._lines(questions, lambda a: '- %s: %s' % (
                a.res_id and self.env['peart.resident'].browse(a.res_id).name or '?', a.summary or '')),
        }
        record = self.sudo().create(vals)
        record._notify()
        return record

    def _notify(self):
        self.ensure_one()
        users = self.env['res.users'].sudo().search([
            '|', ('group_ids', 'in', self.env.ref('peart_clinical_record.group_clinical_doctor').id),
            ('group_ids', 'in', self.env.ref('peart_clinical_record.group_clinical_nurse').id)])
        if not users:
            return
        # No resident data in the notification itself - only a pointer.
        self.message_notify(
            partner_ids=users.partner_id.ids,
            subject=_('Shift handover ready: %s', self.name),
            body=_('The %s shift handover is ready in the Control Center / Residents.', self.name),
            subtype_xmlid='mail.mt_note',
        )

    @api.model
    def _cron_generate(self):
        clock = self._clock()
        date, shift = self._due_shift(clock)
        return self._generate(date, shift)

    def action_generate_now(self):
        """Manual trigger (Doctor), e.g. if the scheduled job was missed."""
        return self._cron_generate()
