# -*- coding: utf-8 -*-
from odoo import fields, models


class SocialOauthApp(models.Model):
    _name = 'social.oauth.app'
    _description = 'App OAuth2 registrada en la plataforma (Facebook / LinkedIn / X / TikTok)'

    name = fields.Char(required=True)
    platform = fields.Selection(
        [
            ('facebook', 'Facebook / Instagram (Meta App)'),
            ('linkedin', 'LinkedIn'),
            ('twitter', 'X (Twitter)'),
            ('tiktok', 'TikTok'),
        ],
        required=True,
    )
    client_id = fields.Char(
        string='App ID / Client ID / Client Key',
        required=True,
        help='Facebook: App ID. LinkedIn/X: Client ID. TikTok: Client Key.',
    )
    client_secret = fields.Char(
        string='App Secret / Client Secret',
        groups='social_agent_publisher.group_social_agent_manager',
        help='Requerido en Facebook, LinkedIn y TikTok. En X (Twitter) solo es '
             'necesario si tu app está configurada como "Confidential client"; '
             'si es "Public client" (recomendado para PKCE) puedes dejarlo vacío.',
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company
    )

    def _get_redirect_uri(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        mapping = {
            'facebook': 'facebook',
            'linkedin': 'linkedin',
            'twitter': 'twitter',
            'tiktok': 'tiktok',
        }
        platform_path = mapping.get(self.platform)
        if not platform_path:
            return False
        return f'{base_url}/social_agent/oauth/{platform_path}/callback'
