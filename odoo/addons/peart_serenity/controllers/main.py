import base64
import binascii

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

SITE_SETTINGS_READ_FIELDS = [
    'whatsapp_number', 'whatsapp_message', 'facebook_url', 'instagram_url', 'tiktok_url', 'linkedin_url',
]

JOB_APPLICATION_REQUIRED_FIELDS = ['name', 'email', 'job_id']

MOST_POPULAR_TAG = 'Most Popular'

NOMENCLATOR_CODE_FIELDS = {
    'peart.waitlist': {'care_type': 'peart.care.type', 'urgency': 'peart.urgency.level'},
    'peart.admission': {'care_type_requested': 'peart.care.type', 'urgency': 'peart.urgency.level'},
}


class PeartSerenityCareAPI(http.Controller):
    # Public JSON-RPC API consumed by the website (project/src/lib/odoo.ts).
    # Routes are called as JSON-RPC (POST body: {jsonrpc, method, params}).
    # `auth='public'` routes elevate to sudo() explicitly and only after
    # validating their own inputs - visitors are never given direct model
    # access. `auth='user'` routes require a valid Odoo session (portal
    # login) and always scope queries to request.env.user's own partner.

    # ---- Nomenclators (Care Type / Urgency Level) --------------------------

    def _resolve_nomenclator_fields(self, res_model, vals):
        """Replace the string codes for nomenclator fields (e.g. care_type='long_term')
        with the id of the matching *active* record. Returns an error message if a
        code was supplied but doesn't match any active value."""
        for field_name, nomenclator_model in NOMENCLATOR_CODE_FIELDS.get(res_model, {}).items():
            code = vals.get(field_name)
            if not code:
                continue
            record = request.env[nomenclator_model].sudo().search(
                [('code', '=', code), ('active', '=', True)], limit=1)
            if not record:
                return f"'{code}' is not a valid or active value for {field_name}."
            vals[field_name] = record.id
        return None

    @http.route('/api/nomenclators', type='jsonrpc', auth='public', methods=['POST'])
    def list_nomenclators(self, **payload):
        care_types = request.env['peart.care.type'].sudo().search([('active', '=', True)], order='sequence, id')
        urgency_levels = request.env['peart.urgency.level'].sudo().search([('active', '=', True)], order='sequence, id')
        return {
            'success': True,
            'care_types': [{'code': r.code, 'name': r.name} for r in care_types],
            'urgency_levels': [{'code': r.code, 'name': r.name} for r in urgency_levels],
        }

    # ---- Care admissions -------------------------------------------------

    @http.route('/api/care-quote', type='jsonrpc', auth='public', methods=['POST'])
    def submit_care_quote(self, **payload):
        missing = [f for f in CARE_QUOTE_REQUIRED_FIELDS if not payload.get(f)]
        if missing:
            return {'success': False, 'error': f"Missing required fields: {', '.join(missing)}"}

        vals = {k: v for k, v in payload.items() if k in CARE_QUOTE_ALLOWED_FIELDS}
        error = self._resolve_nomenclator_fields('peart.admission', vals)
        if error:
            return {'success': False, 'error': error}
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
        error = self._resolve_nomenclator_fields('peart.waitlist', vals)
        if error:
            return {'success': False, 'error': error}
        entry = request.env['peart.waitlist'].sudo().create(vals)
        return {'success': True, 'id': entry.id}

    @http.route('/api/testimonials', type='jsonrpc', auth='public', methods=['POST'])
    def list_testimonials(self, **payload):
        limit = min(int(payload.get('limit') or 6), 20)
        testimonials = request.env['peart.testimonial'].sudo().search(
            [('approved', '=', True)], order='featured desc, create_date desc', limit=limit)
        records = testimonials.read(TESTIMONIAL_READ_FIELDS)
        for record, testimonial in zip(records, testimonials):
            record['photo'] = testimonial.photo.decode('utf-8') if testimonial.photo else False
        return {'success': True, 'records': records}

    # ---- Account sign-up ---------------------------------------------------

    @http.route('/api/auth/signup', type='jsonrpc', auth='public', methods=['POST'])
    def signup(self, **payload):
        name = payload.get('name')
        email = payload.get('email')
        password = payload.get('password')
        phone = payload.get('phone')
        username = payload.get('username')
        if not name or not email or not password or not phone or not username:
            return {'success': False, 'error': 'name, email, phone, username and password are required'}

        users = request.env['res.users'].sudo()
        if users.search_count([('login', '=', email)]):
            return {'success': False, 'error': 'An account with this email already exists.'}
        if users.search_count([('peart_username', '=', username)]):
            return {'success': False, 'error': 'This username is already taken.'}
        if users.search_count([('partner_id.phone', '=', phone)]):
            return {'success': False, 'error': 'An account with this phone number already exists.'}

        partner = request.env['res.partner'].sudo().peart_find_or_create(name, email=email, phone=phone)
        portal_group = request.env.ref('base.group_portal')
        users.create({
            'name': name,
            'login': email,
            'email': email,
            'password': password,
            'peart_username': username,
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
        records = admissions.read(ADMISSION_READ_FIELDS)
        for rec in records:
            rec['care_type_requested'] = rec['care_type_requested'][1] if rec['care_type_requested'] else False
        return {'success': True, 'records': records}

    @http.route('/api/my/tours', type='jsonrpc', auth='user', methods=['POST'])
    def my_tours(self, **payload):
        partner = request.env.user.partner_id
        tours = request.env['peart.tour.booking'].sudo().search(
            [('partner_id', '=', partner.id)], order='create_date desc')
        return {'success': True, 'records': tours.read(TOUR_READ_FIELDS)}

    # ---- Site settings (social links, WhatsApp) ----------------------------

    @http.route('/api/site-settings', type='jsonrpc', auth='public', methods=['POST'])
    def get_site_settings(self, **payload):
        settings = request.env['peart.site.settings'].sudo().search([], limit=1)
        if not settings:
            return {'success': True, **{f: False for f in SITE_SETTINGS_READ_FIELDS}}
        data = settings.read(SITE_SETTINGS_READ_FIELDS)[0]
        data.pop('id', None)
        return {'success': True, **data}

    # ---- Gallery -------------------------------------------------------------

    @http.route('/api/gallery', type='jsonrpc', auth='public', methods=['POST'])
    def list_gallery(self, **payload):
        domain = [('published', '=', True)]
        if payload.get('category'):
            domain.append(('category', '=', payload['category']))
        photos = request.env['peart.gallery.photo'].sudo().search(domain, order='sequence, id')
        records = [{
            'id': photo.id,
            'title': photo.title,
            'category': photo.category,
            'image': photo.image_512.decode('utf-8') if photo.image_512 else False,
        } for photo in photos]
        return {'success': True, 'records': records}

    # ---- Services (published service products) ------------------------------

    @http.route('/api/services', type='jsonrpc', auth='public', methods=['POST'])
    def list_services(self, **payload):
        products = request.env['product.template'].sudo().search(
            [('type', '=', 'service'), ('is_published', '=', True), ('sale_ok', '=', True)], order='id')
        records = [{
            'id': product.id,
            'name': product.name,
            'list_price': product.list_price,
            'price_period': product.website_price_period,
            'description_sale': product.description_sale or '',
            'features': [line.strip() for line in (product.website_features or '').splitlines() if line.strip()],
            'is_popular': MOST_POPULAR_TAG in product.product_tag_ids.mapped('name'),
        } for product in products]
        return {'success': True, 'records': records}

    # ---- Careers / job applications ------------------------------------------

    @http.route('/api/jobs', type='jsonrpc', auth='public', methods=['POST'])
    def list_jobs(self, **payload):
        jobs = request.env['hr.job'].sudo().search(
            [('website_published', '=', True), ('active', '=', True)], order='sequence, id')
        records = [{
            'id': job.id,
            'name': job.name,
            'department': job.department_id.name or False,
            'description': job.description or '',
        } for job in jobs]
        return {'success': True, 'records': records}

    @http.route('/api/jobs/apply', type='jsonrpc', auth='public', methods=['POST'])
    def apply_job(self, **payload):
        missing = [f for f in JOB_APPLICATION_REQUIRED_FIELDS if not payload.get(f)]
        if missing:
            return {'success': False, 'error': f"Missing required fields: {', '.join(missing)}"}

        try:
            job_id = int(payload['job_id'])
        except (TypeError, ValueError):
            return {'success': False, 'error': 'Invalid job position.'}

        job = request.env['hr.job'].sudo().browse(job_id)
        if not job.exists() or not job.website_published:
            return {'success': False, 'error': 'Invalid job position.'}

        applicant = request.env['hr.applicant'].sudo().create({
            'name': f"{payload['name']} — {job.name}",
            'partner_name': payload['name'],
            'email_from': payload['email'],
            'partner_phone': payload.get('phone'),
            'job_id': job.id,
            'department_id': job.department_id.id,
            'years_experience': payload.get('years_experience') or 0,
            'nursing_license_number': payload.get('nursing_license_number'),
            'references': payload.get('references'),
            'description': payload.get('message'),
        })

        if payload.get('cv_base64') and payload.get('cv_filename'):
            try:
                cv_data = base64.b64decode(payload['cv_base64'], validate=True)
            except (ValueError, binascii.Error):
                return {'success': False, 'error': 'Invalid CV file.'}
            request.env['ir.attachment'].sudo().create({
                'name': payload['cv_filename'],
                'datas': base64.b64encode(cv_data),
                'res_model': 'hr.applicant',
                'res_id': applicant.id,
                'mimetype': 'application/pdf',
            })

        return {'success': True, 'id': applicant.id}
