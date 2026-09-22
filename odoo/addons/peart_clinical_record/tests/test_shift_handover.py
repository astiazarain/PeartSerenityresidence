from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestShiftHandover(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)
        cls.nurse = Users.create({'name': 'n', 'login': 'n@ho.test', 'group_ids': [
            (6, 0, [cls.env.ref('peart_clinical_record.group_clinical_nurse').id])]})
        cls.doctor = Users.create({'name': 'd', 'login': 'd@ho.test', 'group_ids': [
            (6, 0, [cls.env.ref('peart_clinical_record.group_clinical_doctor').id])]})
        cls.resident = cls.env['peart.resident'].create(
            {'partner_id': cls.env['res.partner'].create({'name': 'Handover Resident'}).id})

    def test_generate_counts_overdue_dose(self):
        med = self.env['peart.resident.medication'].with_user(self.doctor).create(
            {'resident_id': self.resident.id, 'name': 'X', 'dose': '1', 'frequency': 'prn'})
        self.env['peart.medication.administration'].create({
            'medication_id': med.id, 'scheduled_datetime': fields.Datetime.now() - timedelta(minutes=90)})
        Handover = self.env['peart.shift.handover']
        date, shift = Handover._due_shift(Handover._clock())
        record = Handover._generate(date, shift)
        self.assertEqual(record.overdue_doses_count, 1)
        self.assertIn('Handover Resident', record.overdue_doses_detail)

    def test_generate_is_idempotent(self):
        Handover = self.env['peart.shift.handover']
        date, shift = Handover._due_shift(Handover._clock())
        first = Handover._generate(date, shift)
        second = Handover._generate(date, shift)
        self.assertEqual(first, second)
        self.assertEqual(Handover.search_count([('date', '=', date), ('shift', '=', shift)]), 1)

    def test_open_incident_and_unclosed_log_are_counted(self):
        self.env['peart.incident'].create(
            {'resident_id': self.resident.id, 'kind': 'fall', 'description': 'x'})
        Handover = self.env['peart.shift.handover']
        date, shift = Handover._due_shift(Handover._clock())
        self.env['peart.daily.log'].create({'resident_id': self.resident.id, 'date': date, 'shift': shift})
        record = Handover._generate(date, shift)
        self.assertEqual(record.open_incidents_count, 1)
        self.assertGreaterEqual(record.unclosed_logs_count, 1)

    def test_notify_reaches_clinical_staff_inbox(self):
        Handover = self.env['peart.shift.handover']
        date, shift = Handover._due_shift(Handover._clock())
        record = Handover._generate(date, shift)
        notif = self.env['mail.notification'].search([('mail_message_id.res_id', '=', record.id),
                                                       ('mail_message_id.model', '=', 'peart.shift.handover')])
        self.assertIn(self.nurse.partner_id, notif.mapped('res_partner_id'))
        self.assertIn(self.doctor.partner_id, notif.mapped('res_partner_id'))
        # no PHI in the notification body itself
        body = notif.mapped('mail_message_id.body')[0]
        self.assertNotIn('Handover Resident', body)

    def test_cron_generates_current_due_shift(self):
        Handover = self.env['peart.shift.handover']
        record = Handover._cron_generate()
        date, shift = Handover._due_shift(Handover._clock())
        self.assertEqual((record.date, record.shift), (date, shift))

    def test_manual_generate_button(self):
        record = self.env['peart.shift.handover'].with_user(self.doctor).action_generate_now()
        self.assertTrue(record)

    def test_only_doctor_can_create_manually_others_read_only(self):
        Handover = self.env['peart.shift.handover']
        self.assertFalse(Handover.with_user(self.nurse).has_access('create'))
        self.assertTrue(Handover.with_user(self.nurse).has_access('read'))
