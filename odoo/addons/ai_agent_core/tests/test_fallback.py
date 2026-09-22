# -*- coding: utf-8 -*-
"""Reintento ante 429 y cadena de fallback.

Cada proveedor responde según su URL, con una cola de respuestas: así se
ve exactamente a quién se llamó, cuántas veces y en qué orden.
"""
from unittest.mock import patch

import requests

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from .common import REQUESTS, chat_ok, fake_response, ollama_ok

GROQ = 'https://api.groq.com/openai/v1/chat/completions'
DEEPSEEK = 'https://api.deepseek.com/chat/completions'
MISTRAL = 'https://api.mistral.ai/v1/chat/completions'
OLLAMA = 'http://ollama-local:11434/api/chat'


@tagged('post_install', '-at_install')
class TestFallback(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Config = cls.env['ai.provider.config']
        # Aislamiento: un Ollama local de la base no debe colarse en la cadena.
        Config.search([]).write({'active': False})
        cls.local = Config.create({
            'name': 'Ollama local', 'provider': 'ollama', 'ollama_mode': 'local',
            'base_url': 'http://ollama-local:11434', 'sequence': 99,
        })
        cls.deepseek = Config.create({
            'name': 'DeepSeek', 'provider': 'deepseek', 'api_key': 'k-ds', 'use_local_fallback': False,
        })
        cls.groq = Config.create({
            'name': 'Groq', 'provider': 'groq', 'api_key': 'k-groq',
            'fallback_provider_id': cls.deepseek.id, 'max_retries': 3,
        })
        cls.Provider = type(Config)

    def setUp(self):
        super().setUp()
        self.calls = []
        self.queues = {}
        self.sleeps = []
        post_patcher = patch(REQUESTS + '.post', side_effect=self._route)
        sleep_patcher = patch.object(self.Provider, '_sleep', autospec=True,
                                     side_effect=lambda rec, seconds: self.sleeps.append(seconds))
        post_patcher.start()
        sleep_patcher.start()
        self.addCleanup(post_patcher.stop)
        self.addCleanup(sleep_patcher.stop)

    def _route(self, url, **kwargs):
        self.calls.append(url)
        queue = self.queues.get(url)
        if not queue:
            raise AssertionError('Llamada inesperada a %s' % url)
        answer = queue.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    def _audits(self, provider=None):
        domain = [('event_type', '=', 'llm_call')]
        if provider:
            domain.append(('provider_config_id', '=', provider.id))
        return self.env['ai.audit.log'].search(domain, order='id')

    # ------------------------------------------------------------ reintentos

    def test_429_is_retried_with_backoff_then_succeeds(self):
        self.queues[GROQ] = [
            fake_response(429, {'error': {'message': 'Rate limit reached'}}, headers={'retry-after': '2'}),
            fake_response(429, {'error': {'message': 'Rate limit reached'}}),
            chat_ok('al tercer intento'),
        ]
        self.assertEqual(self.groq.generate_content('x'), 'al tercer intento')
        self.assertEqual(self.calls, [GROQ] * 3)
        self.assertEqual(len(self.sleeps), 2)
        self.assertTrue(2.0 <= self.sleeps[0] <= 3.0, 'respeta Retry-After: %s' % self.sleeps[0])
        self.assertTrue(0.0 <= self.sleeps[1] <= 2.0, 'backoff con jitter: %s' % self.sleeps[1])
        logs = self._audits(self.groq)
        self.assertEqual(logs.mapped('attempt'), [1, 2, 3])
        self.assertEqual(logs.mapped('status'), ['error', 'error', 'success'])
        self.assertEqual(logs[0].error_kind, 'rate_limited')

    def test_429_exhausted_degrades_to_the_configured_fallback(self):
        self.groq.max_retries = 1
        limited = fake_response(429, {'error': {'message': 'Rate limit reached'}})
        self.queues[GROQ] = [limited, limited]
        self.queues[DEEPSEEK] = [chat_ok('desde deepseek')]
        self.assertEqual(self.groq.generate_content('x'), 'desde deepseek')
        self.assertEqual(self.calls, [GROQ, GROQ, DEEPSEEK])
        served = self._audits(self.deepseek)
        self.assertEqual((served.status, served.fallback_from_id), ('success', self.groq))

    def test_retry_after_longer_than_the_budget_degrades_without_waiting(self):
        self.queues[GROQ] = [fake_response(429, {'error': {'message': 'slow down'}}, headers={'retry-after': '600'})]
        self.queues[DEEPSEEK] = [chat_ok('sin esperar')]
        self.assertEqual(self.groq.generate_content('x'), 'sin esperar')
        self.assertEqual(self.sleeps, [])
        self.assertTrue(self.groq.unavailable_until, 'queda en pausa lo que pidió el proveedor')

    def test_exhausted_quota_is_not_retried(self):
        self.queues[GROQ] = [fake_response(402, {'error': {'message': 'Insufficient Balance'}})]
        self.queues[DEEPSEEK] = [chat_ok('ok')]
        self.groq.generate_content('x')
        self.assertEqual((self.sleeps, self.calls), ([], [GROQ, DEEPSEEK]))
        self.assertEqual(self.groq.last_error_kind, 'quota_exhausted')

    # -------------------------------------------------------------- fallback

    def test_expired_key_pauses_provider_and_next_call_skips_it(self):
        self.queues[GROQ] = [fake_response(401, {'error': {'message': 'Invalid API Key'}})]
        self.queues[DEEPSEEK] = [chat_ok('uno'), chat_ok('dos')]
        self.assertEqual(self.groq.generate_content('x'), 'uno')
        self.assertTrue(self.groq.unavailable_until)
        self.assertEqual(self.groq.generate_content('x'), 'dos')
        self.assertEqual(self.calls, [GROQ, DEEPSEEK, DEEPSEEK], 'la segunda no insiste en Groq')

    def test_recovery_clears_the_pause(self):
        self.groq.write({'unavailable_until': '2000-01-01 00:00:00', 'last_error_kind': 'unavailable'})
        self.queues[GROQ] = [chat_ok('volvió')]
        self.groq.generate_content('x')
        self.assertFalse(self.groq.unavailable_until or self.groq.last_error_kind)

    def test_bad_request_does_not_degrade(self):
        self.queues[GROQ] = [fake_response(400, {'error': {'message': 'messages: field required'}})]
        with self.assertRaises(UserError):
            self.groq.generate_content('x')
        self.assertEqual(self.calls, [GROQ], 'otro proveedor fallaría igual: no se degrada')

    def test_no_network_ends_in_local_ollama(self):
        lonely = self.env['ai.provider.config'].create({
            'name': 'Mistral sin cadena', 'provider': 'mistral', 'api_key': 'k-m',
        })
        self.queues[MISTRAL] = [requests.exceptions.ConnectionError('sin red')]
        self.queues[OLLAMA] = [ollama_ok('último recurso')]
        self.assertEqual(lonely.generate_content('x'), 'último recurso')
        self.assertEqual(self.calls, [MISTRAL, OLLAMA])
        self.assertEqual(self._audits(self.local).fallback_from_id, lonely)

    def test_external_facing_agent_only_degrades_to_local_ollama(self):
        self.queues[GROQ] = [fake_response(503, 'Service Unavailable')]
        self.queues[OLLAMA] = [ollama_ok('local')]
        answer = self.groq.with_context(ai_external_facing=True).generate_content('dato de un cliente')
        self.assertEqual(answer, 'local')
        self.assertNotIn(DEEPSEEK, self.calls, 'los datos del cliente no van a otro tercero')

    def test_agent_passes_its_context_to_the_provider(self):
        agent = self.env['ai.agent'].create({
            'name': 'Agente de prueba', 'code': 'test_fallback_agent', 'ai_provider_id': self.groq.id,
        })
        provider = agent.get_provider()
        self.assertEqual(provider.env.context.get('ai_agent_id'), agent.id)
        self.queues[GROQ] = [chat_ok('ok')]
        provider.generate_content('x')
        self.assertEqual(self._audits(self.groq).agent_id, agent)

    def test_cycle_in_the_chain_ends_and_reports_every_failure(self):
        self.deepseek.fallback_provider_id = self.groq
        self.groq.use_local_fallback = False
        self.queues[GROQ] = [fake_response(503, 'caído')]
        self.queues[DEEPSEEK] = [fake_response(503, 'caído')]
        with self.assertRaises(UserError) as caught:
            self.groq.generate_content('x')
        self.assertEqual(self.calls, [GROQ, DEEPSEEK])
        self.assertIn('Groq', str(caught.exception))
        self.assertIn('DeepSeek', str(caught.exception))

    def test_failed_calls_are_audited(self):
        self.groq.use_local_fallback = False
        self.deepseek.fallback_provider_id = False
        self.queues[GROQ] = [fake_response(403, {'error': {'message': 'Access denied. Please check your network settings.'}})]
        self.queues[DEEPSEEK] = [fake_response(402, {'error': {'message': 'Insufficient Balance'}})]
        # Sin assertRaises: el de Odoo abre un savepoint y lo revierte, y en
        # tests la auditoría usa el cursor del test. En producción va por un
        # cursor propio que sobrevive al rollback (_isolated_env), algo que
        # un test transaccional no puede observar sin confirmar datos.
        try:
            self.groq.generate_content('x')
            self.fail('debió fallar toda la cadena')
        except UserError:
            pass
        kinds = self._audits().mapped(lambda log: (log.provider_config_id.name, log.status, log.error_kind))
        self.assertEqual(kinds, [('Groq', 'error', 'geoblocked'), ('DeepSeek', 'error', 'quota_exhausted')])
