from odoo import api, fields, models


class PeartResident(models.Model):
    _name = 'peart.resident'
    _description = 'Resident'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    code = fields.Char(string='Resident Code', readonly=True, copy=False, default='New')
    partner_id = fields.Many2one('res.partner', string='Contact', required=True, ondelete='restrict')
    name = fields.Char(related='partner_id.name', store=True, readonly=False)
    image_1920 = fields.Image(related='partner_id.image_1920', readonly=False)
    admission_id = fields.Many2one('peart.admission', readonly=True, copy=False, ondelete='set null')
    active = fields.Boolean(default=True)

    state = fields.Selection([
        ('active', 'In residence'),
        ('hospitalized', 'Hospitalized'),
        ('discharged', 'Discharged'),
        ('deceased', 'Deceased'),
    ], default='active', required=True, tracking=True)

    # Identity
    date_of_birth = fields.Date(tracking=True)
    age = fields.Integer(compute='_compute_age')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    preferred_lang = fields.Selection(
        [('es', 'Español'), ('en', 'English')], string='Preferred Language', default='en')

    # Stay
    admission_date = fields.Date(default=fields.Date.context_today, tracking=True)
    discharge_date = fields.Date(tracking=True)
    room = fields.Char(tracking=True)
    bed = fields.Char(tracking=True)
    care_level = fields.Selection(
        [('1', 'Low'), ('2', 'Moderate'), ('3', 'High'), ('4', 'Specialized')], tracking=True)

    # Emergency contact
    emergency_contact_name = fields.Char()
    emergency_contact_relationship = fields.Char()
    emergency_contact_phone = fields.Char()
    emergency_contact_email = fields.Char()

    family_link_ids = fields.One2many('peart.resident.family.link', 'resident_id')
    consent_ids = fields.One2many('peart.resident.consent', 'resident_id')
    family_link_count = fields.Integer(compute='_compute_counts')
    consent_count = fields.Integer(compute='_compute_counts')

    _partner_uniq = models.Constraint(
        'unique(partner_id)', 'This contact is already registered as a resident.')

    @api.depends('date_of_birth')
    def _compute_age(self):
        today = fields.Date.context_today(self)
        for rec in self:
            dob = rec.date_of_birth
            rec.age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day)) if dob else 0

    @api.depends('family_link_ids', 'consent_ids')
    def _compute_counts(self):
        for rec in self:
            rec.family_link_count = len(rec.family_link_ids)
            rec.consent_count = len(rec.consent_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code('peart.resident') or 'New'
        return super().create(vals_list)

    def has_consent(self, kind):
        """True if a granted, non-revoked consent of this kind is on file."""
        self.ensure_one()
        return bool(self.consent_ids.filtered_domain([('kind', '=', kind), ('state', '=', 'granted')]))
