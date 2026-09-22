import base64

from odoo import http
from odoo.http import request

NOT_FOUND = {'success': False, 'error': 'not_found'}


def _lang(payload):
    return 'es' if payload.get('lang') == 'es' else 'en'


class PeartFamilyPortal(http.Controller):
    """Family portal API. Every route requires a logged-in portal user and
    resolves the resident through peart.resident._portal_resident, which is
    subject to the record rule (enabled family link only). A resident that
    does not exist and one that is not yours are indistinguishable."""

    def _resident(self, payload):
        return request.env['peart.resident']._portal_resident(request.env.user, payload.get('resident_id'))

    @http.route('/api/my/residents', type='jsonrpc', auth='user', methods=['POST'])
    def my_residents(self, **payload):
        return {'success': True, 'records': request.env['peart.resident']._portal_my_residents(request.env.user)}

    @http.route('/api/my/resident/summary', type='jsonrpc', auth='user', methods=['POST'])
    def resident_summary(self, **payload):
        resident = self._resident(payload)
        if not resident:
            return NOT_FOUND
        resident._portal_log(request.env.user, 'summary')
        return {'success': True, 'resident': resident.portal_summary(_lang(payload))}

    @http.route('/api/my/resident/timeline', type='jsonrpc', auth='user', methods=['POST'])
    def resident_timeline(self, **payload):
        resident = self._resident(payload)
        if not resident:
            return NOT_FOUND
        resident._portal_log(request.env.user, 'timeline')
        return {'success': True, **resident.portal_timeline(
            payload.get('offset', 0), payload.get('limit', 20), _lang(payload))}

    @http.route('/api/my/resident/record', type='jsonrpc', auth='user', methods=['POST'])
    def resident_record(self, **payload):
        resident = self._resident(payload)
        if not resident:
            return NOT_FOUND
        resident._portal_log(request.env.user, 'record')
        return {'success': True, **resident.portal_record(_lang(payload))}

    @http.route('/api/my/resident/documents', type='jsonrpc', auth='user', methods=['POST'])
    def resident_documents(self, **payload):
        resident = self._resident(payload)
        if not resident:
            return NOT_FOUND
        resident._portal_log(request.env.user, 'documents')
        return {'success': True, 'records': resident.portal_documents(_lang(payload))}

    @http.route('/api/my/resident/document/<int:document_id>', type='http', auth='user', methods=['GET'])
    def resident_document(self, document_id, **kw):
        doc = request.env['peart.resident.document'].sudo().browse(document_id).exists()
        resident = request.env['peart.resident']._portal_resident(
            request.env.user, doc.resident_id.id) if doc else False
        if not (doc and resident and doc.family_visible):
            return request.not_found()
        resident._portal_log(request.env.user, 'download', detail=doc.name)
        content = base64.b64decode(doc.file or b'')
        filename = (doc.filename or doc.name or 'document').replace('"', '')
        return request.make_response(content, headers=[
            ('Content-Type', 'application/octet-stream'),
            ('Content-Disposition', f'attachment; filename="{filename}"'),
            ('X-Content-Type-Options', 'nosniff'),
            ('Cache-Control', 'private, no-store'),
        ])

    @http.route('/api/my/resident/aria', type='jsonrpc', auth='user', methods=['POST'])
    def resident_aria(self, **payload):
        resident = self._resident(payload)
        if not resident:
            return NOT_FOUND
        if not resident.has_consent('ai_assistant'):
            return {'success': False, 'error': 'ai_consent_missing'}
        history = payload.get('history') if isinstance(payload.get('history'), list) else []
        result = resident.portal_ask_aria(
            request.env.user, payload.get('message'), history=history, lang=_lang(payload))
        return {'success': True, **result}
