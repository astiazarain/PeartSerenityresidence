# -*- coding: utf-8 -*-
"""Clasificación de fallos con cuerpos reales de cada API.

Los de Groq, Abacus, DeepSeek y Mistral se capturaron el 2026-09-12 contra
las APIs reales, con claves inválidas y desde una red que Groq bloquea: son
el motivo de que el tipo no se decida solo por el código HTTP.
"""
from odoo.tests import TransactionCase, tagged

from odoo.addons.ai_agent_core.llm import errors
from odoo.addons.ai_agent_core.llm.errors import backoff_delay, classify_http_error, parse_retry_after

from .common import fake_response

GEMINI_429_LIMIT_0 = (
    '{"error": {"code": 429, "message": "You exceeded your current quota... '
    'generate_content_free_tier_requests, limit: 0, model: gemini-2.5-flash-image\\n'
    'Please retry in 20.0s.", "details": [{"@type": "type.googleapis.com/google.rpc.RetryInfo", '
    '"retryDelay": "20s"}]}}'
)


@tagged('post_install', '-at_install')
class TestErrorClassification(TransactionCase):

    def assertKind(self, status, body, expected, headers=None):
        kind, _retry = classify_http_error(status, body, headers)
        self.assertEqual(kind, expected, 'HTTP %s %s' % (status, body[:80]))

    def test_same_403_is_geoblock_or_bad_key_depending_on_body(self):
        # Groq desde una red bloqueada vs Abacus con clave inválida: ambos 403.
        self.assertKind(403, '{"error":{"message":"Access denied. Please check your network settings."}}',
                        errors.GEOBLOCKED)
        self.assertKind(403, '{"success": false, "error": "Invalid API Key", '
                             '"errorType": "GenericPermissionDeniedError"}', errors.AUTH)

    def test_invalid_keys(self):
        self.assertKind(401, '{"error":{"message":"Authentication Fails, Your api key: ****alid is invalid",'
                             '"type":"authentication_error"}}', errors.AUTH)  # DeepSeek
        self.assertKind(401, '{"detail":"Invalid API Key"}', errors.AUTH)  # Mistral
        self.assertKind(400, '{"error": {"message": "API key not valid. Please pass a valid API key."}}',
                        errors.AUTH)  # Gemini devuelve 400

    def test_quota_exhausted_is_not_a_transient_rate_limit(self):
        self.assertKind(429, GEMINI_429_LIMIT_0, errors.QUOTA_EXHAUSTED)
        self.assertKind(429, '{"error": {"code": "insufficient_quota", "message": "You exceeded your current quota"}}',
                        errors.QUOTA_EXHAUSTED)  # OpenAI
        self.assertKind(402, '{"error": {"message": "Insufficient credits"}}', errors.QUOTA_EXHAUSTED)  # OpenRouter
        self.assertKind(400, '{"error": {"type": "invalid_request_error", "message": '
                             '"Your credit balance is too low to access the Anthropic API."}}',
                        errors.QUOTA_EXHAUSTED)

    def test_transient_rate_limit_keeps_retry_delay(self):
        body = GEMINI_429_LIMIT_0.replace('limit: 0', 'limit: 10')
        kind, retry = classify_http_error(429, body)
        self.assertEqual((kind, retry), (errors.RATE_LIMITED, 20.0))

    def test_geoblock_unavailable_model_and_bad_request(self):
        self.assertKind(400, '{"error": {"message": "User location is not supported for the API use."}}',
                        errors.GEOBLOCKED)  # Gemini
        self.assertKind(403, '{"error": {"code": "unsupported_country_region_territory"}}', errors.GEOBLOCKED)
        self.assertKind(529, '{"type": "error", "error": {"type": "overloaded_error"}}', errors.UNAVAILABLE)
        self.assertKind(503, 'Service Unavailable', errors.UNAVAILABLE)
        self.assertKind(404, '{"error": {"message": "The model `x` does not exist"}}', errors.MODEL_UNAVAILABLE)
        self.assertKind(400, '{"error": {"message": "messages: field required"}}', errors.BAD_REQUEST)

    def test_retry_after_header_seconds_and_http_date(self):
        self.assertEqual(parse_retry_after({'Retry-After': '7'}), 7.0)
        self.assertEqual(parse_retry_after({'retry-after': 'Wed, 21 Oct 2015 07:28:00 GMT'}), 0.0)
        self.assertIsNone(parse_retry_after({'Retry-After': 'basura'}))
        self.assertIsNone(parse_retry_after(None, ''))

    def test_backoff_is_exponential_capped_and_jittered(self):
        top = lambda: 1.0  # noqa: E731 — rng que devuelve el máximo del rango
        self.assertEqual(backoff_delay(0, rng=top), 1.0)
        self.assertEqual(backoff_delay(2, rng=top), 4.0)
        self.assertEqual(backoff_delay(10, rng=top), 8.0, 'tope')
        self.assertEqual(backoff_delay(3, rng=lambda: 0.0), 0.0, 'full jitter llega a 0')
        self.assertEqual(backoff_delay(0, retry_after=5, rng=lambda: 0.5), 5.5, 'respeta Retry-After')

    def test_error_text_reads_every_format(self):
        self.assertEqual(errors.error_text(fake_response(401, {'detail': 'Invalid API Key'})), 'Invalid API Key')
        self.assertEqual(errors.error_text(fake_response(403, {'error': 'Invalid API Key'})), 'Invalid API Key')
        self.assertEqual(errors.error_text(fake_response(400, {'error': {'message': 'm'}})), 'm')
        self.assertEqual(errors.error_text(fake_response(502, 'Bad gateway')), 'Bad gateway')
