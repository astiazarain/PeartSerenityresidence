from odoo import _, fields, models


class PeartAdmission(models.Model):
    _inherit = 'peart.admission'

    resident_id = fields.Many2one('peart.resident', readonly=True, copy=False)

    def action_mark_admitted(self):
        res = super().action_mark_admitted()
        self._ensure_resident()
        return res

    def action_create_resident(self):
        self.ensure_one()
        resident = self._ensure_resident()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'peart.resident',
            'res_id': resident.id,
            'view_mode': 'form',
        }

    def _ensure_resident(self):
        """Create the resident file from the admission (idempotent).

        The applicant's portal user, if they already have one, is linked but
        left INACTIVE: family access starts only after a consent is recorded.
        """
        Resident = self.env['peart.resident'].sudo()
        last = Resident.browse()
        for rec in self:
            if rec.resident_id:
                last = rec.resident_id
                continue
            if not rec.resident_partner_id:
                rec._ensure_partners()
            resident = Resident.search([('partner_id', '=', rec.resident_partner_id.id)], limit=1)
            if not resident:
                resident = Resident.create({
                    'partner_id': rec.resident_partner_id.id,
                    'admission_id': rec.id,
                    'date_of_birth': rec.resident_dob,
                    'gender': rec.resident_gender,
                    'care_level': rec.care_level,
                    'emergency_contact_name': rec.emergency_contact_name,
                    'emergency_contact_relationship': rec.emergency_contact_relationship,
                    'emergency_contact_phone': rec.emergency_contact_phone,
                    'emergency_contact_email': rec.emergency_contact_email,
                })
            rec.resident_id = resident
            applicant_user = rec.applicant_partner_id.user_ids.filtered('share')[:1]
            if applicant_user and not resident.family_link_ids.filtered(lambda l: l.user_id == applicant_user):
                self.env['peart.resident.family.link'].sudo().create({
                    'resident_id': resident.id,
                    'user_id': applicant_user.id,
                    'relationship': rec.applicant_relationship,
                    'is_primary': True,
                })
            last = resident
        return last
