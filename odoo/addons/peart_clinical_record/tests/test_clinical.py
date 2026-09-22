from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestClinical(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)

        def staff(login, group):
            return Users.create({
                'name': login, 'login': login,
                'group_ids': [(6, 0, [cls.env.ref('peart_clinical_record.' + group).id])],
            })
        cls.doctor = staff('doc@test.com', 'group_clinical_doctor')
        cls.nurse = staff('nurse@test.com', 'group_clinical_nurse')
        cls.admin_user = staff('adm@test.com', 'group_clinical_admin')
        cls.ceo = staff('ceo@test.com', 'group_clinical_ceo')
        cls.resident = cls.env['peart.resident'].create(
            {'partner_id': cls.env['res.partner'].create({'name': 'Resident X'}).id})

    def _scale(self, code):
        return self.env['peart.scale'].search([('code', '=', code)])

    def _assess(self, code, pick):
        """pick(item) -> option record"""
        scale = self._scale(code)
        return self.env['peart.resident.assessment'].create({
            'resident_id': self.resident.id, 'scale_id': scale.id,
            'line_ids': [(0, 0, {'item_id': i.id, 'option_id': pick(i).id}) for i in scale.item_ids],
        })

    def _top(self, item):
        return item.option_ids.sorted('points')[-1]

    def _bottom(self, item):
        return item.option_ids.sorted('points')[0]

    # ---- scoring ----
    def test_scale_max_scores(self):
        expected = {'barthel': 100, 'katz': 6, 'morse': 125, 'norton': 20, 'spmsq': 10, 'gds15': 15}
        for code, mx in expected.items():
            self.assertEqual(self._scale(code).max_score, mx, code)

    def test_barthel_independent_and_dependent(self):
        self.assertEqual(self._assess('barthel', self._top).band_id.name, 'Independent')
        a = self._assess('barthel', self._bottom)
        self.assertEqual(a.total, 0)
        self.assertEqual(a.severity, 'danger')

    def test_morse_high_risk(self):
        a = self._assess('morse', self._top)
        self.assertEqual(a.total, 125)
        self.assertEqual(a.band_id.name, 'High risk')

    def test_norton_low_and_high_risk(self):
        self.assertEqual(self._assess('norton', self._top).severity, 'ok')
        a = self._assess('norton', self._bottom)
        self.assertEqual(a.total, 5)
        self.assertEqual(a.severity, 'danger')

    def test_gds_reverse_scored_items(self):
        # Answering "Yes" to everything must NOT be 15: items 1,5,7,11,13 score on "No".
        a = self._assess('gds15', lambda i: i.option_ids.filtered(lambda o: o.name == 'Yes'))
        self.assertEqual(a.total, 10)
        self.assertEqual(a.band_id.name, 'Moderate depression')

    def test_spmsq_errors(self):
        def pick(item):
            wrong = item.sequence <= 60  # first six questions answered wrongly
            return item.option_ids.filtered(lambda o: o.name == ('Error' if wrong else 'Correct'))
        a = self._assess('spmsq', pick)
        self.assertEqual(a.total, 6)
        self.assertEqual(a.band_id.name, 'Moderate impairment')

    def test_onchange_builds_lines(self):
        form = self.env['peart.resident.assessment'].new({'scale_id': self._scale('katz').id})
        form._onchange_scale_id()
        self.assertEqual(len(form.line_ids), 6)

    # ---- locking ----
    def test_incomplete_assessment_cannot_complete(self):
        scale = self._scale('katz')
        a = self.env['peart.resident.assessment'].create(
            {'resident_id': self.resident.id, 'scale_id': scale.id})
        with self.assertRaises(UserError):
            a.action_confirm()

    def test_completed_assessment_is_locked(self):
        a = self._assess('katz', self._top)
        a.action_confirm()
        with self.assertRaises(UserError):
            a.notes = 'edit'
        with self.assertRaises(UserError):
            a.line_ids[0].option_id = a.line_ids[0].item_id.option_ids[0]
        with self.assertRaises(UserError):
            a.unlink()

    # ---- roles ----
    def _medication(self, user):
        return self.env['peart.resident.medication'].with_user(user).create(
            {'resident_id': self.resident.id, 'name': 'Metformin', 'dose': '500 mg'})

    def test_only_doctor_prescribes(self):
        med = self._medication(self.doctor)
        self.assertEqual(med.prescriber_id, self.doctor)
        with self.assertRaises(AccessError):
            self._medication(self.nurse)

    def test_nurse_can_add_allergy_but_not_diagnosis(self):
        self.env['peart.resident.allergy'].with_user(self.nurse).create(
            {'resident_id': self.resident.id, 'name': 'Penicillin', 'severity': 'severe'})
        self.assertIn('Penicillin', self.resident.with_user(self.nurse).allergy_summary)
        with self.assertRaises(AccessError):
            self.env['peart.resident.condition'].with_user(self.nurse).create(
                {'resident_id': self.resident.id, 'name': 'Diabetes'})

    def test_ceo_is_read_only(self):
        self._medication(self.doctor)
        self.assertEqual(len(self.env['peart.resident.medication'].with_user(self.ceo).search([])), 1)
        with self.assertRaises(AccessError):
            self.env['peart.resident.allergy'].with_user(self.ceo).create(
                {'resident_id': self.resident.id, 'name': 'Nuts'})

    def test_administrator_has_no_clinical_access(self):
        self.env['peart.resident.condition'].with_user(self.doctor).create(
            {'resident_id': self.resident.id, 'name': 'Hypertension'})
        for model in ('peart.resident.condition', 'peart.resident.medication',
                      'peart.resident.assessment', 'peart.resident.intake'):
            with self.assertRaises(AccessError, msg=model):
                self.env[model].with_user(self.admin_user).search([])

    def test_administrator_documents_only_non_clinical(self):
        Doc = self.env['peart.resident.document']
        vals = {'resident_id': self.resident.id, 'file': 'ZmFrZQ==', 'name': 'x'}
        Doc.with_user(self.doctor).create(dict(vals, category='lab'))
        Doc.with_user(self.doctor).create(dict(vals, category='insurance'))
        seen = Doc.with_user(self.admin_user).search([]).mapped('category')
        self.assertEqual(seen, ['insurance'])
        self.assertEqual(len(Doc.with_user(self.nurse).search([])), 2)

    def test_stop_medication(self):
        med = self._medication(self.doctor)
        med.with_user(self.doctor).action_stop()
        self.assertEqual(med.state, 'stopped')
        self.assertTrue(med.end_date)

    def test_care_plan_default_review_date(self):
        plan = self.env['peart.resident.care.plan'].with_user(self.nurse).create({
            'resident_id': self.resident.id, 'name': 'Fall prevention',
            'goal': 'No falls', 'intervention': 'Hourly rounds'})
        self.assertTrue(plan.review_date)

    def test_single_intake_per_resident(self):
        self.resident.action_open_intake()
        self.resident.action_open_intake()
        self.assertEqual(len(self.resident.intake_ids), 1)
