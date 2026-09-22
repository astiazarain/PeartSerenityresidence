from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

CLINICAL_GROUPS = ('peart_clinical_record.group_clinical_doctor,'
                   'peart_clinical_record.group_clinical_nurse,'
                   'peart_clinical_record.group_clinical_ceo')


class PeartResidentIntake(models.Model):
    """Clinical baseline captured at admission (one per resident)."""
    _name = 'peart.resident.intake'
    _description = 'Resident Clinical Intake'
    _inherit = ['mail.thread']

    resident_id = fields.Many2one('peart.resident', required=True, ondelete='cascade', index=True)
    name = fields.Char(related='resident_id.name')
    reason_for_admission = fields.Text(tracking=True)
    code_status = fields.Selection([
        ('not_set', 'Not yet discussed'),
        ('full', 'Full resuscitation'),
        ('dnr', 'Do not resuscitate (DNR)'),
        ('dnr_dni', 'DNR / do not intubate'),
        ('comfort', 'Comfort care only'),
    ], default='not_set', required=True, tracking=True)
    advance_directive = fields.Text(help='Living will, health-care proxy, wishes about hospital transfer.')
    blood_type = fields.Selection([
        ('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'), ('b-', 'B-'),
        ('ab+', 'AB+'), ('ab-', 'AB-'), ('o+', 'O+'), ('o-', 'O-'), ('unknown', 'Unknown')], default='unknown')
    diet_type = fields.Selection([
        ('regular', 'Regular'), ('diabetic', 'Diabetic'), ('low_sodium', 'Low sodium'),
        ('soft', 'Soft / minced'), ('pureed', 'Pureed'), ('thickened', 'Thickened fluids'), ('other', 'Other')],
        default='regular')
    diet_notes = fields.Text()
    swallowing_difficulty = fields.Boolean()
    dentures = fields.Boolean()
    vision = fields.Selection([('normal', 'Normal'), ('glasses', 'Glasses'), ('impaired', 'Impaired'), ('blind', 'Blind')])
    hearing = fields.Selection([('normal', 'Normal'), ('aid', 'Hearing aid'), ('impaired', 'Impaired'), ('deaf', 'Deaf')])
    mobility_aid = fields.Char(help='Cane, walker, wheelchair...')
    continence_urine = fields.Selection([('continent', 'Continent'), ('occasional', 'Occasional'), ('incontinent', 'Incontinent'), ('catheter', 'Catheter')])
    continence_bowel = fields.Selection([('continent', 'Continent'), ('occasional', 'Occasional'), ('incontinent', 'Incontinent'), ('stoma', 'Stoma')])
    cognition_baseline = fields.Text(help='Orientation, memory, behaviour on arrival.')
    skin_on_admission = fields.Text(help='Wounds, pressure areas or bruising found on arrival.')
    spiritual_preferences = fields.Char()

    _resident_uniq = models.Constraint('unique(resident_id)', 'This resident already has a clinical intake.')


class PeartResidentAllergy(models.Model):
    _name = 'peart.resident.allergy'
    _description = 'Resident Allergy'
    _order = 'severity desc, id'

    resident_id = fields.Many2one('peart.resident', required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Allergen', required=True)
    category = fields.Selection(
        [('drug', 'Drug'), ('food', 'Food'), ('environment', 'Environmental'), ('other', 'Other')], default='drug')
    reaction = fields.Char()
    severity = fields.Selection(
        [('mild', 'Mild'), ('moderate', 'Moderate'), ('severe', 'Severe / anaphylaxis')], default='moderate')
    family_visible = fields.Boolean(string='Visible to family', default=True)


class PeartResidentCondition(models.Model):
    _name = 'peart.resident.condition'
    _description = 'Resident Diagnosis / History'
    _inherit = ['mail.thread']
    _order = 'status, onset_date desc'

    resident_id = fields.Many2one('peart.resident', required=True, ondelete='cascade', index=True)
    kind = fields.Selection([
        ('diagnosis', 'Diagnosis'), ('surgery', 'Surgery / procedure'),
        ('history', 'Past medical history'), ('family', 'Family history')], default='diagnosis', required=True)
    name = fields.Char(string='Condition', required=True, tracking=True)
    icd10 = fields.Char(string='ICD-10')
    onset_date = fields.Date()
    status = fields.Selection(
        [('active', 'Active'), ('chronic', 'Chronic'), ('resolved', 'Resolved')], default='active', required=True, tracking=True)
    notes = fields.Text()
    recorded_by_id = fields.Many2one('res.users', default=lambda s: s.env.user, readonly=True)
    family_visible = fields.Boolean(string='Visible to family', default=False)


class PeartResidentMedication(models.Model):
    _name = 'peart.resident.medication'
    _description = 'Resident Medication Order'
    _inherit = ['mail.thread']
    _order = 'state, name'

    resident_id = fields.Many2one('peart.resident', required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Drug', required=True, tracking=True)
    dose = fields.Char(required=True, tracking=True, help='e.g. 500 mg, 2 puffs')
    route = fields.Selection([
        ('oral', 'Oral'), ('sl', 'Sublingual'), ('im', 'Intramuscular'), ('iv', 'Intravenous'),
        ('sc', 'Subcutaneous'), ('topical', 'Topical'), ('inhaled', 'Inhaled'),
        ('eye', 'Eye / ear'), ('rectal', 'Rectal'), ('other', 'Other')], default='oral', required=True)
    frequency = fields.Selection([
        ('od', 'Once daily'), ('bid', 'Twice daily'), ('tid', 'Three times daily'), ('qid', 'Four times daily'),
        ('q8h', 'Every 8 hours'), ('weekly', 'Weekly'), ('prn', 'As needed (PRN)'), ('other', 'Other')],
        default='od', required=True, tracking=True)
    schedule_times = fields.Char(help='Administration times, e.g. 08:00, 20:00')
    prn_reason = fields.Char(string='PRN indication')
    instructions = fields.Text()
    start_date = fields.Date(default=fields.Date.context_today, required=True)
    end_date = fields.Date()
    prescriber_id = fields.Many2one('res.users', string='Prescribed by', default=lambda s: s.env.user, readonly=True)
    state = fields.Selection([('active', 'Active'), ('stopped', 'Stopped')], default='active', tracking=True)
    stop_reason = fields.Char()
    family_visible = fields.Boolean(string='Visible to family', default=True)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(_('The end date cannot be before the start date.'))

    def action_stop(self):
        self.write({'state': 'stopped', 'end_date': fields.Date.context_today(self)})


class PeartResidentContact(models.Model):
    _name = 'peart.resident.contact'
    _description = 'Resident Medical Contact'

    resident_id = fields.Many2one('peart.resident', required=True, ondelete='cascade', index=True)
    kind = fields.Selection([
        ('physician', 'Primary physician'), ('specialist', 'Specialist'), ('hospital', 'Referral hospital'),
        ('pharmacy', 'Pharmacy'), ('insurance', 'Insurance'), ('legal', 'Legal representative'),
        ('other', 'Other')], default='physician', required=True)
    name = fields.Char(required=True)
    organization = fields.Char()
    phone = fields.Char()
    email = fields.Char()
    policy_number = fields.Char()
    notes = fields.Char()


class PeartResidentCarePlan(models.Model):
    _name = 'peart.resident.care.plan'
    _description = 'Resident Care Plan Item'
    _inherit = ['mail.thread']
    _order = 'state, review_date'

    resident_id = fields.Many2one('peart.resident', required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Need / problem', required=True, tracking=True)
    goal = fields.Text(required=True)
    intervention = fields.Text(required=True)
    responsible = fields.Selection(
        [('nurse', 'Nurse'), ('doctor', 'Doctor'), ('all', 'All care staff')], default='nurse')
    start_date = fields.Date(default=fields.Date.context_today)
    review_date = fields.Date(help='Plans are reviewed at least every 3 months.')
    state = fields.Selection(
        [('active', 'Active'), ('achieved', 'Goal achieved'), ('discontinued', 'Discontinued')],
        default='active', tracking=True)
    family_visible = fields.Boolean(string='Visible to family', default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('review_date'):
                start = fields.Date.to_date(vals.get('start_date')) or fields.Date.context_today(self)
                vals['review_date'] = fields.Date.add(start, months=3)
        return super().create(vals_list)


class PeartResidentDocument(models.Model):
    _name = 'peart.resident.document'
    _description = 'Resident Document'
    _order = 'date desc, id desc'

    # Documents of these categories are non-clinical: the Administrator role
    # may manage them. Everything else is clinical (see clinical_rules.xml).
    ADMIN_CATEGORIES = ('id_document', 'legal', 'insurance', 'billing', 'consent')

    resident_id = fields.Many2one('peart.resident', required=True, ondelete='cascade', index=True)
    name = fields.Char(required=True)
    category = fields.Selection([
        ('medical_report', 'Medical report'), ('lab', 'Laboratory result'), ('imaging', 'Imaging'),
        ('prescription', 'Prescription'), ('id_document', 'ID document'), ('legal', 'Legal'),
        ('insurance', 'Insurance'), ('billing', 'Billing'), ('consent', 'Signed consent'),
        ('other', 'Other')], default='medical_report', required=True)
    date = fields.Date(default=fields.Date.context_today)
    file = fields.Binary(required=True, attachment=True)
    filename = fields.Char()
    uploaded_by_id = fields.Many2one('res.users', default=lambda s: s.env.user, readonly=True)
    family_visible = fields.Boolean(string='Visible to family', default=False)


class PeartResident(models.Model):
    _inherit = 'peart.resident'

    intake_ids = fields.One2many('peart.resident.intake', 'resident_id')
    allergy_ids = fields.One2many('peart.resident.allergy', 'resident_id')
    condition_ids = fields.One2many('peart.resident.condition', 'resident_id')
    medication_ids = fields.One2many('peart.resident.medication', 'resident_id')
    contact_ids = fields.One2many('peart.resident.contact', 'resident_id', string='Medical Contacts')
    care_plan_ids = fields.One2many('peart.resident.care.plan', 'resident_id')
    document_ids = fields.One2many('peart.resident.document', 'resident_id')
    assessment_ids = fields.One2many('peart.resident.assessment', 'resident_id')

    # Headline shown on the file - only for roles that may read clinical data.
    allergy_summary = fields.Char(compute='_compute_clinical_headline', groups=CLINICAL_GROUPS)
    code_status = fields.Selection(related='intake_ids.code_status', groups=CLINICAL_GROUPS)

    @api.depends('allergy_ids.name', 'allergy_ids.severity')
    def _compute_clinical_headline(self):
        for rec in self:
            names = rec.allergy_ids.sorted('severity', reverse=True).mapped('name')
            rec.allergy_summary = ', '.join(names) if names else _('No known allergies recorded')

    def action_open_intake(self):
        self.ensure_one()
        intake = self.intake_ids[:1] or self.env['peart.resident.intake'].create({'resident_id': self.id})
        return {
            'type': 'ir.actions.act_window', 'res_model': 'peart.resident.intake',
            'res_id': intake.id, 'view_mode': 'form', 'target': 'current',
        }

    def action_new_assessment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'res_model': 'peart.resident.assessment',
            'view_mode': 'form', 'target': 'current',
            'context': {'default_resident_id': self.id},
        }

    def action_ask_aria(self):
        self.ensure_one()
        return self.env['peart.clinical.assistant.wizard'].action_open_for_resident(self.id)

    def action_request_nursing_task(self):
        self.ensure_one()
        return self.env['peart.nursing.task.wizard'].action_open_for_resident(self.id)
