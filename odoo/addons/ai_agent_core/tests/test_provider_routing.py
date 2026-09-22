# -*- coding: utf-8 -*-
"""Enrutamiento de los proveedores compatibles con OpenAI sobre un único
adaptador, catálogo, costo auditado y health check."""
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.ai_agent_core.llm.registry import PROVIDER_REGISTRY

from .common import REQUESTS, chat_ok, fake_response

OPENAI_COMPATIBLE = ('openai', 'groq', 'deepseek', 'mistral', 'openrouter', 'abacus')


@tagged('post_install', '-at_install')
class TestProviderRouting(TransactionCase):

    def _provider(self, code, **vals):
        return self.env['ai.provider.config'].create(dict({
            'name': 'Test %s' % code, 'provider': code, 'api_key': 'k-%s' % code,
            'use_local_fallback': False,
        }, **vals))

    def _audits(self, provider):
        return self.env['ai.audit.log'].search(
            [('provider_config_id', '=', provider.id)], order='id')

    def test_every_openai_compatible_provider_uses_the_same_adapter(self):
        for code in OPENAI_COMPATIBLE:
            provider = self._provider(code)
            with patch(REQUESTS + '.post', return_value=chat_ok('hola %s' % code)) as post:
                self.assertEqual(provider.generate_content('hola'), 'hola %s' % code)
            url = post.call_args.args[0]
            headers = post.call_args.kwargs['headers']
            self.assertEqual(url, PROVIDER_REGISTRY[code]['base_url'] + '/chat/completions', code)
            self.assertEqual(headers['Authorization'], 'Bearer k-%s' % code)
            self.assertEqual(post.call_args.kwargs['json']['model'],
                             PROVIDER_REGISTRY[code]['default_model'])
            self.assertEqual(headers.get('X-Title') is not None, code == 'openrouter')

    def test_base_url_can_point_to_a_proxy(self):
        provider = self._provider('groq', base_url='https://proxy.interno/groq/v1/')
        with patch(REQUESTS + '.post', return_value=chat_ok()) as post:
            provider.generate_content('x')
        self.assertEqual(post.call_args.args[0], 'https://proxy.interno/groq/v1/chat/completions')

    def test_empty_system_prompt_is_not_sent(self):
        provider = self._provider('mistral', system_prompt=False)
        with patch(REQUESTS + '.post', return_value=chat_ok()) as post:
            provider.generate_content('x')
        roles = [m['role'] for m in post.call_args.kwargs['json']['messages']]
        self.assertEqual(roles, ['user'])

    # ---------------------------------------------------------- costo

    def test_tokens_and_cost_are_audited_from_the_spec(self):
        provider = self._provider('deepseek')  # deepseek-flash: 0.30 / 1.20 USD por 1M
        with patch(REQUESTS + '.post', return_value=chat_ok(prompt_tokens=1000, completion_tokens=2000)):
            provider.generate_content('x')
        log = self._audits(provider)
        self.assertEqual(len(log), 1)
        self.assertEqual((log.event_type, log.model_name, log.input_tokens, log.output_tokens, log.total_tokens),
                         ('llm_call', 'deepseek-flash', 1000, 2000, 3000))
        self.assertAlmostEqual(log.cost_usd, (1000 * 0.30 + 2000 * 1.20) / 1_000_000)
        self.assertEqual(log.cost_source, 'spec')

    def test_cost_reported_by_openrouter_wins(self):
        provider = self._provider('openrouter')
        with patch(REQUESTS + '.post', return_value=chat_ok(cost=0.0042)):
            provider.generate_content('x')
        log = self._audits(provider)
        self.assertEqual((log.cost_usd, log.cost_source), (0.0042, 'provider'))

    def test_unknown_price_is_not_logged_as_free(self):
        provider = self._provider('groq')
        provider.model_name_id = self.env['ai.provider.available.model'].create({
            'provider_config_id': provider.id, 'model_id': 'llama-3.3-70b-versatile',
            'name': 'llama', 'kind': 'text',
        })
        with patch(REQUESTS + '.post', return_value=chat_ok()):
            provider.generate_content('x')
        self.assertEqual(self._audits(provider).cost_source, 'unknown')

    # -------------------------------------------------------- catálogo

    def test_groq_catalog_is_not_filtered_with_openai_rules(self):
        provider = self._provider('groq')
        listing = {'data': [
            {'id': 'llama-3.3-70b-versatile', 'active': True, 'context_window': 131072},
            {'id': 'openai/gpt-oss-120b', 'active': True, 'context_window': 131072},
            {'id': 'whisper-large-v3', 'active': True},
            {'id': 'meta-llama/llama-prompt-guard-2-22m', 'active': True},
            {'id': 'viejo-modelo', 'active': False},
        ]}
        with patch(REQUESTS + '.get', return_value=fake_response(200, listing)) as get:
            provider._fetch_available_models()
        self.assertEqual(get.call_args.args[0], 'https://api.groq.com/openai/v1/models')
        texts = provider.available_model_ids.filtered(lambda m: m.kind == 'text').mapped('model_id')
        self.assertEqual(sorted(texts), ['llama-3.3-70b-versatile', 'openai/gpt-oss-120b'])
        self.assertTrue(provider.available_model_ids.filtered(lambda m: m.kind == 'image'),
                        'Groq dibuja imágenes en SVG con sus modelos de texto')

    def test_openrouter_catalog_creates_specs_with_price_and_free_limits(self):
        provider = self._provider('openrouter')
        listing = {'data': [
            {'id': 'acme/modelo', 'name': 'Acme', 'context_length': 200000,
             'pricing': {'prompt': '0.000001', 'completion': '0.000004'},
             'architecture': {'output_modalities': ['text']}, 'supported_parameters': ['tools']},
            {'id': 'acme/modelo:free', 'context_length': 32000,
             'pricing': {'prompt': '0', 'completion': '0'},
             'architecture': {'output_modalities': ['text']}},
            {'id': 'openrouter/auto', 'pricing': {'prompt': '-1', 'completion': '-1'}},
            {'id': 'acme/imagen', 'architecture': {'output_modalities': ['image']}},
        ]}
        with patch(REQUESTS + '.get', return_value=fake_response(200, listing)):
            provider._fetch_available_models()
        Spec = self.env['ai.model.spec']
        paid = Spec._lookup('openrouter', 'acme/modelo')
        self.assertEqual((paid.context_window, paid.input_cost_per_mtok, paid.output_cost_per_mtok,
                          paid.supports_tools, paid.pricing_known, paid.source),
                         (200000, 1.0, 4.0, True, True, 'api'))
        free = Spec._lookup('openrouter', 'acme/modelo:free')
        self.assertEqual((free.free_rpm, free.free_rpd, free.pricing_known, free._estimate_cost(10, 10)),
                         (20, 50, True, 0.0))
        self.assertFalse(Spec._lookup('openrouter', 'openrouter/auto').pricing_known)
        self.assertFalse(Spec._lookup('openrouter', 'acme/imagen'))

    def test_api_fills_gaps_but_never_overwrites_a_verified_price(self):
        provider = self._provider('mistral')
        listing = {'data': [{'id': 'mistral-large-latest', 'name': 'Large', 'max_context_length': 256000,
                             'capabilities': {'completion_chat': True, 'function_calling': True}}]}
        with patch(REQUESTS + '.get', return_value=fake_response(200, listing)):
            provider._fetch_available_models()
        spec = self.env['ai.model.spec']._lookup('mistral', 'mistral-large-latest')
        self.assertEqual((spec.context_window, spec.input_cost_per_mtok, spec.source),
                         (256000, 0.5, 'official'))

    # ---------------------------------------------------- health check

    def test_health_check_never_calls_a_generation_endpoint(self):
        expected = {
            'openai': ('https://api.openai.com/v1/models', 'Authorization'),
            'groq': ('https://api.groq.com/openai/v1/models', 'Authorization'),
            'deepseek': ('https://api.deepseek.com/user/balance', 'Authorization'),
            'mistral': ('https://api.mistral.ai/v1/models', 'Authorization'),
            'openrouter': ('https://openrouter.ai/api/v1/key', 'Authorization'),
            'abacus': ('https://routellm.abacus.ai/api/v0/describeUser', 'apiKey'),
        }
        for code, (url, auth_header) in expected.items():
            provider = self._provider(code)
            with patch(REQUESTS + '.get', return_value=fake_response(200, {'data': []})) as get, \
                    patch(REQUESTS + '.post') as post:
                provider.action_health_check()
            post.assert_not_called()
            self.assertEqual(get.call_args.args[0], url, code)
            self.assertIn(auth_header, get.call_args.kwargs['headers'])
            self.assertEqual(provider.health_state, 'ok', code)
            health_log = self._audits(provider)
            self.assertEqual((health_log.event_type, health_log.total_tokens), ('health_check', 0))

    def test_health_check_detects_geoblock_and_pauses_provider(self):
        provider = self._provider('groq')
        body = {'error': {'message': 'Access denied. Please check your network settings.'}}
        with patch(REQUESTS + '.get', return_value=fake_response(403, body)):
            provider.action_health_check()
        self.assertEqual((provider.health_state, provider.last_error_kind), ('error', 'geoblocked'))
        self.assertTrue(provider.unavailable_until)
