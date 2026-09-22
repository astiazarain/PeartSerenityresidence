# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.social_agent_publisher.models.social_media_post import TITLE_SYSTEM_PROMPT


@tagged('post_install', '-at_install')
class TestPostAi(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env['ai.provider.config'].create({
            'name': 'IA test', 'provider': 'anthropic', 'api_key': 'k',
        })
        cls.provider.image_model_name_id = cls.env['ai.provider.available.model'].create({
            'provider_config_id': cls.provider.id, 'model_id': 'claude-sonnet-5',
            'name': 'claude-sonnet-5', 'kind': 'image',
        })
        account = cls.env['social.media.account'].create({'name': 'IG test', 'platform': 'instagram'})
        cls.Provider = type(cls.provider)
        cls.post_vals = {
            'topic': 'Nuevo servicio de coworking en Salón Natural',
            'ai_provider_id': cls.provider.id,
            'account_ids': [(6, 0, account.ids)],
        }

    def _fake_content(self, prompt, system_prompt=None):
        if system_prompt == TITLE_SYSTEM_PROMPT:
            return '**Título:** "Coworking de belleza en Salón Natural."'
        return 'Texto de la publicación'

    def test_generate_fills_empty_title_and_name_follows_it(self):
        post = self.env['social.media.post'].create(self.post_vals)
        self.assertEqual(post.name, 'Publicación #%s' % post.id, 'La instrucción ya no es el nombre')
        with patch.object(self.Provider, 'generate_content', autospec=True,
                          side_effect=lambda rec, *a, **kw: self._fake_content(*a, **kw)), \
                patch.object(self.Provider, 'generate_image', autospec=True,
                             return_value=('SU1H', 'ai_generated.jpg')):
            post.action_generate_with_ai()
        self.assertEqual(post.content, 'Texto de la publicación')
        self.assertEqual(post.title, 'Coworking de belleza en Salón Natural')
        self.assertEqual(post.name, post.title)

    def test_generate_keeps_title_written_by_user(self):
        post = self.env['social.media.post'].create(dict(self.post_vals, title='Mi título'))
        with patch.object(self.Provider, 'generate_content', autospec=True,
                          side_effect=lambda rec, *a, **kw: self._fake_content(*a, **kw)) as gen, \
                patch.object(self.Provider, 'generate_image', autospec=True,
                             return_value=('SU1H', 'ai_generated.jpg')):
            post.action_generate_with_ai()
        self.assertEqual(post.title, 'Mi título')
        self.assertEqual(gen.call_count, 1, 'Con título puesto no se pide otro a la IA')

    def test_regenerate_image_leaves_text_and_title_untouched(self):
        post = self.env['social.media.post'].create(dict(
            self.post_vals, title='Mi título', content='Texto aprobado',
        ))
        with patch.object(self.Provider, 'generate_content', autospec=True) as gen, \
                patch.object(self.Provider, 'generate_image', autospec=True,
                             return_value=('TlVFVkE=', 'ai_generated.jpg')):
            post.action_generate_image()
        gen.assert_not_called()
        self.assertEqual((post.content, post.title), ('Texto aprobado', 'Mi título'))
        self.assertEqual(post.image_filename, 'ai_generated.jpg')
        self.assertTrue(post.image)

    def test_regenerate_image_error_is_shown_to_user(self):
        post = self.env['social.media.post'].create(self.post_vals)
        with patch.object(self.Provider, 'generate_image', autospec=True,
                          side_effect=UserError('cuota 0')):
            with self.assertRaisesRegex(UserError, 'cuota 0'):
                post.action_generate_image()

    def test_regenerate_image_requires_image_model(self):
        self.provider.image_model_name_id = False
        post = self.env['social.media.post'].create(self.post_vals)
        with self.assertRaisesRegex(UserError, 'Modelo de imagen'):
            post.action_generate_image()

    def test_clean_title(self):
        clean = self.env['social.media.post']._clean_title
        self.assertEqual(clean('\n# Promo de verano.\nexplicación'), 'Promo de verano')
        self.assertEqual(clean('«Llega el coworking»'), 'Llega el coworking')
        long_title = ' '.join(['palabra'] * 30)
        self.assertLessEqual(len(clean(long_title)), 80)
        self.assertFalse(clean(long_title).endswith(' '))
