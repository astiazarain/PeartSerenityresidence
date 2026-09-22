from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCare(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)

        def staff(login, group):
            return Users.create({
                'name': login, 'login': login,
                'group_ids': [(6, 0, [cls.env.ref('peart_clinical_record.' + group).id])]})
        cls.doctor = staff('doc3@test.com', 'group_clinical_doctor')
        cls.nurse = staff('nurse3@test.com', 'group_clinical_nurse')
        cls.admin_user = staff('adm3@test.com', 'group_clinical_admin')
        cls.ceo = staff('ceo3@test.com', 'group_clinical_ceo')
        cls.resident = cls.env['peart.resident'].create(
            {'partner_id': cls.env['res.partner'].create({'name': 'Resident Y'}).id})

    def _med(self, **kw):
        vals = {'resident_id': self.resident.id, 'name': 'Metformin', 'dose': '500 mg',
                'frequency': 'bid', 'start_date': fields.Date.today() - timedelta(days=1)}
        vals.update(kw)
        return self.env['peart.resident.medication'].with_user(self.doctor).create(vals)

    def _log(self, **kw):
        vals = {'resident_id': self.resident.id, 'date': fields.Date.today(), 'shift': 'day'}
        vals.update(kw)
        return self.env['peart.daily.log'].with_user(self.nurse).create(vals)

    # ---- shift log ----
    def test_one_log_per_resident_and_shift(self):
        self._log()
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self._log()
        self._log(shift='night')

    def test_vital_flags(self):
        log = self._log(bp_systolic=85, spo2=88, temperature=38.6, heart_rate=72)
        self.assertTrue(log.has_alert)
        for word in ('Systolic BP', 'SpO2', 'Temperature'):
            self.assertIn(word, log.alert_flags)
        self.assertNotIn('Heart rate', log.alert_flags)
        self.assertFalse(self._log(shift='night', bp_systolic=120, spo2=97).has_alert)

    def test_pain_not_assessed_is_not_a_flag(self):
        self.assertFalse(self._log(heart_rate=70).has_alert)
        self.assertTrue(self._log(shift='night', pain_score=8).has_alert)

    def test_cannot_close_empty_log(self):
        with self.assertRaises(UserError):
            self._log().action_close()

    def test_closed_log_locked_and_addendum(self):
        log = self._log(heart_rate=70)
        log.action_close()
        with self.assertRaises(UserError):
            log.heart_rate = 80
        with self.assertRaises(UserError):
            log.unlink()
        self.env['peart.daily.log.addendum'].with_user(self.nurse).create(
            {'log_id': log.id, 'text': 'Correction: HR was 78'})
        self.assertEqual(len(log.addendum_ids), 1)

    def test_closing_flagged_log_notes_resident(self):
        count = len(self.resident.message_ids)
        log = self._log(spo2=85)
        log.action_close()
        self.assertGreater(len(self.resident.message_ids), count)

    def test_generate_shift_logs_is_idempotent_and_skips_inactive(self):
        other = self.env['peart.resident'].create(
            {'partner_id': self.env['res.partner'].create({'name': 'Gone'}).id, 'state': 'discharged'})
        Log = self.env['peart.daily.log'].with_user(self.nurse)
        Log.action_generate_current_shift()
        Log.action_generate_current_shift()
        logs = self.env['peart.daily.log'].search([('resident_id', 'in', (self.resident | other).ids)])
        self.assertEqual(logs.resident_id, self.resident)
        self.assertEqual(len(logs), 1)

    # ---- MAR ----
    def _doses(self, med):
        return self.env['peart.medication.administration'].search([('medication_id', '=', med.id)])

    def _fresh_doses(self, med, day):
        """Drop doses auto-created on order creation, then generate for `day`."""
        self._doses(med).unlink()
        med._generate_administrations(day, day)
        return self._doses(med)

    def test_generation_from_frequency_and_times(self):
        day = fields.Date.today()
        self.assertEqual(len(self._fresh_doses(self._med(frequency='od'), day)), 1)
        self.assertEqual(len(self._fresh_doses(self._med(name='B', frequency='bid'), day)), 2)
        self.assertEqual(len(self._fresh_doses(self._med(name='T', frequency='tid'), day)), 3)
        self.assertEqual(len(self._fresh_doses(self._med(name='Q', frequency='q8h'), day)), 3)
        custom = self._med(name='Insulin', schedule_times='07:30, 12:00, 17:30, 21:00')
        self.assertEqual(len(self._fresh_doses(custom, day)), 4)

    def test_generation_is_idempotent(self):
        med = self._med()
        day = fields.Date.today()
        first = len(self._fresh_doses(med, day))
        self.assertEqual(first, 2)
        med._generate_administrations(day, day)
        self.assertEqual(len(self._doses(med)), first)

    def test_timezone_is_jamaica(self):
        med = self._med(frequency='od', schedule_times='08:00', start_date=fields.Date.today())
        self.env['peart.medication.administration'].search([('medication_id', '=', med.id)]).unlink()
        day = fields.Date.today()
        med._generate_administrations(day, day)
        dose = self._doses(med)
        self.assertEqual(dose.scheduled_datetime.hour, 13)  # 08:00 Jamaica (UTC-5) = 13:00 UTC
        self.assertEqual(dose.scheduled_datetime.minute, 0)

    def test_prn_and_weekly(self):
        prn = self._med(name='Paracetamol', frequency='prn')
        day = fields.Date.today()
        prn._generate_administrations(day, day)
        self.assertFalse(self._doses(prn))
        weekly = self._med(name='Alendronate', frequency='weekly', start_date=day - timedelta(days=3))
        self.env['peart.medication.administration'].search([('medication_id', '=', weekly.id)]).unlink()
        weekly._generate_administrations(day, day + timedelta(days=6))
        self.assertEqual(len(self._doses(weekly)), 1)

    def test_invalid_time_rejected(self):
        with self.assertRaises(ValidationError):
            self._med(schedule_times='8am')

    def test_no_doses_for_hospitalized_resident(self):
        self.resident.state = 'hospitalized'
        med = self._med()
        day = fields.Date.today()
        med._generate_administrations(day, day)
        self.assertFalse(self._doses(med))

    def test_give_and_lock(self):
        med = self._med()
        dose = self.env['peart.medication.administration'].with_user(self.nurse).create(
            {'medication_id': med.id, 'scheduled_datetime': fields.Datetime.now() + timedelta(days=30)})
        dose.action_give()
        self.assertEqual(dose.state, 'given')
        self.assertEqual(dose.given_by_id, self.nurse)
        with self.assertRaises(UserError):
            dose.state = 'pending'
        with self.assertRaises(UserError):
            dose.action_give()
        with self.assertRaises(UserError):
            dose.unlink()

    def test_refusal_requires_reason(self):
        med = self._med()
        dose = self.env['peart.medication.administration'].with_user(self.nurse).create(
            {'medication_id': med.id, 'scheduled_datetime': fields.Datetime.now() + timedelta(days=31)})
        with self.assertRaises(ValidationError):
            dose.action_refuse()
        dose.reason = 'Resident spat it out'
        dose.action_refuse()
        self.assertEqual(dose.state, 'refused')

    def test_overdue_flag(self):
        med = self._med()
        dose = self.env['peart.medication.administration'].with_user(self.nurse).create(
            {'medication_id': med.id, 'scheduled_datetime': fields.Datetime.now() - timedelta(hours=2)})
        self.assertTrue(dose.is_late)

    def test_stopping_cancels_future_pending_doses_only(self):
        med = self._med()
        Admin = self.env['peart.medication.administration']
        past = Admin.create({'medication_id': med.id, 'scheduled_datetime': fields.Datetime.now() - timedelta(days=5)})
        future = Admin.create({'medication_id': med.id, 'scheduled_datetime': fields.Datetime.now() + timedelta(days=5)})
        med.with_user(self.doctor).action_stop()
        self.assertEqual(future.state, 'cancelled')
        self.assertEqual(past.state, 'pending')

    def test_new_order_creates_only_future_doses_today(self):
        med = self._med(start_date=fields.Date.today())
        now = fields.Datetime.now()
        self.assertTrue(all(d.scheduled_datetime >= now for d in self._doses(med)))

    # ---- incidents ----
    def _incident(self, user=None, **kw):
        vals = {'resident_id': self.resident.id, 'kind': 'fall', 'description': 'Found on floor'}
        vals.update(kw)
        return self.env['peart.incident'].with_user(user or self.nurse).create(vals)

    def test_incident_reference(self):
        self.assertTrue(self._incident().name.startswith('INC-'))

    def test_serious_incident_alerts_doctors(self):
        inc = self._incident(severity='serious')
        self.assertIn(self.doctor, inc.sudo().activity_ids.user_id)
        self.assertFalse(self._incident(severity='minor').sudo().activity_ids)

    def test_cannot_close_serious_without_notifications(self):
        inc = self._incident(severity='serious', follow_up='Monitor 24h')
        with self.assertRaises(ValidationError):
            inc.action_close()
        inc.write({'physician_notified': True})
        with self.assertRaises(ValidationError):
            inc.action_close()
        inc.write({'family_notified': True})
        inc.action_close()
        self.assertEqual(inc.state, 'closed')
        self.assertEqual(inc.closed_by_id, self.nurse)

    def test_closed_incident_locked_and_undeletable(self):
        inc = self._incident(follow_up='None needed')
        inc.action_close()
        with self.assertRaises(UserError):
            inc.description = 'changed'
        with self.assertRaises(UserError):
            inc.unlink()

    def test_incident_requires_follow_up_to_close(self):
        with self.assertRaises(ValidationError):
            self._incident().action_close()

    # ---- roles ----
    def test_admin_and_ceo_roles(self):
        self._log(heart_rate=70)
        for model in ('peart.daily.log', 'peart.medication.administration', 'peart.incident'):
            with self.assertRaises(AccessError, msg=model):
                self.env[model].with_user(self.admin_user).search([])
        self.assertEqual(len(self.env['peart.daily.log'].with_user(self.ceo).search([])), 1)
        with self.assertRaises(AccessError):
            self.env['peart.daily.log'].with_user(self.ceo).create(
                {'resident_id': self.resident.id, 'date': fields.Date.today(), 'shift': 'night'})
