import json
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

SECRET_NOTE = 'STAFF-ONLY-SECRET'
GDS_SECRET = 'GDS-HIDDEN'


@tagged('post_install', '-at_install')
class TestFamilyPortal(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)
        portal = cls.env.ref('base.group_portal')
        cls.fam_a = Users.create({'name': 'Fam A', 'login': 'pa@test.com', 'group_ids': [(6, 0, portal.ids)]})
        cls.fam_b = Users.create({'name': 'Fam B', 'login': 'pb@test.com', 'group_ids': [(6, 0, portal.ids)]})
        cls.nurse = Users.create({'name': 'N', 'login': 'pn@test.com', 'group_ids': [
            (6, 0, [cls.env.ref('peart_clinical_record.group_clinical_nurse').id])]})
        Partner = cls.env['res.partner']
        cls.res_a = cls.env['peart.resident'].create({'partner_id': Partner.create({'name': 'Resident A'}).id})
        cls.res_b = cls.env['peart.resident'].create({'partner_id': Partner.create({'name': 'Resident B'}).id})
        for res, fam in ((cls.res_a, cls.fam_a), (cls.res_b, cls.fam_b)):
            cls.env['peart.resident.consent'].create({'resident_id': res.id, 'kind': 'family_access', 'signed_by': 'x'})
            cls.env['peart.resident.family.link'].create(
                {'resident_id': res.id, 'user_id': fam.id, 'access_enabled': True})
        cls.env['peart.resident.consent'].create({'resident_id': cls.res_a.id, 'kind': 'ai_assistant', 'signed_by': 'x'})

        Log = cls.env['peart.daily.log']
        today = fields.Date.today()
        cls.shared = Log.create({
            'resident_id': cls.res_a.id, 'date': today, 'shift': 'day', 'heart_rate': 72, 'mood': 'cheerful',
            'notes': SECRET_NOTE, 'family_note': 'Had a lovely lunch.', 'spo2': 85})
        cls.shared.action_close()
        cls.hidden = Log.create({
            'resident_id': cls.res_a.id, 'date': today, 'shift': 'night', 'heart_rate': 60, 'notes': SECRET_NOTE,
            'family_note': 'NOT SHARED', 'family_visible': False})
        cls.hidden.action_close()
        cls.draft = Log.create({'resident_id': cls.res_a.id, 'date': fields.Date.subtract(today, days=1), 'shift': 'night',
                                'family_note': 'DRAFT NOTE'})
        Log.create({'resident_id': cls.res_b.id, 'date': today, 'shift': 'day', 'heart_rate': 80,
                    'family_note': 'RESIDENT B NOTE'}).action_close()

        Med = cls.env['peart.resident.medication']
        Med.create({'resident_id': cls.res_a.id, 'name': 'Shared Med', 'dose': '5 mg'})
        Med.create({'resident_id': cls.res_a.id, 'name': 'Hidden Med', 'dose': '1 mg', 'family_visible': False})
        cls.env['peart.resident.condition'].create({'resident_id': cls.res_a.id, 'name': 'Hidden Dx'})
        cls.env['peart.resident.condition'].create(
            {'resident_id': cls.res_a.id, 'name': 'Shared Dx', 'family_visible': True})
        cls.env['peart.resident.document'].create(
            {'resident_id': cls.res_a.id, 'name': 'Private report', 'file': 'ZmFrZQ=='})
        cls.env['peart.resident.document'].create(
            {'resident_id': cls.res_a.id, 'name': 'Shared report', 'file': 'ZmFrZQ==', 'family_visible': True})
        cls.env['peart.incident'].create({
            'resident_id': cls.res_a.id, 'kind': 'fall', 'description': SECRET_NOTE,
            'family_visible': True, 'family_summary': 'Slipped, no injury.'})
        cls.env['peart.incident'].create({
            'resident_id': cls.res_a.id, 'kind': 'fall', 'description': SECRET_NOTE, 'family_summary': 'unshared'})

        scale = cls.env['peart.scale'].search([('code', '=', 'gds15')])
        for shared in (False, True):
            a = cls.env['peart.resident.assessment'].create({
                'resident_id': cls.res_a.id, 'scale_id': scale.id, 'family_visible': shared,
                'line_ids': [(0, 0, {'item_id': i.id, 'option_id': i.option_ids[0].id}) for i in scale.item_ids]})
            a.action_confirm()

    def _dump(self, obj):
        return json.dumps(obj, default=str)

    # ---- isolation ----
    def test_family_only_sees_own_resident(self):
        Res = self.env['peart.resident']
        self.assertTrue(Res._portal_resident(self.fam_a, self.res_a.id))
        self.assertFalse(Res._portal_resident(self.fam_a, self.res_b.id))
        self.assertFalse(Res._portal_resident(self.fam_a, 999999))
        self.assertFalse(Res._portal_resident(self.fam_a, 'abc'))
        self.assertEqual([r['name'] for r in Res._portal_my_residents(self.fam_a)], ['Resident A'])

    def test_no_access_after_consent_revoked(self):
        self.res_b.consent_ids.filtered(lambda c: c.kind == 'family_access').action_revoke()
        self.assertFalse(self.env['peart.resident']._portal_resident(self.fam_b, self.res_b.id))

    # ---- no leaks ----
    def test_summary_leaks_nothing(self):
        out = self._dump(self.res_a.portal_summary())
        for banned in (SECRET_NOTE, 'NOT SHARED', 'Hidden Med', 'Hidden Dx', 'DRAFT NOTE',
                       'RESIDENT B NOTE', 'unshared', 'alert_flags', 'care_level', 'code_status'):
            self.assertNotIn(banned, out)
        self.assertIn('Had a lovely lunch.', out)
        self.assertIn('Shared Med', out)

    def test_timeline_only_closed_shared_logs(self):
        out = self.res_a.portal_timeline()
        self.assertEqual(out['total'], 1)
        text = self._dump(out)
        for banned in (SECRET_NOTE, 'NOT SHARED', 'DRAFT NOTE', 'RESIDENT B NOTE', 'alert'):
            self.assertNotIn(banned, text)
        self.assertEqual(out['items'][0]['vitals']['heart_rate'], 72)

    def test_record_respects_flags(self):
        rec = self.res_a.portal_record()
        text = self._dump(rec)
        self.assertEqual([c['name'] for c in rec['conditions']], ['Shared Dx'])
        self.assertNotIn('Hidden', text)
        self.assertNotIn(SECRET_NOTE, text)
        self.assertEqual(len(rec['assessments']), 1)
        self.assertEqual([i['summary'] for i in rec['incidents']], ['Slipped, no injury.'])

    def test_documents_only_shared(self):
        self.assertEqual([d['name'] for d in self.res_a.portal_documents()], ['Shared report'])

    def test_timeline_paging_is_sanitised(self):
        # negative offset -> 0, limit 0 -> 1: never an error, never negative slicing
        items = self.res_a.portal_timeline(offset=-5, limit=0)['items']
        self.assertEqual([i['id'] for i in items], [self.shared.id])
        self.assertEqual(self.res_a.portal_timeline(offset=5, limit=10)['items'], [])

    # ---- translation ----
    def test_scale_name_translates_when_lang_installed(self):
        self.env['res.lang']._activate_lang('es_ES')
        self.env['ir.module.module'].search([('name', '=', 'peart_clinical_record')])._update_translations(['es_ES'])
        es = self.res_a.portal_record('es')['assessments'][0]['scale']
        self.assertIn('Depresión', es)
        self.assertIn('Depression', self.res_a.portal_record('en')['assessments'][0]['scale'])

    # ---- ARIA ----
    def _ask(self, reply, user=None, message='How is she?', res=None):
        fake = type('P', (), {})()
        fake.with_context = lambda **kw: fake
        fake.generate_content = lambda prompt, system_prompt=None: (self.calls.append((prompt, system_prompt)) or reply)
        with patch.object(type(self.env['peart.resident']), '_aria_provider', return_value=fake):
            return (res or self.res_a).portal_ask_aria(user or self.fam_a, message, lang='en')

    def setUp(self):
        super().setUp()
        self.calls = []

    def test_aria_answers_from_scoped_data_only(self):
        out = self._ask('She had a lovely lunch.')
        self.assertEqual(out['route'], 'answered')
        prompt, system = self.calls[0]
        self.assertIn('Had a lovely lunch.', system)
        for banned in (SECRET_NOTE, 'NOT SHARED', 'RESIDENT B NOTE', 'Hidden Med', 'Resident B'):
            self.assertNotIn(banned, system)
        log = self.env['peart.family.access.log'].search([('action', '=', 'aria')])
        self.assertEqual(log.question, 'How is she?')
        self.assertEqual(log.user_id, self.fam_a)

    def test_aria_escalates_to_nurses(self):
        out = self._ask('NECESITA_ENFERMERA: family asks if dose should change')
        self.assertEqual(out['route'], 'escalated')
        self.assertIn(self.nurse, self.res_a.sudo().activity_ids.user_id)
        self.assertTrue(self.env['peart.family.access.log'].search([('escalated', '=', True)]))

    def test_aria_uses_no_external_fallback(self):
        seen = {}
        fake = type('P', (), {})()

        def with_context(**kw):
            seen.update(kw)
            return fake
        fake.with_context = with_context
        fake.generate_content = lambda prompt, system_prompt=None: 'ok'
        with patch.object(type(self.env['peart.resident']), '_aria_provider', return_value=fake):
            self.res_a.portal_ask_aria(self.fam_a, 'hi')
        self.assertTrue(seen.get('ai_external_facing'))

    def test_aria_provider_failure_is_graceful(self):
        fake = type('P', (), {})()
        fake.with_context = lambda **kw: fake

        def boom(*a, **k):
            raise RuntimeError('down')
        fake.generate_content = boom
        with patch.object(type(self.env['peart.resident']), '_aria_provider', return_value=fake):
            out = self.res_a.portal_ask_aria(self.fam_a, 'hi')
        self.assertEqual(out['route'], 'error')

    def test_aria_rate_limit(self):
        for _ in range(6):
            self.assertEqual(self._ask('ok')['route'], 'answered')
        self.assertEqual(self._ask('ok')['route'], 'rate_limited')

    def test_aria_requires_message(self):
        with self.assertRaises(UserError):
            self._ask('ok', message='   ')

    def test_aria_history_is_trimmed(self):
        fake = type('P', (), {})()
        fake.with_context = lambda **kw: fake
        fake.generate_content = lambda prompt, system_prompt=None: (self.calls.append((prompt, system_prompt)) or 'ok')
        history = [{'role': 'user', 'content': 'q%s' % i} for i in range(20)]
        with patch.object(type(self.env['peart.resident']), '_aria_provider', return_value=fake):
            self.res_a.portal_ask_aria(self.fam_a, 'latest', history=history)
        prompt = self.calls[0][0]
        self.assertNotIn('q0', prompt)
        self.assertIn('q19', prompt)
        self.assertTrue(prompt.endswith('Family: latest'))

    # ---- provider selection: no silent default ----
    def test_aria_provider_needs_explicit_setting(self):
        icp = self.env['ir.config_parameter'].sudo()
        Provider = self.env['ai.provider.config'].sudo()
        default = Provider.search([('is_default', '=', True)], limit=1) or Provider.search([('active', '=', True)], limit=1)
        icp.set_param('peart_clinical_record.ai_provider_id', False)
        self.assertFalse(self.env['peart.resident']._aria_provider())
        out = self.res_a.portal_ask_aria(self.fam_a, 'hi')
        self.assertEqual(out['route'], 'error')  # no provider -> graceful, nothing sent anywhere
        if default:
            icp.set_param('peart_clinical_record.ai_provider_id', default.id)
            self.assertEqual(self.env['peart.resident']._aria_provider(), default)
            default.active = False
            self.assertFalse(self.env['peart.resident']._aria_provider())
