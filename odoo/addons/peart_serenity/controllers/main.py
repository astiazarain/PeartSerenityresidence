from odoo import http
from odoo.http import request

CARE_QUOTE_REQUIRED_FIELDS = [
    'applicant_name', 'applicant_email', 'resident_name', 'care_type_requested',
]

CARE_QUOTE_ALLOWED_FIELDS = [
    'applicant_name', 'applicant_email', 'applicant_phone', 'applicant_relationship',
    'resident_name', 'resident_dob', 'resident_gender', 'resident_address',
    'care_type_requested', 'preferred_start_date', 'urgency', 'mobility_level',
    'requires_specialized_care', 'specialized_care_details',
    'primary_diagnosis', 'medications', 'allergies', 'dietary_restrictions',
    'physician_name', 'physician_phone',
    'emergency_contact_name', 'emergency_contact_relationship',
    'emergency_contact_phone', 'emergency_contact_email',
    'family_physician', 'insurance_provider', 'insurance_number',
    'preferred_payment_method', 'additional_notes',
]

TOUR_BOOKING_REQUIRED_FIELDS = ['name', 'email', 'preferred_date']
TOUR_BOOKING_ALLOWED_FIELDS = [
    'name', 'email', 'phone', 'preferred_date', 'preferred_time', 'party_size', 'message',
]

CONTACT_REQUIRED_FIELDS = ['name', 'email', 'message']

WAITLIST_REQUIRED_FIELDS = ['name', 'email', 'care_type']
WAITLIST_ALLOWED_FIELDS = ['name', 'email', 'phone', 'country', 'care_type', 'urgency', 'notes']

TESTIMONIAL_READ_FIELDS = ['author_name', 'relation', 'location', 'content', 'rating']

ADMISSION_READ_FIELDS = ['resident_name', 'care_type_requested', 'state', 'create_date']
TOUR_READ_FIELDS = ['preferred_date', 'preferred_time', 'party_size', 'status', 'create_date']


class PeartSerenityCareAPI(http.Controller):
    # Public JSON-RPC API consumed by the website (project/src/lib/odoo.ts).
    # Routes are called as JSON-RPC (POST body: {jsonrpc, method, params}).
    # `auth='public'` routes elevate to sudo() explicitly and only after
    # validating their own inputs - visitors are never given direct model
    # access. `auth='user'` routes require a valid Odoo session (portal
    # login) and always scope queries to request.env.user's own partner.

    # ---- Care admissions -------------------------------------------------

    @http.route('/api/care-quote', type='jsonrpc', auth='public', methods=['POST'])
    def submit_care_quote(self, **payload):
        missing = [f for f in CARE_QUOTE_REQUIRED_FIELDS if not payload.get(f)]
        if missing:
            return {'success': False, 'error': f"Missing required fields: {', '.join(missing)}"}

        vals = {k: v for k, v in payload.items() if k in CARE_QUOTE_ALLOWED_FIELDS}
        admission = request.env['peart.admission'].sudo().create(vals)
        return {'success': True, 'id': admission.id}

    # ---- Contact / tours / waitlist / testimonials ------------------------

    @http.route('/api/contact', type='jsonrpc', auth='public', methods=['POST'])
    def submit_contact(self, **payload):
        missing = [f for f in CONTACT_REQUIRED_FIELDS if not payload.get(f)]
        if missing:
            return {'success': False, 'error': f"Missing required fields: {', '.join(missing)}"}

        team = request.env.ref('peart_serenity.crm_team_care_admissions', raise_if_not_found=False)
        stage = request.env.ref('peart_serenity.crm_stage_care_new', raise_if_not_found=False)
        description_parts = [payload.get('message', '')]
        if payload.get('service_type'):
            description_parts.append(f"Service of interest: {payload['service_type']}")
        if payload.get('preferred_date'):
            description_parts.append(f"Preferred start date: {payload['preferred_date']}")
        if payload.get('country'):
            description_parts.append(f"Country: {payload['country']}")

        lead = request.env['crm.lead'].sudo().create({
            'name': f"Website Inquiry — {payload.get('name')}",
            'contact_name': payload.get('name'),
            'email_from': payload.get('email'),
            'phone': payload.get('phone'),
            'description': '\n'.join(description_parts),
            'team_id': team.id if team else False,
            'stage_id': stage.id if stage else False,
        })
        return {'success': True, 'id': lead.id}

    @http.route('/api/tour-booking', type='jsonrpc', auth='public', methods=['POST'])
    def submit_tour_booking(self, **payload):
        missing = [f for f in TOUR_BOOKING_REQUIRED_FIELDS if not payload.get(f)]
        if missing:
            return {'success': False, 'error': f"Missing required fields: {', '.join(missing)}"}

        vals = {k: v for k, v in payload.items() if k in TOUR_BOOKING_ALLOWED_FIELDS}
        booking = request.env['peart.tour.booking'].sudo().create(vals)
        return {'success': True, 'id': booking.id}

    @http.route('/api/waitlist', type='jsonrpc', auth='public', methods=['POST'])
    def submit_waitlist(self, **payload):
        missing = [f for f in WAITLIST_REQUIRED_FIELDS if not payload.get(f)]
        if missing:
            return {'success': False, 'error': f"Missing required fields: {', '.join(missing)}"}

        vals = {k: v for k, v in payload.items() if k in WAITLIST_ALLOWED_FIELDS}
        entry = request.env['peart.waitlist'].sudo().create(vals)
        return {'success': True, 'id': entry.id}

    @http.route('/api/testimonials', type='jsonrpc', auth='public', methods=['POST'])
    def list_testimonials(self, **payload):
        limit = min(int(payload.get('limit') or 6), 20)
        testimonials = request.env['peart.testimonial'].sudo().search(
            [('approved', '=', True)], order='featured desc, create_date desc', limit=limit)
        return {'success': True, 'records': testimonials.read(TESTIMONIAL_READ_FIELDS)}

    # ---- Account sign-up ---------------------------------------------------

    @http.route('/api/auth/signup', type='jsonrpc', auth='public', methods=['POST'])
    def signup(self, **payload):
        name = payload.get('name')
        email = payload.get('email')
        password = payload.get('password')
        if not name or not email or not password:
            return {'success': False, 'error': 'name, email and password are required'}
        if request.env['res.users'].sudo().search_count([('login', '=', email)]):
            return {'success': False, 'error': 'An account with this email already exists.'}

        partner = request.env['res.partner'].sudo().peart_find_or_create(name, email=email)
        portal_group = request.env.ref('base.group_portal')
        request.env['res.users'].sudo().create({
            'name': name,
            'login': email,
            'email': email,
            'password': password,
            'partner_id': partner.id,
            'group_ids': [(6, 0, [portal_group.id])],
        })
        return {'success': True}

    # ---- Family portal (requires an authenticated Odoo session) -----------

    @http.route('/api/my/admissions', type='jsonrpc', auth='user', methods=['POST'])
    def my_admissions(self, **payload):
        partner = request.env.user.partner_id
        admissions = request.env['peart.admission'].sudo().search([
            '|', ('applicant_partner_id', '=', partner.id), ('resident_partner_id', '=', partner.id),
        ], order='create_date desc')
        return {'success': True, 'records': admissions.read(ADMISSION_READ_FIELDS)}

    @http.route('/api/my/tours', type='jsonrpc', auth='user', methods=['POST'])
    def my_tours(self, **payload):
        partner = request.env.user.partner_id
        tours = request.env['peart.tour.booking'].sudo().search(
            [('partner_id', '=', partner.id)], order='create_date desc')
        return {'success': True, 'records': tours.read(TOUR_READ_FIELDS)}
