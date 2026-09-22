from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestFamilyPortalHttp(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)
        portal = cls.env.ref('base.group_portal')
        cls.fam_a = Users.create({'name': 'Fam A', 'login': 'ha@test.com', 'password': 'ha@test.com',
                                  'group_ids': [(6, 0, portal.ids)]})
        cls.fam_b = Users.create({'name': 'Fam B', 'login': 'hb@test.com', 'password': 'hb@test.com',
                                  'group_ids': [(6, 0, portal.ids)]})
        Partner = cls.env['res.partner']
        cls.res_a = cls.env['peart.resident'].create({'partner_id': Partner.create({'name': 'HTTP A'}).id})
        cls.res_b = cls.env['peart.resident'].create({'partner_id': Partner.create({'name': 'HTTP B'}).id})
        for res, fam in ((cls.res_a, cls.fam_a), (cls.res_b, cls.fam_b)):
            cls.env['peart.resident.consent'].create({'resident_id': res.id, 'kind': 'family_access', 'signed_by': 'x'})
            cls.env['peart.resident.family.link'].create(
                {'resident_id': res.id, 'user_id': fam.id, 'access_enabled': True})
        Doc = cls.env['peart.resident.document']
        cls.shared_doc = Doc.create({'resident_id': cls.res_a.id, 'name': 'ok', 'file': 'ZmFrZQ==', 'family_visible': True})
        cls.hidden_doc = Doc.create({'resident_id': cls.res_a.id, 'name': 'no', 'file': 'ZmFrZQ=='})
        cls.other_doc = Doc.create({'resident_id': cls.res_b.id, 'name': 'b', 'file': 'ZmFrZQ==', 'family_visible': True})

    def _rpc(self, path, **params):
        response = self.url_open(path, json={'jsonrpc': '2.0', 'method': 'call', 'params': params})
        return response.json()

    def test_anonymous_gets_no_data(self):
        self.authenticate(None, None)
        body = self._rpc('/api/my/resident/summary', resident_id=self.res_a.id)
        self.assertNotIn('result', body)
        self.assertNotIn('HTTP A', str(body))

    def test_family_reads_own_and_not_others(self):
        self.authenticate('ha@test.com', 'ha@test.com')
        own = self._rpc('/api/my/resident/summary', resident_id=self.res_a.id)['result']
        self.assertTrue(own['success'])
        self.assertEqual(own['resident']['name'], 'HTTP A')
        other = self._rpc('/api/my/resident/summary', resident_id=self.res_b.id)['result']
        self.assertEqual(other, {'success': False, 'error': 'not_found'})
        for path in ('timeline', 'record', 'documents', 'aria'):
            body = self._rpc('/api/my/resident/' + path, resident_id=self.res_b.id, message='x')['result']
            self.assertEqual(body, {'success': False, 'error': 'not_found'}, path)

    def test_my_residents_lists_only_own(self):
        self.authenticate('ha@test.com', 'ha@test.com')
        names = [r['name'] for r in self._rpc('/api/my/residents')['result']['records']]
        self.assertEqual(names, ['HTTP A'])

    def test_aria_needs_ai_consent(self):
        self.authenticate('ha@test.com', 'ha@test.com')
        body = self._rpc('/api/my/resident/aria', resident_id=self.res_a.id, message='hello')['result']
        self.assertEqual(body, {'success': False, 'error': 'ai_consent_missing'})

    def test_document_download_rules(self):
        self.authenticate('ha@test.com', 'ha@test.com')
        base = '/api/my/resident/document/%s'
        ok = self.url_open(base % self.shared_doc.id)
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.content, b'fake')
        self.assertIn('attachment', ok.headers['Content-Disposition'])
        self.assertEqual(self.url_open(base % self.hidden_doc.id).status_code, 404)
        self.assertEqual(self.url_open(base % self.other_doc.id).status_code, 404)
        self.assertEqual(self.url_open(base % 999999).status_code, 404)

    def test_access_is_audited(self):
        self.authenticate('ha@test.com', 'ha@test.com')
        self._rpc('/api/my/resident/summary', resident_id=self.res_a.id)
        self.url_open('/api/my/resident/document/%s' % self.shared_doc.id)
        actions = self.env['peart.family.access.log'].search([('user_id', '=', self.fam_a.id)]).mapped('action')
        self.assertCountEqual(actions, ['summary', 'download'])
