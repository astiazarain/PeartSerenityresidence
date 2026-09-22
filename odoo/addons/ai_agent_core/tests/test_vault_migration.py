# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged
from odoo.tools.sql import column_exists

from odoo.addons.ai_agent_core.llm.migration import (
    LEGACY_COLUMN,
    encrypt_legacy_api_keys,
    reset_legacy_base_urls,
)
from odoo.addons.ai_agent_core.llm.registry import LEGACY_BASE_URL_DEFAULT

from .common import REQUESTS, ollama_ok


@tagged('post_install', '-at_install')
class TestVaultAndMigration(TransactionCase):

    def _stored(self, provider):
        self.env.flush_all()
        self.env.cr.execute('SELECT api_key_encrypted FROM ai_provider_config WHERE id = %s', (provider.id,))
        return self.env.cr.fetchone()[0]

    def test_api_key_is_stored_only_encrypted(self):
        provider = self.env['ai.provider.config'].create({
            'name': 'Groq', 'provider': 'groq', 'api_key': 'gsk-secreto-1234',
        })
        stored = self._stored(provider)
        self.assertTrue(stored)
        self.assertNotIn('secreto', stored)
        self.assertFalse(provider.api_key, 'el campo es de solo escritura')
        self.assertTrue(provider.api_key_masked.endswith('1234'))
        self.assertEqual(provider._get_api_key(), 'gsk-secreto-1234')
        self.assertFalse(column_exists(self.env.cr, 'ai_provider_config', 'api_key'),
                         'no queda columna en texto plano')

    def test_saving_the_form_without_a_new_key_keeps_the_old_one(self):
        provider = self.env['ai.provider.config'].create({
            'name': 'Mistral', 'provider': 'mistral', 'api_key': 'mk-original',
        })
        provider.write({'api_key': False, 'name': 'Mistral renombrado'})
        self.assertEqual(provider._get_api_key(), 'mk-original')

    def test_legacy_plaintext_keys_are_encrypted_and_the_column_dropped(self):
        Config = self.env['ai.provider.config']
        openai = Config.create({'name': 'OpenAI', 'provider': 'openai', 'api_key': 'placeholder'})
        proxied = Config.create({'name': 'Claude proxy', 'provider': 'anthropic', 'api_key': 'placeholder'})
        ollama = Config.create({'name': 'Ollama', 'provider': 'ollama', 'ollama_mode': 'local',
                                'base_url': 'http://localhost:11434'})
        self.env.flush_all()
        cr = self.env.cr
        # Estado de una base en 19.0.1.0.0: clave en claro y base_url de Ollama en todos.
        cr.execute('ALTER TABLE ai_provider_config ADD COLUMN %s varchar' % LEGACY_COLUMN)
        cr.execute('UPDATE ai_provider_config SET api_key_encrypted = NULL, %s = %%s, base_url = %%s WHERE id = %%s'
                   % LEGACY_COLUMN, ('sk-openai-real ', LEGACY_BASE_URL_DEFAULT, openai.id))
        cr.execute('UPDATE ai_provider_config SET api_key_encrypted = NULL, %s = %%s, base_url = %%s WHERE id = %%s'
                   % LEGACY_COLUMN, ('sk-ant-real', 'https://gateway.interno/anthropic', proxied.id))

        migrated = encrypt_legacy_api_keys(self.env)
        reset_legacy_base_urls(cr)
        self.env.invalidate_all()

        self.assertGreaterEqual(migrated, 2)
        self.assertFalse(column_exists(cr, 'ai_provider_config', LEGACY_COLUMN))
        self.assertEqual(openai._get_api_key(), 'sk-openai-real')
        self.assertEqual(proxied._get_api_key(), 'sk-ant-real')
        self.assertEqual(openai.base_url, 'https://api.openai.com/v1', 'ya no apunta a Ollama')
        self.assertEqual(proxied.base_url, 'https://gateway.interno/anthropic', 'una URL a mano se respeta')
        self.assertEqual(ollama.base_url, 'http://localhost:11434')

    def test_unreadable_key_degrades_instead_of_breaking(self):
        Config = self.env['ai.provider.config']
        Config.search([]).write({'active': False})
        Config.create({'name': 'Ollama local', 'provider': 'ollama', 'ollama_mode': 'local',
                       'base_url': 'http://ollama-local:11434'})
        broken = Config.create({'name': 'Groq', 'provider': 'groq', 'api_key': 'gsk-x'})
        self.env.flush_all()
        self.env.cr.execute("UPDATE ai_provider_config SET api_key_encrypted = 'gAAAAA-basura' WHERE id = %s",
                            (broken.id,))
        self.env.invalidate_all()
        with patch(REQUESTS + '.post', return_value=ollama_ok('sigue funcionando')) as post:
            self.assertEqual(broken.generate_content('x'), 'sigue funcionando')
        self.assertEqual(post.call_args.args[0], 'http://ollama-local:11434/api/chat')
        self.assertEqual(broken.last_error_kind, 'config')
