import json
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

HUD = 'ops.hud.dashboard'


@tagged('post_install', '-at_install')
class TestHudResidence(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)

        def user(role):
            gid = cls.env.ref('peart_clinical_record.group_clinical_' + role).id
            return Users.create({'name': role, 'login': role + '@hud.test', 'group_ids': [(6, 0, [gid])]})
        cls.u = {r: user(r) for r in ('ceo', 'doctor', 'nurse', 'admin')}
        cls.plain = Users.create({'name': 'plain', 'login': 'plain@hud.test', 'group_ids': [(6, 0, [])]})

        Partner = cls.env['res.partner']
        cls.r1 = cls.env['peart.resident'].create({
            'partner_id': Partner.create({'name': 'Ana Secret'}).id,
            'admission_date': fields.Date.today() - timedelta(days=40), 'room': '1'})
        cls.r2 = cls.env['peart.resident'].create({
            'partner_id': Partner.create({'name': 'Beto Secret'}).id,
            'admission_date': fields.Date.today() - timedelta(days=40), 'room': '2'})
        cls.med = cls.env['peart.resident.medication'].create(
            {'resident_id': cls.r1.id, 'name': 'Zzdrug', 'dose': '5 mg', 'frequency': 'prn'})

    def make_compliant(self, resident, skip=()):
        self.env['peart.resident.intake'].create({'resident_id': resident.id})
        for kind in ('data_processing', 'treatment'):
            self.env['peart.resident.consent'].create({'resident_id': resident.id, 'kind': kind, 'signed_by': 'x'})
        for scale in self.env['peart.scale'].search([('frequency_days', '>', 0), ('code', 'not in', list(skip))]):
            a = self.env['peart.resident.assessment'].create({
                'resident_id': resident.id, 'scale_id': scale.id,
                'line_ids': [(0, 0, {'item_id': i.id, 'option_id': i.option_ids[0].id}) for i in scale.item_ids]})
            a.action_confirm()

    def data(self, role):
        return self.env[HUD].with_user(self.u[role]).get_residence_dashboard_data()

    def dose(self, minutes_ago, state='pending', resident=None):
        return self.env['peart.medication.administration'].create({
            'medication_id': self.med.id, 'state': state,
            'scheduled_datetime': fields.Datetime.now() - timedelta(minutes=minutes_ago),
            **({'reason': 'x'} if state in ('refused', 'omitted', 'held') else {})})

    # ---- who sees what ----
    def test_context_tabs_per_role(self):
        for role in self.u:
            ctx = self.env[HUD].with_user(self.u[role]).get_hud_context()
            self.assertIn('residencia', ctx['tabs'], role)
        ctx = self.env[HUD].with_user(self.plain).get_hud_context()
        self.assertNotIn('residencia', ctx['tabs'])

    def test_blocks_per_role(self):
        expected = {
            'ceo': {'meds', 'logs', 'incidents', 'compliance', 'occupancy', 'family', 'family_q',
                    'portal', 'trace', 'aria_chat', 'handover', 'approvals', 'attention'},
            'doctor': {'meds', 'logs', 'incidents', 'compliance', 'family', 'family_q',
                       'aria_chat', 'handover', 'approvals', 'attention'},
            'nurse': {'meds', 'logs', 'incidents', 'family_q', 'aria_chat', 'handover', 'attention'},
            'admin': {'occupancy', 'portal', 'attention'},
        }
        for role, blocks in expected.items():
            self.assertEqual(set(self.data(role)['allowed_blocks']), blocks, role)

    def test_user_without_role_is_refused(self):
        with self.assertRaises(AccessError):
            self.env[HUD].with_user(self.plain).get_residence_dashboard_data()

    def test_only_allowed_kpis_are_sent(self):
        self.assertEqual(set(self.data('nurse')['kpis']),
                        {'meds', 'logs', 'alerts', 'incidents', 'falls', 'family_pending', 'handover'})
        self.assertEqual(set(self.data('admin')['kpis']), {'occupancy', 'portal'})
        self.assertNotIn('trend_occupancy', self.data('nurse'))
        self.assertNotIn('trend_safety', self.data('admin'))

    def test_administrator_receives_no_clinical_data(self):
        self.dose(150)
        self.env['peart.incident'].create({'resident_id': self.r1.id, 'kind': 'fall', 'description': 'CLINICAL-TEXT', 'severity': 'serious'})
        self.env['peart.resident.condition'].create({'resident_id': self.r1.id, 'name': 'CLINICAL-DX'})
        text = json.dumps(self.data('admin'), default=str)
        for banned in ('Zzdrug', 'CLINICAL', 'fall', 'Dosis', 'Incidente'):
            self.assertNotIn(banned, text)

    # ---- medication ----
    def test_meds_thresholds(self):
        self.assertEqual(self.data('nurse')['kpis']['meds']['status'], 'ok')
        self.dose(90)
        meds = self.data('nurse')['kpis']['meds']
        self.assertEqual((meds['value'], meds['status']), (1, 'warn'))
        self.dose(100)
        self.dose(110)
        self.assertEqual(self.data('nurse')['kpis']['meds']['status'], 'danger')  # 3 overdue

    def test_meds_single_dose_over_two_hours_is_danger(self):
        self.dose(130)
        self.assertEqual(self.data('nurse')['kpis']['meds']['status'], 'danger')

    def test_recent_pending_dose_is_not_overdue(self):
        self.dose(30)
        self.assertEqual(self.data('nurse')['kpis']['meds']['value'], 0)

    def test_refused_dose_today_warns(self):
        self.dose(5, state='refused')
        meds = self.data('nurse')['kpis']['meds']
        self.assertEqual((meds['value'], meds['status']), (1, 'warn'))

    # ---- shift logs ----
    def _due(self):
        return patch.object(type(self.env[HUD]), '_res_due_shift', return_value=(fields.Date.today(), 'day'))

    def test_logs_percentage_and_status(self):
        Log = self.env['peart.daily.log']
        with self._due():
            self.assertEqual(self.data('nurse')['kpis']['logs']['status'], 'danger')  # 0/2 closed
            Log.create({'resident_id': self.r1.id, 'date': fields.Date.today(), 'shift': 'day', 'heart_rate': 70}).action_close()
            logs = self.data('nurse')['kpis']['logs']
            self.assertEqual((logs['value'], logs['display'], logs['status']), (50, '50%', 'danger'))
            Log.create({'resident_id': self.r2.id, 'date': fields.Date.today(), 'shift': 'day', 'heart_rate': 70}).action_close()
            logs = self.data('nurse')['kpis']['logs']
            self.assertEqual((logs['value'], logs['status']), (100, 'ok'))

    def test_draft_logs_and_missing_logs_appear_in_queue(self):
        self.env['peart.daily.log'].create({'resident_id': self.r1.id, 'date': fields.Date.today(), 'shift': 'day'})
        with self._due():
            rows = self.data('nurse')['attention']
        titles = [r['title'] for r in rows]
        self.assertTrue(any('Ana Secret' == t for t in titles))       # draft
        self.assertTrue(any('sin registro' in t for t in titles))     # missing

    def test_no_expected_residents_means_no_status(self):
        self.r1.state = self.r2.state = 'discharged'
        with self._due():
            self.assertEqual(self.data('nurse')['kpis']['logs']['status'], 'none')

    def test_due_shift_boundaries(self):
        import datetime as dt
        import pytz
        hud = self.env[HUD]
        tz = pytz.timezone('America/Jamaica')

        def due(hour, minute=0):
            local = tz.localize(dt.datetime(2026, 9, 21, hour, minute))
            return hud._res_due_shift({'local': local, 'today': local.date()})
        today, yesterday = dt.date(2026, 9, 21), dt.date(2026, 9, 20)
        self.assertEqual(due(20, 0), (today, 'day'))
        self.assertEqual(due(19, 59), (yesterday, 'night'))
        self.assertEqual(due(8, 0), (yesterday, 'night'))
        self.assertEqual(due(7, 59), (yesterday, 'day'))
        self.assertEqual(due(0, 30), (yesterday, 'day'))

    def test_vital_alerts_kpi(self):
        Log = self.env['peart.daily.log']
        for i, r in enumerate((self.r1, self.r2)):
            Log.create({'resident_id': r.id, 'date': fields.Date.today(), 'shift': 'day', 'spo2': 85}).action_close()
        alerts = self.data('nurse')['kpis']['alerts']
        self.assertEqual(alerts['value'], 2)
        self.assertEqual(alerts['status'], 'warn')

    # ---- incidents ----
    def test_incident_status_rules(self):
        Inc = self.env['peart.incident']
        self.assertEqual(self.data('nurse')['kpis']['incidents']['status'], 'ok')
        minor = Inc.create({'resident_id': self.r1.id, 'kind': 'other', 'description': 'x', 'severity': 'minor'})
        self.assertEqual(self.data('nurse')['kpis']['incidents']['status'], 'warn')
        mod = Inc.create({'resident_id': self.r1.id, 'kind': 'fall', 'description': 'x', 'severity': 'moderate'})
        self.assertEqual(self.data('nurse')['kpis']['incidents']['status'], 'danger')   # notices missing
        minor.write({'follow_up': 'ok'})
        mod.write({'physician_notified': True, 'family_notified': True})
        self.assertEqual(self.data('nurse')['kpis']['incidents']['status'], 'warn')

    def test_serious_open_incident_is_danger_even_if_notified(self):
        self.env['peart.incident'].create({
            'resident_id': self.r1.id, 'kind': 'injury', 'description': 'x', 'severity': 'serious',
            'physician_notified': True, 'family_notified': True})
        data = self.data('nurse')
        self.assertEqual(data['kpis']['incidents']['status'], 'danger')
        self.assertTrue(any(r['area'] == 'Incidente' and r['severity'] == 'danger' for r in data['attention']))

    def test_falls_counted_for_30_days(self):
        Inc = self.env['peart.incident']
        Inc.create({'resident_id': self.r1.id, 'kind': 'fall', 'description': 'x'})
        Inc.create({'resident_id': self.r1.id, 'kind': 'fall', 'description': 'old',
                    'occurred_at': fields.Datetime.now() - timedelta(days=45)})
        self.assertEqual(self.data('nurse')['kpis']['falls']['value'], 1)

    # ---- compliance ----
    def test_compliance_counts_overdue_items(self):
        comp = self.data('doctor')['kpis']['compliance']
        # both residents admitted 40 days ago: 6 scales never assessed, no intake, no consents
        self.assertGreater(comp['value'], 4)
        self.assertEqual(comp['status'], 'danger')
        self.assertIn('Valoraciones:', comp['hint'])

    def test_compliance_clears_when_up_to_date(self):
        for r in (self.r1, self.r2):
            self.make_compliant(r)
        comp = self.data('doctor')['kpis']['compliance']
        self.assertEqual((comp['value'], comp['status']), (0, 'ok'))

    def test_overdue_assessment_is_detected(self):
        self.make_compliant(self.r2)
        self.r2.state = 'discharged'
        self.make_compliant(self.r1, skip=('norton',))
        scale = self.env['peart.scale'].search([('code', '=', 'norton')])   # weekly
        a = self.env['peart.resident.assessment'].create({
            'resident_id': self.r1.id, 'scale_id': scale.id, 'date': fields.Datetime.now() - timedelta(days=20),
            'line_ids': [(0, 0, {'item_id': i.id, 'option_id': i.option_ids[0].id}) for i in scale.item_ids]})
        a.action_confirm()                                                    # due 13 days ago
        rows = [r for r in self.data('doctor')['attention'] if r['area'] == 'Valoración vencida']
        self.assertEqual(len(rows), 1)
        self.assertIn('NORTON', rows[0]['detail'])
        self.assertIn('Ana Secret', rows[0]['title'])
        self.assertEqual(self.data('doctor')['kpis']['compliance']['value'], 1)

    def test_assessments_are_grouped_per_resident_in_the_queue(self):
        rows = [r for r in self.data('doctor')['attention'] if r['area'] == 'Valoración vencida']
        self.assertEqual(len(rows), 2)                                   # one per resident, not 12
        self.assertIn('6 valoración', rows[0]['title'])
        self.assertGreaterEqual(self.data('doctor')['kpis']['compliance']['value'], 12)   # still counted one by one

    def test_care_plan_review_overdue(self):
        self.make_compliant(self.r1)
        self.r2.state = 'discharged'
        self.env['peart.resident.care.plan'].create({
            'resident_id': self.r1.id, 'name': 'PlanX', 'goal': 'g', 'intervention': 'i',
            'review_date': fields.Date.today() - timedelta(days=3)})
        rows = [r for r in self.data('doctor')['attention'] if r['area'] == 'Plan de cuidados']
        self.assertEqual(len(rows), 1)
        self.assertIn('PlanX', rows[0]['title'])
        self.assertEqual(self.data('doctor')['kpis']['compliance']['value'], 1)

    # ---- occupancy ----
    def test_occupancy_with_and_without_capacity(self):
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('ops_hud_clinical.bed_capacity', 0)
        occ = self.data('admin')['kpis']['occupancy']
        self.assertEqual((occ['value'], occ['display']), (2, '2'))
        icp.set_param('ops_hud_clinical.bed_capacity', 8)
        self.assertEqual(self.data('admin')['kpis']['occupancy']['display'], '2/8 (25%)')

    def test_hospitalized_still_occupies_a_bed(self):
        self.r2.state = 'hospitalized'
        self.assertEqual(self.data('admin')['kpis']['occupancy']['value'], 2)

    def test_occupancy_trend(self):
        # Use the HUD's own (Jamaica-local) "today", not the server/UTC date:
        # near midnight UTC the two can differ by a day and the assertions
        # below would flake depending on the wall-clock time of the test run.
        hud_today = self.env[HUD]._res_clock()['today']
        self.env['peart.resident'].create({
            'partner_id': self.env['res.partner'].create({'name': 'Carla'}).id,
            'admission_date': hud_today - timedelta(days=10)})
        trend = self.data('ceo')['trend_occupancy']
        self.assertEqual(len(trend['labels']), 30)
        self.assertEqual(trend['values'][0], 2)      # both were admitted 40 days ago
        self.assertEqual(trend['values'][18], 2)     # 11 days ago
        self.assertEqual(trend['values'][19], 3)     # the day Carla arrived
        self.assertEqual(trend['values'][-1], 3)

    # ---- family / ARIA ----
    def test_family_question_pending_and_aging(self):
        act_type = self.env.ref('peart_clinical_record.mail_activity_type_family_question')
        act = self.env['mail.activity'].sudo().create({
            'activity_type_id': act_type.id, 'res_model_id': self.env['ir.model']._get_id('peart.resident'),
            'res_id': self.r1.id, 'user_id': self.u['nurse'].id, 'summary': 'q'})

        def age(hours):
            self.env.flush_all()
            self.env.cr.execute('UPDATE mail_activity SET create_date=%s WHERE id=%s',
                                (fields.Datetime.now() - timedelta(hours=hours), act.id))
            self.env.invalidate_all()
            return self.data('nurse')['kpis']['family_pending']
        q = age(0)
        self.assertEqual((q['value'], q['status']), (1, 'ok'))      # just asked
        self.assertEqual(age(2)['status'], 'warn')
        self.assertEqual(age(30)['status'], 'danger')

    def test_aria_off_is_flagged_when_consent_exists_without_provider(self):
        self.env['ir.config_parameter'].sudo().set_param('peart_clinical_record.ai_provider_id', False)
        self.env['peart.resident.consent'].create({'resident_id': self.r1.id, 'kind': 'ai_assistant', 'signed_by': 'x'})
        data = self.data('doctor')
        self.assertEqual(data['kpis']['aria']['status'], 'danger')
        self.assertTrue(any(r['area'] == 'ARIA' for r in data['attention']))

    def test_portal_pending_links_listed_for_admin(self):
        fam = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Fam', 'login': 'fam@hud.test', 'group_ids': [(6, 0, self.env.ref('base.group_portal').ids)]})
        self.env['peart.resident.family.link'].create({'resident_id': self.r1.id, 'user_id': fam.id})
        data = self.data('admin')
        self.assertEqual(data['kpis']['portal']['status'], 'warn')
        self.assertTrue(any(r['area'] == 'Portal familiar' for r in data['attention']))

    # ---- queue ----
    def test_queue_sorted_by_severity_and_actions_are_valid(self):
        self.dose(150)      # danger
        self.dose(80)       # warn
        rows = self.data('nurse')['attention']
        ranks = {'danger': 3, 'warn': 2, 'info': 1}
        self.assertEqual([ranks[r['severity']] for r in rows], sorted((ranks[r['severity']] for r in rows), reverse=True))
        for row in rows:
            self.assertIn(row['severity_label'], ('URGENTE', 'ATENCIÓN', 'INFO'))
            if row['action']:
                self.assertEqual(row['action']['type'], 'ir.actions.act_window')
                self.assertIn(row['action']['res_model'], self.env)

    def test_queue_is_capped(self):
        for i in range(40):
            self.env['peart.incident'].create({'resident_id': self.r1.id, 'kind': 'other', 'description': 'x'})
        data = self.data('nurse')
        self.assertLessEqual(len(data['attention']), 25)

    def test_row_actions_open_records_the_role_can_read(self):
        self.dose(150)
        for row in self.data('nurse')['attention']:
            a = row['action']
            if a and a.get('res_id'):
                self.env[a['res_model']].with_user(self.u['nurse']).browse(a['res_id']).check_access('read')

    # ---- thresholds ----
    def test_thresholds_are_configurable(self):
        Th = self.env['ops.hud.threshold']
        Th.search([('code', '=', 'meds_overdue')]).write({'warn': 5, 'danger': 10})
        Th.search([('code', '=', 'meds_max_delay')]).write({'warn': 500, 'danger': 900})
        self.dose(90)
        self.dose(95)
        self.assertEqual(self.data('nurse')['kpis']['meds']['status'], 'ok')

    def test_only_doctor_edits_thresholds(self):
        Th = self.env['ops.hud.threshold']
        self.assertTrue(Th.with_user(self.u['doctor']).has_access('write'))
        for role in ('ceo', 'nurse', 'admin'):
            self.assertFalse(Th.with_user(self.u[role]).has_access('write'), role)
        self.assertFalse(Th.with_user(self.u['admin']).has_access('read'))

    def test_lower_is_worse_threshold_logic(self):
        Th = self.env['ops.hud.threshold']
        self.assertEqual(Th.status('logs_closed_pct', 100), 'ok')
        self.assertEqual(Th.status('logs_closed_pct', 90), 'warn')
        self.assertEqual(Th.status('logs_closed_pct', 79), 'danger')
        self.assertEqual(Th.status('unknown_code', 999), 'ok')

    # ---- safety trend ----
    def test_safety_trend_series(self):
        self.env['peart.incident'].create({'resident_id': self.r1.id, 'kind': 'fall', 'description': 'x'})
        self.dose(5, state='refused')
        trend = self.data('nurse')['trend_safety']
        self.assertEqual(len(trend['labels']), 30)
        self.assertEqual(sum(trend['incidents']), 1)
        self.assertEqual(sum(trend['not_given']), 1)

    def test_payload_is_json_serialisable(self):
        for role in self.u:
            json.dumps(self.data(role))

    def test_works_when_spanish_is_not_installed(self):
        """The HUD asks for Spanish labels, but must not break on a database
        that never installed the language (it raised 'Invalid language code')."""
        self.env['res.lang'].search([('code', '=', 'es_ES')]).write({'active': False})
        self.assertTrue(self.data('nurse')['kpis'])


    # ---- approvals block (Doctor/CEO only) ----
    def test_approvals_block_only_for_doctor_and_ceo(self):
        self.assertIn('approvals', self.data('doctor')['kpis'])
        self.assertIn('approvals', self.data('ceo')['kpis'])
        self.assertNotIn('approvals', self.data('nurse')['kpis'])
        self.assertNotIn('approvals', self.data('admin')['kpis'])

    def test_pending_approval_appears_in_queue(self):
        self.env['peart.clinical.action.request'].with_user(self.u['nurse']).request(
            'nursing_task', self.r1.id, 'Check wound', {'resident_id': self.r1.id, 'title': 'x'})
        data = self.data('doctor')
        self.assertEqual(data['kpis']['approvals']['value'], 1)
        self.assertEqual(data['kpis']['approvals']['status'], 'warn')
        self.assertTrue(any(r['area'] == 'Aprobación pendiente' for r in data['attention']))
