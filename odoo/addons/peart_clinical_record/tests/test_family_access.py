from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFamilyAccess(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)
        portal = cls.env.ref('base.group_portal')
        cls.family_a = Users.create({'name': 'Fam A', 'login': 'fam_a@test.com', 'group_ids': [(6, 0, portal.ids)]})
        cls.family_b = Users.create({'name': 'Fam B', 'login': 'fam_b@test.com', 'group_ids': [(6, 0, portal.ids)]})
        Partner = cls.env['res.partner']
        cls.res_a = cls.env['peart.resident'].create({'partner_id': Partner.create({'name': 'Resident A'}).id})
        cls.res_b = cls.env['peart.resident'].create({'partner_id': Partner.create({'name': 'Resident B'}).id})

    def _link(self, resident, user, enable=True):
        link = self.env['peart.resident.family.link'].create(
            {'resident_id': resident.id, 'user_id': user.id, 'relationship': 'Daughter'})
        if enable:
            self._consent(resident)
            link.access_enabled = True
        return link

    def _consent(self, resident, kind='family_access'):
        return self.env['peart.resident.consent'].create(
            {'resident_id': resident.id, 'kind': kind, 'signed_by': 'Resident'})

    def test_family_sees_only_own_resident(self):
        self._link(self.res_a, self.family_a)
        self._link(self.res_b, self.family_b)
        Res = self.env['peart.resident']
        self.assertEqual(Res._portal_resident(self.family_a, self.res_a.id), self.res_a)
        self.assertFalse(Res._portal_resident(self.family_a, self.res_b.id))
        self.assertEqual(Res._portal_my_residents(self.family_a)[0]['id'], self.res_a.id)
        self.assertEqual(len(Res._portal_my_residents(self.family_a)), 1)

    def test_link_without_consent_grants_nothing(self):
        self._link(self.res_a, self.family_a, enable=False)
        self.assertFalse(self.env['peart.resident']._portal_my_residents(self.family_a))

    def test_cannot_enable_without_consent(self):
        link = self._link(self.res_a, self.family_a, enable=False)
        with self.assertRaises(ValidationError):
            link.access_enabled = True

    def test_revoking_consent_cuts_access(self):
        link = self._link(self.res_a, self.family_a)
        self.res_a.consent_ids.filtered(lambda c: c.kind == 'family_access').action_revoke()
        self.assertFalse(link.access_enabled)
        self.assertFalse(self.env['peart.resident']._portal_resident(self.family_a, self.res_a.id))

    def test_family_has_no_orm_access_at_all(self):
        # The API is the only door: /web/dataset/call_kw must give nothing.
        self._link(self.res_a, self.family_a)
        res = self.res_a.with_user(self.family_a)
        with self.assertRaises(AccessError):
            res.write({'room': '12'})
        with self.assertRaises(AccessError):
            res.read(['emergency_contact_phone'])
        with self.assertRaises(AccessError):
            self.env['peart.resident'].with_user(self.family_a).search([])

    def test_staff_cannot_be_linked(self):
        with self.assertRaises(ValidationError):
            self.env['peart.resident.family.link'].create(
                {'resident_id': self.res_a.id, 'user_id': self.env.ref('base.user_admin').id})

    def test_family_cannot_read_consents(self):
        self._link(self.res_a, self.family_a)
        with self.assertRaises(AccessError):
            self.env['peart.resident.consent'].with_user(self.family_a).search([])


@tagged('post_install', '-at_install')
class TestAdmissionToResident(TransactionCase):

    def test_admitting_creates_resident_and_inactive_family_link(self):
        Users = self.env['res.users'].with_context(no_reset_password=True)
        family = Users.create({
            'name': 'Applicant', 'login': 'applicant@test.com', 'email': 'applicant@test.com',
            'group_ids': [(6, 0, self.env.ref('base.group_portal').ids)],
        })
        admission = self.env['peart.admission'].create({
            'applicant_name': 'Applicant', 'applicant_email': 'applicant@test.com',
            'applicant_relationship': 'Son', 'resident_name': 'Mr Peart',
            'care_type_requested': self.env['peart.care.type'].search([], limit=1).id,
            'mobility_level': 'assisted',
        })
        admission.applicant_partner_id = family.partner_id
        admission.action_mark_admitted()
        resident = admission.resident_id
        self.assertTrue(resident)
        self.assertEqual(resident.name, 'Mr Peart')
        self.assertEqual(resident.care_level, '2')
        link = resident.family_link_ids
        self.assertEqual(link.user_id, family)
        self.assertFalse(link.access_enabled)
        # Idempotent
        admission.action_mark_admitted()
        self.assertEqual(admission.resident_id, resident)
        self.assertEqual(self.env['peart.resident'].search_count([('admission_id', '=', admission.id)]), 1)
