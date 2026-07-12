from odoo import api, fields, models

# Maps the "type of care" the family selected on the public form to the
# default service product suggested on the quotation. Staff can always add,
# remove or swap lines afterwards - this only saves them a click.
CARE_TYPE_PRODUCT_XMLID = {
    'day_care': 'peart_serenity.product_care_day',
    'respite': 'peart_serenity.product_care_respite_week',
    'long_term': 'peart_serenity.product_care_shared_monthly',
    'private_suite': 'peart_serenity.product_care_private_suite_monthly',
    'recovery': 'peart_serenity.product_care_postop_recovery',
    'specialized': 'peart_serenity.product_care_private_suite_monthly',
}


class PeartAdmission(models.Model):
    _name = 'peart.admission'
    _description = 'Care Admission Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(compute='_compute_name', store=True)

    state = fields.Selection([
        ('new', 'New'),
        ('assessed', 'Assessed'),
        ('quoted', 'Quoted'),
        ('admitted', 'Admitted'),
        ('declined', 'Declined'),
    ], default='new', required=True, tracking=True)

    # Section A - Applicant
    applicant_name = fields.Char(required=True)
    applicant_email = fields.Char(required=True)
    applicant_phone = fields.Char()
    applicant_relationship = fields.Char()
    applicant_partner_id = fields.Many2one('res.partner', readonly=True)

    # Section B - Resident
    resident_name = fields.Char(required=True)
    resident_dob = fields.Date()
    resident_gender = fields.Selection([
        ('male', 'Male'), ('female', 'Female'), ('other', 'Other'),
    ])
    resident_address = fields.Char()
    resident_partner_id = fields.Many2one('res.partner', readonly=True)

    # Section C - Care needs
    care_type_requested = fields.Selection([
        ('day_care', 'Adult Day Care'),
        ('respite', 'Respite Care'),
        ('long_term', 'Long-Term Residential'),
        ('private_suite', 'Private Suite'),
        ('recovery', 'Post-Surgical Recovery'),
        ('specialized', 'Specialized Care'),
    ], required=True)
    preferred_start_date = fields.Date()
    urgency = fields.Selection([
        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High'),
    ], default='medium')
    mobility_level = fields.Selection([
        ('independent', 'Independent'),
        ('assisted', 'Requires assistance'),
        ('wheelchair', 'Wheelchair user'),
        ('bedbound', 'Bedbound'),
    ])
    requires_specialized_care = fields.Boolean()
    specialized_care_details = fields.Text()

    # Section D - Medical (confidential - see security/ir.model.access.csv)
    primary_diagnosis = fields.Char()
    medications = fields.Text()
    allergies = fields.Char()
    dietary_restrictions = fields.Char()
    physician_name = fields.Char()
    physician_phone = fields.Char()

    # Section E - Emergency contact
    emergency_contact_name = fields.Char()
    emergency_contact_relationship = fields.Char()
    emergency_contact_phone = fields.Char()
    emergency_contact_email = fields.Char()

    # Section F - Family / financial
    family_physician = fields.Char()
    insurance_provider = fields.Char()
    insurance_number = fields.Char()
    preferred_payment_method = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('wire', 'Wire Transfer (Diaspora)'),
        ('insurance', 'Insurance Billing'),
    ], default='monthly')

    # Section G - Additional
    additional_notes = fields.Text()

    # Internal / pipeline
    care_level = fields.Selection([
        ('1', 'Low'), ('2', 'Moderate'), ('3', 'High'), ('4', 'Specialized'),
    ], compute='_compute_care_level', store=True,
        help='Internal triage signal from mobility/specialized-care answers. '
             'Guides which service and add-ons staff quote - never shown publicly.')
    suggested_product_id = fields.Many2one(
        'product.product', compute='_compute_suggested_product',
        help='Default line proposed on the quotation based on the requested care type.')
    crm_lead_id = fields.Many2one('crm.lead', readonly=True, copy=False)
    sale_order_id = fields.Many2one('sale.order', readonly=True, copy=False)
    sale_order_count = fields.Integer(compute='_compute_sale_order_count')

    @api.depends('resident_name', 'applicant_name')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.resident_name or rec.applicant_name or 'New Admission'

    @api.depends('mobility_level', 'requires_specialized_care')
    def _compute_care_level(self):
        for rec in self:
            if rec.requires_specialized_care or rec.mobility_level == 'bedbound':
                rec.care_level = '4'
            elif rec.mobility_level == 'wheelchair':
                rec.care_level = '3'
            elif rec.mobility_level == 'assisted':
                rec.care_level = '2'
            else:
                rec.care_level = '1'

    @api.depends('care_type_requested')
    def _compute_suggested_product(self):
        for rec in self:
            xmlid = CARE_TYPE_PRODUCT_XMLID.get(rec.care_type_requested)
            product = self.env.ref(xmlid, raise_if_not_found=False) if xmlid else False
            rec.suggested_product_id = product.product_variant_id if product else False

    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = 1 if rec.sale_order_id else 0

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._ensure_partners()
        records._ensure_crm_lead()
        return records

    def _ensure_partners(self):
        Partner = self.env['res.partner']
        for rec in self:
            if not rec.resident_partner_id and rec.resident_name:
                rec.resident_partner_id = Partner.peart_find_or_create(rec.resident_name)
            if not rec.applicant_partner_id and rec.applicant_name:
                rec.applicant_partner_id = Partner.peart_find_or_create(
                    rec.applicant_name, email=rec.applicant_email, phone=rec.applicant_phone)

    def _ensure_crm_lead(self):
        team = self.env.ref('peart_serenity.crm_team_care_admissions', raise_if_not_found=False)
        stage_new = self.env.ref('peart_serenity.crm_stage_care_new', raise_if_not_found=False)
        for rec in self:
            if rec.crm_lead_id:
                continue
            lead = self.env['crm.lead'].create({
                'name': f'Care Quote — {rec.resident_name}',
                'partner_id': rec.applicant_partner_id.id,
                'contact_name': rec.applicant_name,
                'email_from': rec.applicant_email,
                'phone': rec.applicant_phone,
                'team_id': team.id if team else False,
                'stage_id': stage_new.id if stage_new else False,
                'description': rec.additional_notes or '',
            })
            rec.crm_lead_id = lead.id

    def action_mark_assessed(self):
        self.write({'state': 'assessed'})
        stage = self.env.ref('peart_serenity.crm_stage_care_assessed', raise_if_not_found=False)
        for rec in self:
            if rec.crm_lead_id and stage:
                rec.crm_lead_id.stage_id = stage.id

    def action_mark_admitted(self):
        self.write({'state': 'admitted'})
        stage = self.env.ref('peart_serenity.crm_stage_care_admitted', raise_if_not_found=False)
        for rec in self:
            if rec.crm_lead_id and stage:
                rec.crm_lead_id.stage_id = stage.id

    def action_mark_declined(self):
        self.write({'state': 'declined'})

    def action_create_quotation(self):
        self.ensure_one()
        if self.sale_order_id:
            return self._quotation_action_window(self.sale_order_id)

        team = self.env.ref('peart_serenity.crm_team_care_admissions', raise_if_not_found=False)
        template = self.env.ref('peart_serenity.sale_order_template_care_quote', raise_if_not_found=False)

        order_vals = {
            'partner_id': self.resident_partner_id.id or self.applicant_partner_id.id,
            'origin': self.name,
        }
        if team:
            order_vals['team_id'] = team.id
        if template:
            order_vals['sale_order_template_id'] = template.id
            order_vals['note'] = template.note

        order = self.env['sale.order'].create(order_vals)
        if self.suggested_product_id:
            self.env['sale.order.line'].create({
                'order_id': order.id,
                'product_id': self.suggested_product_id.id,
                'product_uom_qty': 1,
            })

        self.sale_order_id = order.id
        self.state = 'quoted'
        stage = self.env.ref('peart_serenity.crm_stage_care_quoted', raise_if_not_found=False)
        if self.crm_lead_id and stage:
            self.crm_lead_id.stage_id = stage.id

        return self._quotation_action_window(order)

    def _quotation_action_window(self, order):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Quotation',
            'res_model': 'sale.order',
            'res_id': order.id,
            'view_mode': 'form',
            'target': 'current',
        }
