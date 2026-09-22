import json
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

SECRET = 'STAFF-ONLY-CONFIDENTIAL-NOTE'


@tagged('post_install', '-at_install')
class TestAriaClinical(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)

        def user(role, group=None):
            groups = [cls.env.ref('peart_clinical_record.group_clinical_' + group).id] if group else []
            return Users.create({'name': role, 'login': role + '@aria.test', 'group_ids': [(6, 0, groups)]})
        cls.doctor = user('doc', 'doctor')
        cls.nurse = user('nurse', 'nurse')
        cls.ceo = user('ceo', 'ceo')
        cls.admin_user = user('adm', 'admin')
        cls.plain = user('plain')
        cls.resident = cls.env['peart.resident'].create({
            'partner_id': cls.env['res.partner'].create({'name': 'Confidential Resident'}).id, 'room': '9'})
        cls.env['peart.resident.allergy'].create(
            {'resident_id': cls.resident.id, 'name': 'Penicillin', 'severity': 'severe'})
        cls.env['peart.incident'].create(
            {'resident_id': cls.resident.id, 'kind': 'fall', 'description': SECRET})

    def _fake(self, reply):
        fake = type('P', (), {})()
        fake.with_context = lambda **kw: fake
        fake.generate_content = lambda prompt, system_prompt=None: (
            self.calls.append((prompt, system_prompt)) or reply)
        return fake

    def setUp(self):
        super().setUp()
        self.calls = []
        icp = self.env['ir.config_parameter'].sudo()
        provider = self.env['ai.provider.config'].sudo().search([], limit=1)
        icp.set_param('peart_clinical_record.staff_ai_provider_id', provider.id if provider else False)

    def _ask(self, user, message='Any updates?', resident_id=None, reply='All fine.'):
        with patch.object(type(self.env['ai.clinical.assistant']), '_provider', return_value=self._fake(reply)):
            return self.env['ai.clinical.assistant'].with_user(user).ask(message, resident_id=resident_id)

    # ---- access ----
    def test_only_clinical_roles_may_ask(self):
        for user in (self.doctor, self.nurse, self.ceo):
            self.assertEqual(self._ask(user)['route'], 'answered')
        for user in (self.admin_user, self.plain):
            with self.assertRaises(AccessError):
                self._ask(user)

    def test_resident_scoped_question_respects_acl(self):
        # Administrator has no ACL on peart.resident.allergy/incident/etc, and
        # is denied by the role check before any of that is even reached.
        with self.assertRaises(AccessError):
            self._ask(self.admin_user, resident_id=self.resident.id)
        self.assertEqual(self._ask(self.nurse, resident_id=self.resident.id)['route'], 'answered')

    def test_requires_message(self):
        with self.assertRaises(UserError):
            self._ask(self.nurse, message='   ')

    # ---- provider ----
    def test_no_provider_configured(self):
        self.env['ir.config_parameter'].sudo().set_param('peart_clinical_record.staff_ai_provider_id', False)
        out = self.env['ai.clinical.assistant'].with_user(self.nurse).ask('Any updates?')
        self.assertEqual(out['route'], 'not_configured')
        self.assertIn('ARIA Clínica', out['reply'])

    def test_provider_failure_is_graceful(self):
        fake = type('P', (), {})()
        fake.with_context = lambda **kw: fake

        def boom(*a, **k):
            raise RuntimeError('down')
        fake.generate_content = boom
        with patch.object(type(self.env['ai.clinical.assistant']), '_provider', return_value=fake):
            out = self.env['ai.clinical.assistant'].with_user(self.nurse).ask('hi')
        self.assertEqual(out['route'], 'error')

    def test_rate_limit(self):
        for _ in range(10):
            self.assertEqual(self._ask(self.nurse)['route'], 'answered')
        self.assertEqual(self._ask(self.nurse)['route'], 'rate_limited')

    # ---- pseudonymisation ----
    def test_resident_name_never_sent_and_code_restored(self):
        self.resident.name  # ensure computed
        out = self._ask(self.nurse, resident_id=self.resident.id,
                        reply='%s has a fever.' % self.resident.code)
        prompt, system = self.calls[0]
        self.assertNotIn('Confidential Resident', system)
        self.assertIn(self.resident.code, system)
        self.assertIn('Confidential Resident (%s)' % self.resident.code, out['reply'])

    def test_operational_brief_pseudonymises_all_residents(self):
        other = self.env['peart.resident'].create(
            {'partner_id': self.env['res.partner'].create({'name': 'Other Secret Name'}).id})
        self._ask(self.nurse, reply='ok')
        system = self.calls[0][1]
        self.assertNotIn('Confidential Resident', system)
        self.assertNotIn('Other Secret Name', system)

    def test_resident_data_contains_no_confidential_free_text_leak(self):
        # allergies/incidents are summarised by field, never dump raw descriptions
        self._ask(self.nurse, resident_id=self.resident.id)
        system = self.calls[0][1]
        self.assertNotIn(SECRET, system)
        self.assertIn('Penicillin', system)

    # ---- prompt rules ----
    def test_system_prompt_forbids_prescribing_and_cites_data(self):
        self._ask(self.doctor, resident_id=self.resident.id)
        system = self.calls[0][1]
        for rule in ('never diagnose', 'starting, changing, stopping'):
            self.assertIn(rule, system)

    def test_history_is_included_and_trimmed(self):
        history = [{'role': 'user', 'content': 'q%s' % i} for i in range(20)]
        with patch.object(type(self.env['ai.clinical.assistant']), '_provider', return_value=self._fake('ok')):
            self.env['ai.clinical.assistant'].with_user(self.nurse).ask('latest', history=history)
        prompt = self.calls[0][0]
        self.assertNotIn('q0', prompt)
        self.assertIn('q19', prompt)
        self.assertTrue(prompt.endswith('Staff: latest'))

    # ---- audit ----
    def test_question_is_logged(self):
        self._ask(self.nurse, resident_id=self.resident.id, message='status?')
        log = self.env['peart.family.access.log'].search([('action', '=', 'aria_staff')])
        self.assertEqual(log.user_id, self.nurse)
        self.assertEqual(log.resident_id, self.resident)
        self.assertEqual(log.question, 'status?')

    def test_serialisable_snapshot(self):
        # both branches must be JSON-safe (dates, etc.)
        assistant = self.env['ai.clinical.assistant'].with_user(self.nurse)
        json.dumps(assistant._resident_brief(self.resident))
        brief, _map = assistant._operational_brief()
        json.dumps(brief)

    # ---- Coordinator wiring ----
    def test_tool_is_registered_and_wired_to_the_assistant(self):
        # The Coordinator's own ACL (ai.conversation, ai.agent.tool execution)
        # is a separate concern from ARIA Clínica; here we only guarantee the
        # catalog entry points at the right method, and that calling it the
        # way ai.agent.tool.execute() would (**params) works end to end.
        tool = self.env.ref('peart_clinical_record.tool_preguntar_aria_clinica')
        self.assertEqual(tool.target_model, 'ai.clinical.assistant')
        self.assertEqual(tool.target_method, 'coordinator_ask')
        self.assertEqual(tool.risk_level, '0')
        self.assertFalse(tool.requires_approval)
        with patch.object(type(self.env['ai.clinical.assistant']), '_provider', return_value=self._fake('ok')):
            out = self.env['ai.clinical.assistant'].with_user(self.nurse).coordinator_ask(
                message='Qué dosis están atrasadas', resident_id=False)
        self.assertEqual(out['route'], 'answered')

    def test_clinical_roles_can_read_the_tool_catalog(self):
        # Needed for the Skills panel / any future Coordinator wiring to show
        # something meaningful to clinical staff, without granting them
        # access to ai.conversation or other agents' data.
        for user in (self.doctor, self.nurse, self.ceo):
            self.env['ai.agent.tool'].with_user(user).search([])
        for user in (self.admin_user, self.plain):
            with self.assertRaises(AccessError):
                self.env['ai.agent.tool'].with_user(user).search([]).mapped('name')
                self.env['ai.agent.tool'].with_user(user).browse(
                    self.env.ref('peart_clinical_record.tool_preguntar_aria_clinica').id).check_access('read')

    def test_wizard_roundtrip(self):
        with patch.object(type(self.env['ai.clinical.assistant']), '_provider', return_value=self._fake('Stable.')):
            wizard = self.env['peart.clinical.assistant.wizard'].with_user(self.nurse).create(
                {'resident_id': self.resident.id, 'message': 'How is the resident?'})
            wizard.action_ask()
        self.assertEqual(wizard.reply, 'Stable.')
        self.assertEqual(wizard.route, 'answered')
        self.assertEqual(len(json.loads(wizard.history)), 2)

    def test_administrator_cannot_open_wizard_flow(self):
        with self.assertRaises(AccessError):
            self.env['peart.clinical.assistant.wizard'].with_user(self.admin_user).create(
                {'resident_id': self.resident.id, 'message': 'x'})
