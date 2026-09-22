from unittest.mock import patch

from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

SECRET_STAFF_NOTE = 'INTERNAL-ONLY-Marcia is difficult with staff'


@tagged('post_install', '-at_install')
class TestFamilyNoteDraft(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)
        cls.nurse = Users.create({'name': 'n', 'login': 'n@draft.test', 'group_ids': [
            (6, 0, [cls.env.ref('peart_clinical_record.group_clinical_nurse').id])]})
        cls.admin_user = Users.create({'name': 'a', 'login': 'a@draft.test', 'group_ids': [
            (6, 0, [cls.env.ref('peart_clinical_record.group_clinical_admin').id])]})
        cls.resident = cls.env['peart.resident'].create({
            'partner_id': cls.env['res.partner'].create({'name': 'Draft Resident'}).id,
            'preferred_lang': 'es'})
        cls.log = cls.env['peart.daily.log'].create({
            'resident_id': cls.resident.id, 'shift': 'day', 'notes': SECRET_STAFF_NOTE})
        cls.incident = cls.env['peart.incident'].create({
            'resident_id': cls.resident.id, 'kind': 'fall', 'description': SECRET_STAFF_NOTE})
        icp = cls.env['ir.config_parameter'].sudo()
        provider = cls.env['ai.provider.config'].sudo().search([], limit=1)
        icp.set_param('peart_clinical_record.staff_ai_provider_id', provider.id if provider else False)

    def _fake(self, reply):
        fake = type('P', (), {})()
        fake.with_context = lambda **kw: fake
        fake.generate_content = lambda prompt, system_prompt=None: (
            self.calls.append((prompt, system_prompt)) or reply)
        return fake

    def setUp(self):
        super().setUp()
        self.calls = []

    def _draft(self, user, kind, record_id, reply='Had a good day, resting well.'):
        with patch.object(type(self.env['ai.clinical.assistant']), '_provider', return_value=self._fake(reply)):
            return self.env['ai.clinical.assistant'].with_user(user).draft_family_text(kind, record_id)

    # ---- core behaviour ----
    def test_draft_never_saves_by_itself(self):
        self._draft(self.nurse, 'daily_log', self.log.id)
        self.assertFalse(self.log.family_note)

    def test_draft_uses_resident_preferred_language(self):
        self._draft(self.nurse, 'daily_log', self.log.id)
        system = self.calls[0][1]
        self.assertIn('Escribe en español', system)

    def test_source_note_never_leaves_this_resident_scope(self):
        out = self._draft(self.nurse, 'daily_log', self.log.id, reply='Tuvo un buen día.')
        self.assertEqual(out['draft'], 'Tuvo un buen día.')
        system = self.calls[0][1]
        self.assertIn(SECRET_STAFF_NOTE, system)  # it's the source text, expected
        self.assertNotIn('Draft Resident', system)  # but the real name never is

    def test_empty_source_short_circuits_without_calling_provider(self):
        empty_log = self.env['peart.daily.log'].create({'resident_id': self.resident.id, 'shift': 'night'})
        with patch.object(type(self.env['ai.clinical.assistant']), '_provider', return_value=self._fake('x')):
            out = self.env['ai.clinical.assistant'].with_user(self.nurse).draft_family_text(
                'daily_log', empty_log.id)
        self.assertEqual(out['route'], 'empty')
        self.assertFalse(self.calls)

    def test_incident_source(self):
        out = self._draft(self.nurse, 'incident', self.incident.id, reply='Sufrió una caída leve, sin lesiones.')
        self.assertEqual(out['route'], 'answered')
        self.assertIn('caída', out['draft'])

    def test_unknown_source_kind_rejected(self):
        with self.assertRaises(UserError):
            self.env['ai.clinical.assistant'].with_user(self.nurse).draft_family_text('bogus', self.log.id)

    def test_administrator_cannot_draft(self):
        with self.assertRaises(AccessError):
            self._draft(self.admin_user, 'daily_log', self.log.id)

    def test_no_provider_configured(self):
        self.env['ir.config_parameter'].sudo().set_param('peart_clinical_record.staff_ai_provider_id', False)
        out = self.env['ai.clinical.assistant'].with_user(self.nurse).draft_family_text('daily_log', self.log.id)
        self.assertEqual(out['route'], 'not_configured')

    # ---- wizard: draft -> edit -> save flow ----
    def test_wizard_generate_then_save_writes_target_field(self):
        with patch.object(type(self.env['ai.clinical.assistant']), '_provider', return_value=self._fake('Great day.')):
            wizard = self.env['peart.family.note.draft.wizard'].with_user(self.nurse).create(
                {'source_kind': 'daily_log', 'daily_log_id': self.log.id})
            wizard.action_generate()
        self.assertEqual(wizard.draft, 'Great day.')
        self.assertFalse(self.log.family_note)  # still not saved
        wizard.draft = 'Great day, edited by the nurse.'   # human edits it
        wizard.action_save()
        self.assertEqual(self.log.family_note, 'Great day, edited by the nurse.')

    def test_wizard_save_without_draft_raises(self):
        wizard = self.env['peart.family.note.draft.wizard'].with_user(self.nurse).create(
            {'source_kind': 'daily_log', 'daily_log_id': self.log.id})
        with self.assertRaises(UserError):
            wizard.action_save()

    def test_wizard_incident_save_writes_family_summary(self):
        with patch.object(type(self.env['ai.clinical.assistant']), '_provider', return_value=self._fake('Fall, no injury.')):
            wizard = self.env['peart.family.note.draft.wizard'].with_user(self.nurse).create(
                {'source_kind': 'incident', 'incident_id': self.incident.id})
            wizard.action_generate()
        wizard.action_save()
        self.assertEqual(self.incident.family_summary, 'Fall, no injury.')
        self.assertFalse(self.incident.description == self.incident.family_summary)

    def test_wizard_never_writes_the_internal_note_itself(self):
        with patch.object(type(self.env['ai.clinical.assistant']), '_provider', return_value=self._fake('ok')):
            wizard = self.env['peart.family.note.draft.wizard'].with_user(self.nurse).create(
                {'source_kind': 'daily_log', 'daily_log_id': self.log.id})
            wizard.action_generate()
            wizard.action_save()
        self.assertEqual(self.log.notes, SECRET_STAFF_NOTE)
