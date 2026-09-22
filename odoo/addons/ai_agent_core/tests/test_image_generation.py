# -*- coding: utf-8 -*-
import base64
import json
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

REQUESTS = 'odoo.addons.ai_agent_core.models.ai_provider_config.requests'

# Cuerpo real de la API de Gemini para una API key en el nivel gratuito
# pidiendo un modelo de imagen (recortado a lo que se usa).
GEMINI_FREE_TIER_429 = {
    'error': {
        'code': 429,
        'message': (
            'You exceeded your current quota, please check your plan and '
            'billing details.\n* Quota exceeded for metric: '
            'generativelanguage.googleapis.com/generate_content_free_tier_requests, '
            'limit: 0, model: gemini-2.5-flash-preview-image\nPlease retry in 20.0s.'
        ),
        'status': 'RESOURCE_EXHAUSTED',
        'details': [
            {
                '@type': 'type.googleapis.com/google.rpc.QuotaFailure',
                'violations': [{
                    'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests',
                    'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier',
                }],
            },
            {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '20s'},
        ],
    }
}


def fake_response(status, payload):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = payload
    response.text = json.dumps(payload)
    return response


@tagged('post_install', '-at_install')
class TestImageGeneration(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Config = cls.env['ai.provider.config']
        cls.gemini = Config.create({'name': 'Gemini test', 'provider': 'google', 'api_key': 'k'})
        cls.claude = Config.create({'name': 'Claude test', 'provider': 'anthropic', 'api_key': 'k'})
        cls.ollama = Config.create({
            'name': 'Ollama test', 'provider': 'ollama',
            'ollama_mode': 'local', 'base_url': 'http://ollama:11434',
        })

    def _set_image_model(self, config, model_id):
        config.image_model_name_id = self.env['ai.provider.available.model'].create({
            'provider_config_id': config.id, 'model_id': model_id,
            'name': model_id, 'kind': 'image',
        })

    def _kinds(self, config):
        models = self.env['ai.provider.available.model'].with_context(active_test=False).search(
            [('provider_config_id', '=', config.id)]
        )
        return {(m.model_id, m.kind) for m in models}

    # ---------------------------------------------------------------- catálogo

    def test_gemini_catalog_classifies_image_models(self):
        listing = {'models': [
            {'name': 'models/gemini-3.5-flash', 'supportedGenerationMethods': ['generateContent']},
            {'name': 'models/gemini-3.1-flash-image', 'supportedGenerationMethods': ['generateContent']},
            {'name': 'models/nano-banana-pro-preview', 'supportedGenerationMethods': ['generateContent']},
            {'name': 'models/imagen-4.0-generate-001', 'supportedGenerationMethods': ['predict']},
            {'name': 'models/veo-3.1-generate-preview', 'supportedGenerationMethods': ['predictLongRunning']},
            {'name': 'models/gemini-embedding-001', 'supportedGenerationMethods': ['embedContent']},
        ]}
        with patch(REQUESTS + '.get', return_value=fake_response(200, listing)):
            self.gemini._fetch_available_models()
        self.assertEqual(self._kinds(self.gemini), {
            ('gemini-3.5-flash', 'text'),
            ('gemini-3.1-flash-image', 'image'),
            ('nano-banana-pro-preview', 'image'),
            ('imagen-4.0-generate-001', 'image'),
        })

    def test_svg_providers_register_text_models_as_image_models(self):
        listing = {'data': [{'id': 'claude-sonnet-5', 'display_name': 'Claude Sonnet 5'}]}
        with patch(REQUESTS + '.get', return_value=fake_response(200, listing)):
            self.claude._fetch_available_models()
        self.assertEqual(self._kinds(self.claude), {
            ('claude-sonnet-5', 'text'), ('claude-sonnet-5', 'image'),
        })

    # ----------------------------------------------------------------- errores

    def test_gemini_free_tier_error_explains_billing(self):
        self._set_image_model(self.gemini, 'gemini-2.5-flash-image')
        with patch(REQUESTS + '.post', return_value=fake_response(429, GEMINI_FREE_TIER_429)):
            with self.assertRaises(UserError) as caught:
                self.gemini.generate_image('un salón de belleza')
        message = str(caught.exception)
        self.assertIn('nivel gratuito', message)
        self.assertIn('facturación', message)
        self.assertIn('gemini-2.5-flash-image', message)
        self.assertNotIn('@type', message, 'No debe volcar el JSON crudo de la API')

    def test_gemini_rate_limit_with_quota_left_suggests_waiting(self):
        payload = json.loads(json.dumps(GEMINI_FREE_TIER_429))
        payload['error']['message'] = payload['error']['message'].replace('limit: 0', 'limit: 10')
        self._set_image_model(self.gemini, 'gemini-2.5-flash-image')
        with patch(REQUESTS + '.post', return_value=fake_response(429, payload)):
            with self.assertRaises(UserError) as caught:
                self.gemini.generate_image('x')
        self.assertIn('Reintenta en 20s', str(caught.exception))

    # ------------------------------------------------------------------ Imagen

    def test_imagen_goes_through_predict(self):
        self._set_image_model(self.gemini, 'imagen-4.0-generate-001')
        body = {'predictions': [{'bytesBase64Encoded': 'QUJD', 'mimeType': 'image/png'}]}
        with patch(REQUESTS + '.post', return_value=fake_response(200, body)) as post:
            result = self.gemini.generate_image('una manzana')
        self.assertEqual(result, ('QUJD', 'ai_generated.png'))
        self.assertTrue(post.call_args.args[0].endswith('imagen-4.0-generate-001:predict'))
        self.assertEqual(post.call_args.kwargs['json']['instances'], [{'prompt': 'una manzana'}])

    # --------------------------------------------------------------------- SVG

    def test_sanitize_svg_strips_active_and_external_content(self):
        raw = """Aquí tienes:
```svg
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="540" height="540" onload="alert(1)">
  <defs><linearGradient id="g"><stop offset="0" stop-color="teal"/></linearGradient></defs>
  <style>@import url(http://evil/x.css);</style>
  <script>alert(1)</script>
  <foreignObject><div>hola</div></foreignObject>
  <image href="http://169.254.169.254/latest"/>
  <rect width="10" height="10" fill="url(#g)"/>
  <rect width="10" height="10" fill="url('#g')"/>
  <rect width="10" height="10" style="fill:url(http://evil/p)"/>
  <use xlink:href="http://evil/s.svg#a"/>
  <use href="#g"/>
  <text>Salón&nbsp;Natural</text>
</svg>
```"""
        svg = self.env['ai.provider.config']._sanitize_svg(raw)
        for forbidden in ('onload', '<script', 'foreignObject', '<image', '@import', 'evil', '169.254'):
            self.assertNotIn(forbidden, svg)
        self.assertEqual(svg.count('url(#g)') + svg.count("url('#g')"), 2)
        self.assertIn('href="#g"', svg)
        self.assertIn('viewBox="0 0 540 540"', svg)
        self.assertIn('width="1080"', svg)
        self.assertIn('Salón\xa0Natural', svg)

    def test_truncated_svg_is_reported_as_cut(self):
        with self.assertRaisesRegex(UserError, 'cortada'):
            self.env['ai.provider.config']._sanitize_svg('<svg xmlns="http://www.w3.org/2000/svg"><rect')

    def test_claude_draws_svg_and_returns_jpg(self):
        self._set_image_model(self.claude, 'claude-sonnet-5')
        body = {'content': [{'type': 'text', 'text': (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1080">'
            '<rect width="1080" height="1080" fill="teal"/></svg>'
        )}]}
        Report = type(self.env['ir.actions.report'])
        with patch(REQUESTS + '.post', return_value=fake_response(200, body)) as post, \
                patch.object(Report, '_run_wkhtmltoimage', return_value=[b'JPEGDATA']) as render:
            data, filename = self.claude.generate_image('promo de verano')
        self.assertEqual((base64.b64decode(data), filename), (b'JPEGDATA', 'ai_generated.jpg'))
        payload = post.call_args.kwargs['json']
        self.assertEqual(payload['model'], 'claude-sonnet-5')
        self.assertGreater(payload['max_tokens'], 1024)
        self.assertIn('SVG', payload['system'])
        html, width, height = render.call_args.args[0][0], render.call_args.args[1], render.call_args.args[2]
        self.assertIn('<rect', html)
        self.assertEqual((width, height), (1080, 1080))

    def test_local_ollama_draws_svg_without_api_key(self):
        self._set_image_model(self.ollama, 'gemma4:31b')
        body = {'message': {'content': '<svg xmlns="http://www.w3.org/2000/svg"><circle r="5"/></svg>'}}
        Report = type(self.env['ir.actions.report'])
        with patch(REQUESTS + '.post', return_value=fake_response(200, body)) as post, \
                patch.object(Report, '_run_wkhtmltoimage', return_value=[b'JPEGDATA']):
            data, filename = self.ollama.generate_image('logo')
        self.assertEqual(filename, 'ai_generated.jpg')
        self.assertTrue(post.call_args.args[0].startswith('http://ollama:11434/api/chat'))
