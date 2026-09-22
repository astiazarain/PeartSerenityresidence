from odoo import fields
from odoo.tests import TransactionCase, tagged

D, N, A, C = 'doctor', 'nurse', 'admin', 'ceo'
ALL = {D, N, A, C}
CLINICAL = {D, N, C}

# model -> (who may read, who may create). Written by hand on purpose: if a
# permission changes, this table must change with it (reviewable, not derived).
MATRIX = {
    'peart.resident': (ALL, {A}),
    'peart.resident.family.link': (ALL, {A}),
    'peart.resident.consent': (ALL, {A, N}),
    'peart.resident.intake': (CLINICAL, {D, N}),
    'peart.resident.allergy': (CLINICAL, {D, N}),
    'peart.resident.condition': (CLINICAL, {D}),
    'peart.resident.medication': (CLINICAL, {D}),
    'peart.resident.contact': (ALL, {D, N, A}),
    'peart.resident.care.plan': (CLINICAL, {D, N}),
    'peart.resident.document': (ALL, {D, N, A}),
    'peart.resident.assessment': (CLINICAL, {D, N}),
    'peart.daily.log': (CLINICAL, {D, N}),
    'peart.medication.administration': (CLINICAL, {D, N}),
    'peart.incident': (CLINICAL, {D, N}),
    'peart.scale': (ALL, {D}),
    'peart.family.access.log': ({C, A}, set()),
}


@tagged('post_install', '-at_install')
class TestSecurityMatrix(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)

        def user(login, group):
            groups = [cls.env.ref(group).id] if group else []
            return Users.create({'name': login, 'login': login + '@sec.test', 'group_ids': [(6, 0, groups)]})
        cls.users = {r: user(r, 'peart_clinical_record.group_clinical_' + r) for r in ALL}
        cls.plain = user('plain', None)
        cls.family = Users.create({'name': 'fam', 'login': 'fam@sec.test',
                                   'group_ids': [(6, 0, cls.env.ref('base.group_portal').ids)]})
        cls.resident = cls.env['peart.resident'].create(
            {'partner_id': cls.env['res.partner'].create({'name': 'Sec Resident'}).id})

    def test_role_matrix(self):
        for model, (readers, creators) in MATRIX.items():
            for role, user in self.users.items():
                m = self.env[model].with_user(user)
                self.assertEqual(m.has_access('read'), role in readers, '%s read by %s' % (model, role))
                self.assertEqual(m.has_access('create'), role in creators, '%s create by %s' % (model, role))

    def test_nobody_but_doctor_and_admin_deletes_sensitive_records(self):
        for model in ('peart.incident', 'peart.daily.log', 'peart.medication.administration',
                      'peart.resident.assessment', 'peart.resident', 'peart.resident.consent'):
            for role, user in self.users.items():
                self.assertFalse(self.env[model].with_user(user).has_access('unlink'), '%s delete by %s' % (model, role))

    def test_portal_and_unroled_users_have_no_orm_access(self):
        for model in MATRIX:
            for who in (self.family, self.plain):
                m = self.env[model].with_user(who)
                for op in ('read', 'write', 'create', 'unlink'):
                    self.assertFalse(m.has_access(op), '%s %s by %s' % (model, op, who.name))

    def test_staff_view_is_audited_once_per_window(self):
        nurse = self.users[N]
        Log = self.env['peart.family.access.log'].sudo()
        domain = [('user_id', '=', nurse.id), ('action', '=', 'staff_view'), ('resident_id', '=', self.resident.id)]
        self.resident.with_user(nurse).web_read({'name': {}})
        self.resident.with_user(nurse).web_read({'name': {}})
        self.assertEqual(Log.search_count(domain), 1)

    def test_pdf_print_is_audited(self):
        nurse = self.users[N]
        self.env['ir.actions.report'].with_user(nurse)._render_qweb_pdf(
            'peart_clinical_record.action_report_resident_record', [self.resident.id])
        log = self.env['peart.family.access.log'].sudo().search(
            [('user_id', '=', nurse.id), ('action', '=', 'report')])
        self.assertEqual(log.resident_id, self.resident)


@tagged('post_install', '-at_install')
class TestReports(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)
        cls.nurse = Users.create({'name': 'rn', 'login': 'rn@rep.test', 'group_ids': [
            (6, 0, [cls.env.ref('peart_clinical_record.group_clinical_nurse').id])]})
        cls.admin_user = Users.create({'name': 'ra', 'login': 'ra@rep.test', 'group_ids': [
            (6, 0, [cls.env.ref('peart_clinical_record.group_clinical_admin').id])]})
        cls.resident = cls.env['peart.resident'].create(
            {'partner_id': cls.env['res.partner'].create({'name': 'Report Resident'}).id})
        cls.env['peart.resident.allergy'].create({'resident_id': cls.resident.id, 'name': 'Penicillin'})
        cls.env['peart.resident.condition'].create({'resident_id': cls.resident.id, 'name': 'Hypertension'})
        cls.env['peart.resident.medication'].create(
            {'resident_id': cls.resident.id, 'name': 'Amlodipine', 'dose': '5 mg'})
        cls.log = cls.env['peart.daily.log'].create({
            'resident_id': cls.resident.id, 'shift': 'day', 'spo2': 85, 'notes': 'Slept in chair'})

    def _html(self, xmlid, ids, user):
        html, _fmt = self.env['ir.actions.report'].with_user(user)._render_qweb_html(xmlid, ids)
        return html.decode()

    def test_resident_record_content(self):
        html = self._html('peart_clinical_record.action_report_resident_record', self.resident.ids, self.nurse)
        for expected in ('Report Resident', 'Penicillin', 'Hypertension', 'Amlodipine', 'CONFIDENTIAL', 'Slept in chair'):
            self.assertIn(expected, html)

    def test_administrator_cannot_print_clinical_record(self):
        with self.assertRaises(Exception):
            self._html('peart_clinical_record.action_report_resident_record', self.resident.ids, self.admin_user)

    def test_shift_summary_flags_out_of_range(self):
        html = self._html('peart_clinical_record.action_report_shift_summary', self.log.ids, self.nurse)
        self.assertIn('Report Resident', html)
        self.assertIn('SpO2', html)
        self.assertIn('o_peart_row_alert', html)

    def test_report_actions_are_restricted_to_clinical_groups(self):
        groups = self.env.ref('peart_clinical_record.action_report_resident_record').group_ids
        self.assertNotIn(self.env.ref('peart_clinical_record.group_clinical_admin'), groups)
        self.assertEqual(len(groups), 3)


@tagged('post_install', '-at_install')
class TestViewDomains(TransactionCase):
    """View domains and filters are evaluated in the BROWSER by Odoo's small
    Python interpreter, not on the server, so loading a view proves nothing
    about them. That interpreter lacks parts of `datetime` (a filter using
    datetime.time.min crashed the Medication Round screen). Stick to the
    expressions Odoo core itself uses in filters."""

    FORBIDDEN = ('datetime.time', '.combine(', 'datetime.date(', 'timedelta(', 'import ')

    def test_search_views_only_use_client_safe_python(self):
        views = self.env['ir.ui.view'].sudo().search([
            ('model', 'like', 'peart.'), ('type', 'in', ('search', 'list', 'form'))])
        self.assertTrue(views)
        for view in views:
            if not view.get_external_id().get(view.id, '').startswith('peart_clinical_record.'):
                continue
            for token in self.FORBIDDEN:
                self.assertNotIn(token, view.arch_db, '%s uses %r in a client-evaluated domain' % (view.name, token))
