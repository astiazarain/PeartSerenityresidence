# -*- coding: utf-8 -*-
import base64
import logging
import urllib.parse

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SocialMediaAccount(models.Model):
    _name = 'social.media.account'
    _description = 'Cuenta de red social conectada'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    platform = fields.Selection(
        [
            ('facebook', 'Facebook'),
            ('instagram', 'Instagram'),
            ('linkedin', 'LinkedIn'),
            ('twitter', 'X (Twitter)'),
            ('tiktok', 'TikTok'),
            ('generic', 'Genérico / Webhook (cualquier sistema)'),
        ],
        required=True,
        default='generic',
    )
    account_identifier = fields.Char(
        string='ID de cuenta / página',
        help='Page ID, Business Account ID, URN, usuario, etc. según la red.',
    )
    access_token = fields.Char(
        string='Access Token',
        groups='social_agent_publisher.group_social_agent_manager',
    )
    webhook_url = fields.Char(
        string='URL de Webhook',
        help='Solo para plataforma Genérico: endpoint HTTP POST a donde se '
             'enviará el contenido (útil para integrar con cualquier sistema '
             'propio, Zapier, Make, n8n, etc.).',
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company
    )
    notes = fields.Text(string='Notas')

    target_page_id = fields.Char(
        string='ID de Página de Facebook (opcional)',
        help='Si tu usuario administra varias Páginas, indica aquí el ID de '
             'la Página exacta que quieres conectar. Si lo dejas vacío, se '
             'tomará la primera página disponible.',
    )
    token_expiry = fields.Datetime(
        string='Expiración del token', readonly=True,
        help='Facebook: ~60 días. LinkedIn: según configuración de la app. '
             'X (Twitter): ~2 horas (se renueva solo). TikTok: 24hs (se renueva solo).',
    )
    oauth_state = fields.Char(readonly=True, copy=False)
    refresh_token = fields.Char(
        string='Refresh Token', copy=False,
        groups='social_agent_publisher.group_social_agent_manager',
        help='Usado por X (Twitter) y TikTok para renovar el access_token '
             'automáticamente sin que el usuario tenga que reconectar.',
    )
    oauth_code_verifier = fields.Char(
        readonly=True, copy=False,
        help='Valor temporal usado en el flujo PKCE de X (Twitter). Se limpia '
             'automáticamente tras conectar la cuenta.',
    )

    def action_connect_facebook(self):
        """Redirige al usuario al diálogo de autorización de Facebook."""
        self.ensure_one()
        import secrets
        state = secrets.token_urlsafe(24)
        self.oauth_state = state
        app = self.env['social.oauth.app'].search(
            [('platform', '=', 'facebook'), ('active', '=', True)], limit=1
        )
        if not app:
            from odoo.exceptions import UserError
            raise UserError(
                'No hay ninguna Meta App configurada en Social Agent → '
                'Configuración → Apps OAuth.'
            )
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        redirect_uri = app._get_redirect_uri()
        scope = (
            'pages_show_list,pages_manage_posts,pages_read_engagement,'
            'instagram_business_basic,instagram_business_content_publish'
        )
        import urllib.parse
        params = {
            'client_id': app.client_id,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'state': f'{state}:{self.id}',
            'response_type': 'code',
        }
        url = (
            'https://www.facebook.com/v21.0/dialog/oauth?'
            + urllib.parse.urlencode(params)
        )
        return {'type': 'ir.actions.act_url', 'url': url, 'target': 'self'}

    def action_connect_linkedin(self):
        """Redirige al usuario al diálogo de autorización de LinkedIn."""
        self.ensure_one()
        import secrets
        state = secrets.token_urlsafe(24)
        self.oauth_state = state
        app = self.env['social.oauth.app'].search(
            [('platform', '=', 'linkedin'), ('active', '=', True)], limit=1
        )
        if not app:
            from odoo.exceptions import UserError
            raise UserError(
                'No hay ninguna app de LinkedIn configurada en Social Agent → '
                'Configuración → Apps OAuth.'
            )
        redirect_uri = app._get_redirect_uri()
        scope = 'openid profile w_member_social'
        import urllib.parse
        params = {
            'response_type': 'code',
            'client_id': app.client_id,
            'redirect_uri': redirect_uri,
            'state': f'{state}:{self.id}',
            'scope': scope,
        }
        url = (
            'https://www.linkedin.com/oauth/v2/authorization?'
            + urllib.parse.urlencode(params)
        )
        return {'type': 'ir.actions.act_url', 'url': url, 'target': 'self'}

    def action_connect_twitter(self):
        """Redirige al usuario al diálogo de autorización de X (Twitter) usando PKCE."""
        self.ensure_one()
        import base64
        import hashlib
        import secrets
        import urllib.parse

        state = secrets.token_urlsafe(24)
        code_verifier = secrets.token_urlsafe(64)[:128]
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')

        self.write({'oauth_state': state, 'oauth_code_verifier': code_verifier})

        app = self.env['social.oauth.app'].search(
            [('platform', '=', 'twitter'), ('active', '=', True)], limit=1
        )
        if not app:
            raise UserError(
                'No hay ninguna app de X (Twitter) configurada en Social Agent → '
                'Configuración → Apps OAuth.'
            )
        redirect_uri = app._get_redirect_uri()
        params = {
            'response_type': 'code',
            'client_id': app.client_id,
            'redirect_uri': redirect_uri,
            'scope': 'tweet.read tweet.write users.read offline.access',
            'state': f'{state}:{self.id}',
            'code_challenge': challenge,
            'code_challenge_method': 'S256',
        }
        url = 'https://twitter.com/i/oauth2/authorize?' + urllib.parse.urlencode(params)
        return {'type': 'ir.actions.act_url', 'url': url, 'target': 'self'}

    def action_connect_tiktok(self):
        """Redirige al usuario al diálogo de autorización de TikTok."""
        self.ensure_one()
        import secrets
        import urllib.parse

        state = secrets.token_urlsafe(24)
        self.oauth_state = state

        app = self.env['social.oauth.app'].search(
            [('platform', '=', 'tiktok'), ('active', '=', True)], limit=1
        )
        if not app:
            raise UserError(
                'No hay ninguna app de TikTok configurada en Social Agent → '
                'Configuración → Apps OAuth.'
            )
        redirect_uri = app._get_redirect_uri()
        params = {
            'client_key': app.client_id,
            'response_type': 'code',
            'scope': 'user.info.basic,video.publish,video.upload',
            'redirect_uri': redirect_uri,
            'state': f'{state}:{self.id}',
        }
        url = (
            'https://www.tiktok.com/v2/auth/authorize/?'
            + urllib.parse.urlencode(params)
        )
        return {'type': 'ir.actions.act_url', 'url': url, 'target': 'self'}

    def _get_image_bytes(self, post):
        if post.image:
            return base64.b64decode(post.image)
        return None

    def publish(self, post):
        """Publica el contenido de `post` en esta cuenta.

        :return: tuple (success: bool, message: str, remote_id: str|False)
        """
        self.ensure_one()
        try:
            if self.platform == 'facebook':
                return self._publish_facebook(post)
            elif self.platform == 'instagram':
                return self._publish_instagram(post)
            elif self.platform == 'linkedin':
                return self._publish_linkedin(post)
            elif self.platform == 'twitter':
                return self._publish_twitter(post)
            elif self.platform == 'tiktok':
                return self._publish_tiktok(post)
            elif self.platform == 'generic':
                return self._publish_generic(post)
            return False, 'Plataforma no soportada: %s' % self.platform, False
        except requests.exceptions.RequestException as exc:
            _logger.exception('Error publicando en %s', self.name)
            return False, str(exc), False

    # ------------------------------------------------------------------
    # Implementaciones por plataforma.
    # NOTA: cada red social requiere su propio flujo OAuth2 previo para
    # obtener el access_token. Aquí se asume que el token ya es válido y
    # se muestra la llamada mínima de publicación; ajusta los endpoints/
    # parámetros según los permisos y versión de API que uses.
    # ------------------------------------------------------------------

    def _publish_facebook(self, post):
        url = f'https://graph.facebook.com/v20.0/{self.account_identifier}/feed'
        params = {'message': post.content, 'access_token': self.access_token}
        response = requests.post(url, params=params, timeout=30)
        if response.status_code == 200:
            post_id = response.json().get('id')
            return True, post_id or 'OK', post_id
        return False, response.text, False

    def _publish_instagram(self, post):
        # Instagram Graph API requiere primero crear un "media container"
        # con una imagen pública (image_url) y luego publicarlo.
        if not post.image_url:
            return False, (
                'Instagram requiere una imagen pública accesible por URL '
                '(campo "URL pública de imagen" en la publicación).'
            ), False
        base_url = f'https://graph.facebook.com/v20.0/{self.account_identifier}'
        container = requests.post(
            f'{base_url}/media',
            params={
                'image_url': post.image_url,
                'caption': post.content,
                'access_token': self.access_token,
            },
            timeout=30,
        )
        if container.status_code != 200:
            return False, container.text, False
        creation_id = container.json().get('id')
        publish = requests.post(
            f'{base_url}/media_publish',
            params={'creation_id': creation_id, 'access_token': self.access_token},
            timeout=30,
        )
        if publish.status_code == 200:
            media_id = publish.json().get('id')
            return True, media_id or 'OK', media_id
        return False, publish.text, False

    def _publish_linkedin(self, post):
        url = 'https://api.linkedin.com/v2/ugcPosts'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0',
        }
        payload = {
            'author': self.account_identifier,
            'lifecycleState': 'PUBLISHED',
            'specificContent': {
                'com.linkedin.ugc.ShareContent': {
                    'shareCommentary': {'text': post.content},
                    'shareMediaCategory': 'NONE',
                }
            },
            'visibility': {
                'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
            },
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code in (200, 201):
            post_urn = response.headers.get('x-restli-id')
            return True, post_urn or 'OK', post_urn
        return False, response.text, False

    def _publish_twitter(self, post):
        url = 'https://api.twitter.com/2/tweets'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        payload = {'text': post.content}
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 201:
            tweet_id = response.json().get('data', {}).get('id')
            return True, tweet_id or 'OK', tweet_id
        return False, response.text, False

    def _publish_tiktok(self, post):
        # TikTok solo publica VIDEO, no imágenes. Reutilizamos el campo
        # "URL pública de imagen" de la publicación como URL del video
        # (debe ser un .mp4 público) cuando se usa TikTok como destino.
        if not post.image_url:
            return False, (
                'TikTok requiere la URL pública de un video (.mp4). Ponla en '
                'el campo "URL pública de imagen" de la publicación.'
            ), False
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        payload = {
            'post_info': {
                'title': post.content[:2200] if post.content else '',
                'privacy_level': 'SELF_ONLY',
                'disable_duet': False,
                'disable_comment': False,
                'disable_stitch': False,
            },
            'source_info': {
                'source': 'PULL_FROM_URL',
                'video_url': post.image_url,
            },
        }
        response = requests.post(
            'https://open.tiktokapis.com/v2/post/publish/video/init/',
            headers=headers,
            json=payload,
            timeout=30,
        )
        if response.status_code != 200:
            return False, response.text, False
        data = response.json().get('data', {})
        publish_id = data.get('publish_id')
        if not publish_id:
            return False, 'TikTok no devolvió un publish_id: %s' % response.text, False
        return True, (
            'Video enviado a TikTok (publish_id: %s). Nota: quedó como '
            '"SELF_ONLY" (borrador visible solo para ti) por defecto de la '
            'API mientras tu app no tenga aprobado el permiso de publicación '
            'directa; revisa el estado en tu app de TikTok.' % publish_id
        ), publish_id

    # ------------------------------------------------------------------
    # Renovación automática de tokens (X/Twitter y TikTok expiran pronto)
    # ------------------------------------------------------------------

    @api.model
    def _cron_refresh_short_lived_tokens(self):
        from datetime import timedelta
        soon = fields.Datetime.now() + timedelta(minutes=20)
        accounts = self.search(
            [
                ('platform', 'in', ('twitter', 'tiktok')),
                ('refresh_token', '!=', False),
                ('token_expiry', '<=', soon),
            ]
        )
        for account in accounts:
            try:
                if account.platform == 'twitter':
                    account._refresh_twitter_token()
                elif account.platform == 'tiktok':
                    account._refresh_tiktok_token()
            except requests.exceptions.RequestException:
                _logger.exception('No se pudo renovar el token de %s', account.name)

    def _refresh_twitter_token(self):
        from datetime import timedelta
        self.ensure_one()
        app = self.env['social.oauth.app'].search(
            [('platform', '=', 'twitter'), ('active', '=', True)], limit=1
        )
        if not app:
            return
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': app.client_id,
        }
        auth = (app.client_id, app.client_secret) if app.client_secret else None
        resp = requests.post(
            'https://api.twitter.com/2/oauth2/token', data=data, auth=auth, timeout=30
        )
        resp.raise_for_status()
        token_data = resp.json()
        self.write(
            {
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token', self.refresh_token),
                'token_expiry': fields.Datetime.now()
                + timedelta(seconds=token_data.get('expires_in', 7200)),
            }
        )

    def _refresh_tiktok_token(self):
        from datetime import timedelta
        self.ensure_one()
        app = self.env['social.oauth.app'].search(
            [('platform', '=', 'tiktok'), ('active', '=', True)], limit=1
        )
        if not app:
            return
        resp = requests.post(
            'https://open.tiktokapis.com/v2/oauth/token/',
            data={
                'client_key': app.client_id,
                'client_secret': app.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30,
        )
        resp.raise_for_status()
        token_data = resp.json()
        self.write(
            {
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token', self.refresh_token),
                'token_expiry': fields.Datetime.now()
                + timedelta(seconds=token_data.get('expires_in', 86400)),
            }
        )

    def _publish_generic(self, post):
        if not self.webhook_url:
            return False, 'Debes configurar la URL de Webhook para esta cuenta.', False
        payload = {
            'account': self.name,
            'account_identifier': self.account_identifier,
            'content': post.content,
            'image_url': post.image_url or False,
        }
        headers = {'Content-Type': 'application/json'}
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        response = requests.post(
            self.webhook_url, json=payload, headers=headers, timeout=30
        )
        if 200 <= response.status_code < 300:
            return True, 'OK (%s)' % response.status_code, False
        return False, response.text, False

    # ------------------------------------------------------------------
    # Analítica: consulta de métricas (likes, comentarios, compartidos...)
    # ------------------------------------------------------------------

    def _fetch_metrics(self, line):
        """Consulta las métricas del post remoto asociado a `line` y las
        guarda en la propia línea. Falla en silencio (solo log) para no
        interrumpir el cron si una red está caída o el token expiró."""
        self.ensure_one()
        try:
            if self.platform == 'facebook':
                self._fetch_metrics_facebook(line)
            elif self.platform == 'instagram':
                self._fetch_metrics_instagram(line)
            elif self.platform == 'linkedin':
                self._fetch_metrics_linkedin(line)
            elif self.platform == 'twitter':
                self._fetch_metrics_twitter(line)
        except requests.exceptions.RequestException:
            _logger.exception(
                'No se pudieron obtener métricas para %s (%s)', line.post_id.name, self.name
            )

    def _fetch_metrics_facebook(self, line):
        response = requests.get(
            f'https://graph.facebook.com/v20.0/{line.remote_post_id}',
            params={
                'fields': 'likes.summary(true),comments.summary(true),shares',
                'access_token': self.access_token,
            },
            timeout=30,
        )
        if response.status_code != 200:
            return
        data = response.json()
        line.write(
            {
                'likes_count': data.get('likes', {}).get('summary', {}).get('total_count', 0),
                'comments_count': data.get('comments', {}).get('summary', {}).get('total_count', 0),
                'shares_count': data.get('shares', {}).get('count', 0),
                'metrics_updated_at': fields.Datetime.now(),
            }
        )

    def _fetch_metrics_instagram(self, line):
        response = requests.get(
            f'https://graph.facebook.com/v20.0/{line.remote_post_id}',
            params={
                'fields': 'like_count,comments_count',
                'access_token': self.access_token,
            },
            timeout=30,
        )
        if response.status_code != 200:
            return
        data = response.json()
        line.write(
            {
                'likes_count': data.get('like_count', 0),
                'comments_count': data.get('comments_count', 0),
                'metrics_updated_at': fields.Datetime.now(),
            }
        )

    def _fetch_metrics_linkedin(self, line):
        # LinkedIn requiere el permiso "r_organization_social" (páginas de
        # empresa) o "r_member_social" para leer estadísticas de shares
        # personales; muchas apps solo tienen permiso de escritura
        # (w_member_social), en cuyo caso esta llamada devolverá 403 y las
        # métricas quedarán en 0 hasta que amplíes los permisos.
        response = requests.get(
            'https://api.linkedin.com/v2/socialActions/'
            + urllib.parse.quote(line.remote_post_id, safe=''),
            headers={'Authorization': f'Bearer {self.access_token}'},
            timeout=30,
        )
        if response.status_code != 200:
            return
        data = response.json()
        line.write(
            {
                'likes_count': data.get('likesSummary', {}).get('totalLikes', 0),
                'comments_count': data.get('commentsSummary', {}).get('totalFirstLevelComments', 0),
                'metrics_updated_at': fields.Datetime.now(),
            }
        )

    def _fetch_metrics_twitter(self, line):
        response = requests.get(
            f'https://api.twitter.com/2/tweets/{line.remote_post_id}',
            params={'tweet.fields': 'public_metrics'},
            headers={'Authorization': f'Bearer {self.access_token}'},
            timeout=30,
        )
        if response.status_code != 200:
            return
        metrics = response.json().get('data', {}).get('public_metrics', {})
        line.write(
            {
                'likes_count': metrics.get('like_count', 0),
                'comments_count': metrics.get('reply_count', 0),
                'shares_count': metrics.get('retweet_count', 0),
                'impressions_count': metrics.get('impression_count', 0),
                'metrics_updated_at': fields.Datetime.now(),
            }
        )
