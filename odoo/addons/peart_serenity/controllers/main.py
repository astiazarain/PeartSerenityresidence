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


class PeartSerenityCareAPI(http.Controller):
    # Public JSON-RPC API consumed by the website (project/src/lib/odoo.ts).
    # Routes are called as JSON-RPC (POST body: {jsonrpc, method, params})
    # and run as the public user; each one elevates to sudo() explicitly and
    # only after validating its own inputs - visitors are never given direct
    # model access.

    @http.route('/api/care-quote', type='jsonrpc', auth='public', methods=['POST'])
    def submit_care_quote(self, **payload):
        missing = [f for f in CARE_QUOTE_REQUIRED_FIELDS if not payload.get(f)]
        if missing:
            return {'success': False, 'error': f"Missing required fields: {', '.join(missing)}"}

        vals = {k: v for k, v in payload.items() if k in CARE_QUOTE_ALLOWED_FIELDS}
        admission = request.env['peart.admission'].sudo().create(vals)
        return {'success': True, 'id': admission.id}

    @http.route('/api/register-contact', type='jsonrpc', auth='public', methods=['POST'])
    def register_contact(self, **payload):
        name = payload.get('name')
        email = payload.get('email')
        phone = payload.get('phone')
        if not name or not email:
            return {'success': False, 'error': 'name and email are required'}

        partner = request.env['res.partner'].sudo().peart_find_or_create(name, email=email, phone=phone)
        return {'success': True, 'id': partner.id}
