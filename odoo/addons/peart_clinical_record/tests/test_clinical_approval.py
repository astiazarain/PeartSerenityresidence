from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestClinicalApproval(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)

        def user(role):
            return Users.create({'name': role, 'login': role + '@appr.test', 'group_ids': [
                (6, 0, [cls.env.ref('peart_clinical_record.group_clinical_' + role).id])]})
        cls.doctor = user('doctor')
        cls.doctor2 = Users.create({'name': 'doctor2', 'login': 'doctor2@appr.test', 'group_ids': [
            (6, 0, [cls.env.ref('peart_clinical_record.group_clinical_doctor').id])]})  # second doctor, for approve-not-self tests
        cls.nurse = user('nurse')
        cls.ceo = user('ceo')
        cls.admin_user = user('admin')
        cls.resident = cls.env['peart.resident'].create(
            {'partner_id': cls.env['res.partner'].create({'name': 'Approval Resident'}).id})
        cls.log = cls.env['peart.daily.log'].create(
            {'resident_id': cls.resident.id, 'shift': 'day', 'notes': 'ok'})
        cls.incident = cls.env['peart.incident'].create(
            {'resident_id': cls.resident.id, 'kind': 'other', 'description': 'x'})

    # ---- ai.clinical.actions: only reachable through an approved request ----
    def test_actions_require_clinical_role(self):
        with self.assertRaises(AccessError):
            self.env['ai.clinical.actions'].with_user(self.admin_user).create_nursing_task(
                self.resident.id, 'Check wound')

    def test_mark_family_visible_rejects_unknown_model(self):
        with self.assertRaises(UserError):
            self.env['ai.clinical.actions'].with_user(self.doctor).mark_family_visible('bogus', self.log.id)

    def test_nursing_task_needs_a_title(self):
        with self.assertRaises(UserError):
            self.env['ai.clinical.actions'].with_user(self.nurse).create_nursing_task(self.resident.id, '  ')

    # ---- request -> approve -> execute (nursing task) ----
    def test_nursing_task_request_then_approve_creates_activity(self):
        Request = self.env['peart.clinical.action.request'].with_user(self.nurse)
        req = Request.request('nursing_task', self.resident.id, 'Check wound tomorrow',
                              {'resident_id': self.resident.id, 'title': 'Check wound'})
        self.assertEqual(req.state, 'pending')
        self.assertFalse(self.resident.sudo().activity_ids)
        req.with_user(self.doctor).action_approve()
        self.assertEqual(req.state, 'executed')
        self.assertTrue(self.resident.sudo().activity_ids.filtered(lambda a: a.summary == 'Check wound'))

    def test_nursing_task_broadcasts_to_all_nurses_when_no_assignee(self):
        other_nurse = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'n2', 'login': 'n2@appr.test',
            'group_ids': [(6, 0, [self.env.ref('peart_clinical_record.group_clinical_nurse').id])]})
        req = self.env['peart.clinical.action.request'].with_user(self.nurse).request(
            'nursing_task', self.resident.id, 'x', {'resident_id': self.resident.id, 'title': 'Round'})
        req.with_user(self.doctor).action_approve()
        assignees = self.resident.sudo().activity_ids.filtered(lambda a: a.summary == 'Round').user_id
        self.assertIn(self.nurse, assignees)
        self.assertIn(other_nurse, assignees)

    def test_nursing_task_specific_assignee(self):
        req = self.env['peart.clinical.action.request'].with_user(self.doctor).request(
            'nursing_task', self.resident.id, 'x',
            {'resident_id': self.resident.id, 'title': 'Vitals', 'assignee_login': self.nurse.login})
        req.with_user(self.doctor2).action_approve()
        activity = self.resident.sudo().activity_ids.filtered(lambda a: a.summary == 'Vitals')
        self.assertEqual(activity.user_id, self.nurse)

    def test_unknown_assignee_login_errors_on_execution(self):
        req = self.env['peart.clinical.action.request'].with_user(self.doctor).request(
            'nursing_task', self.resident.id, 'x',
            {'resident_id': self.resident.id, 'title': 'x', 'assignee_login': 'ghost@nowhere.test'})
        # Not self.assertRaises(): Odoo's version wraps the block in its own
        # savepoint and rolls it back once the expected exception fires - it
        # would silently undo the state='error' write we're checking for.
        try:
            req.with_user(self.doctor2).action_approve()
            self.fail('Expected a UserError')
        except UserError as exc:
            self.assertIn('not an active nurse', str(exc))
        self.assertEqual(req.state, 'error')

    # ---- request -> approve -> execute (family visibility) ----
    def test_family_visible_request_then_approve(self):
        unshared_log = self.env['peart.daily.log'].create(
            {'resident_id': self.resident.id, 'shift': 'night', 'notes': 'ok', 'family_visible': False})
        req = self.env['peart.clinical.action.request'].with_user(self.nurse).request(
            'family_visible', self.resident.id, 'x', {'model_key': 'daily_log', 'record_id': unshared_log.id})
        self.assertFalse(unshared_log.family_visible)
        req.with_user(self.doctor).action_approve()
        self.assertTrue(unshared_log.family_visible)
        self.assertEqual(req.state, 'executed')

    def test_family_visible_incident(self):
        req = self.env['peart.clinical.action.request'].with_user(self.doctor).request(
            'family_visible', self.resident.id, 'x', {'model_key': 'incident', 'record_id': self.incident.id})
        req.with_user(self.doctor2).action_approve()
        self.assertTrue(self.incident.family_visible)

    # ---- who can request/approve/reject ----
    def test_ceo_cannot_request(self):
        # CEO is read-only everywhere in this system; clinical action
        # requests are no exception.
        with self.assertRaises(AccessError):
            self.env['peart.clinical.action.request'].with_user(self.ceo).request(
                'nursing_task', self.resident.id, 'x', {'resident_id': self.resident.id, 'title': 'x'})

    def test_ceo_cannot_approve_a_request(self):
        req = self.env['peart.clinical.action.request'].with_user(self.doctor).request(
            'nursing_task', self.resident.id, 'x', {'resident_id': self.resident.id, 'title': 'x'})
        with self.assertRaises(UserError):
            req.with_user(self.ceo).action_approve()

    def test_nurse_cannot_approve(self):
        req = self.env['peart.clinical.action.request'].with_user(self.doctor).request(
            'nursing_task', self.resident.id, 'x', {'resident_id': self.resident.id, 'title': 'x'})
        with self.assertRaises(UserError):
            req.with_user(self.nurse).action_approve()
        self.assertEqual(req.state, 'pending')

    def test_requester_cannot_self_approve(self):
        req = self.env['peart.clinical.action.request'].with_user(self.doctor).request(
            'nursing_task', self.resident.id, 'x', {'resident_id': self.resident.id, 'title': 'x'})
        with self.assertRaises(UserError):
            req.with_user(self.doctor).action_approve()
        self.assertEqual(req.state, 'pending')

    def test_requester_can_reject_own_request(self):
        req = self.env['peart.clinical.action.request'].with_user(self.nurse).request(
            'nursing_task', self.resident.id, 'x', {'resident_id': self.resident.id, 'title': 'x'})
        req.with_user(self.nurse).action_reject()
        self.assertEqual(req.state, 'rejected')

    def test_nurse_cannot_reject_someone_elses_request(self):
        req = self.env['peart.clinical.action.request'].with_user(self.doctor).request(
            'nursing_task', self.resident.id, 'x', {'resident_id': self.resident.id, 'title': 'x'})
        with self.assertRaises(UserError):
            req.with_user(self.nurse).action_reject()

    def test_rejected_request_is_never_executed(self):
        unshared_log = self.env['peart.daily.log'].create(
            {'resident_id': self.resident.id, 'shift': 'night', 'notes': 'ok', 'family_visible': False})
        req = self.env['peart.clinical.action.request'].with_user(self.nurse).request(
            'family_visible', self.resident.id, 'x', {'model_key': 'daily_log', 'record_id': unshared_log.id})
        req.with_user(self.doctor).action_reject()
        self.assertFalse(unshared_log.family_visible)
        self.assertEqual(req.state, 'rejected')

    def test_cannot_approve_twice(self):
        req = self.env['peart.clinical.action.request'].with_user(self.nurse).request(
            'nursing_task', self.resident.id, 'x', {'resident_id': self.resident.id, 'title': 'x'})
        req.with_user(self.doctor).action_approve()
        with self.assertRaises(UserError):
            req.with_user(self.doctor2).action_approve()

    def test_admin_cannot_request_or_approve(self):
        with self.assertRaises(AccessError):
            self.env['peart.clinical.action.request'].with_user(self.admin_user).request(
                'nursing_task', self.resident.id, 'x', {'resident_id': self.resident.id, 'title': 'x'})

    # ---- notifications & ACL ----
    def test_doctors_are_notified_on_new_request(self):
        self.env['peart.clinical.action.request'].with_user(self.nurse).request(
            'nursing_task', self.resident.id, 'Check wound', {'resident_id': self.resident.id, 'title': 'x'})
        notif = self.env['mail.notification'].search(
            [('mail_message_id.model', '=', 'peart.clinical.action.request')])
        self.assertIn(self.doctor.partner_id, notif.mapped('res_partner_id'))
        self.assertIn(self.doctor2.partner_id, notif.mapped('res_partner_id'))
        self.assertNotIn(self.nurse.partner_id, notif.mapped('res_partner_id'))

    def test_nurse_has_write_but_cannot_actually_approve(self):
        # Nurse needs write() ACL to reject her OWN request; the real gate
        # against approving/rejecting someone else's is enforced in Python
        # (action_approve/action_reject), not by the ACL.
        Request = self.env['peart.clinical.action.request']
        self.assertTrue(Request.with_user(self.nurse).has_access('write'))
        self.assertTrue(Request.with_user(self.nurse).has_access('create'))
        self.assertTrue(Request.with_user(self.nurse).has_access('read'))

    def test_ceo_is_read_only_on_requests(self):
        Request = self.env['peart.clinical.action.request']
        self.assertTrue(Request.with_user(self.ceo).has_access('read'))
        self.assertFalse(Request.with_user(self.ceo).has_access('create'))
        self.assertFalse(Request.with_user(self.ceo).has_access('write'))

    # ---- catalog wiring ----
    def test_tools_are_registered_as_risk_2(self):
        for xmlid in ('tool_crear_tarea_enfermeria', 'tool_marcar_visible_familia'):
            tool = self.env.ref('peart_clinical_record.' + xmlid)
            self.assertEqual(tool.risk_level, '2')
            self.assertTrue(tool.requires_approval)
            self.assertEqual(tool.target_model, 'ai.clinical.actions')

    # ---- wizards ----
    def test_nursing_task_wizard_creates_pending_request(self):
        wizard = self.env['peart.nursing.task.wizard'].with_user(self.nurse).create(
            {'resident_id': self.resident.id, 'title': 'Check dressing', 'assignee_id': self.nurse.id})
        wizard.action_request()
        req = self.env['peart.clinical.action.request'].search(
            [('resident_id', '=', self.resident.id), ('kind', '=', 'nursing_task')])
        self.assertEqual(req.state, 'pending')
        self.assertEqual(req.get_payload()['assignee_login'], self.nurse.login)

    def test_nursing_task_wizard_requires_title(self):
        wizard = self.env['peart.nursing.task.wizard'].with_user(self.nurse).create(
            {'resident_id': self.resident.id, 'title': '   '})
        with self.assertRaises(UserError):
            wizard.action_request()

    def test_request_family_visible_button_on_daily_log(self):
        self.log.with_user(self.nurse).action_request_family_visible()
        req = self.env['peart.clinical.action.request'].search(
            [('kind', '=', 'family_visible'), ('resident_id', '=', self.resident.id)])
        self.assertEqual(req.state, 'pending')
        self.assertEqual(req.get_payload(), {'model_key': 'daily_log', 'record_id': self.log.id})

    def test_request_family_visible_button_on_incident(self):
        self.incident.with_user(self.doctor).action_request_family_visible()
        req = self.env['peart.clinical.action.request'].search(
            [('kind', '=', 'family_visible'), ('resident_id', '=', self.resident.id)])
        self.assertEqual(req.get_payload(), {'model_key': 'incident', 'record_id': self.incident.id})
