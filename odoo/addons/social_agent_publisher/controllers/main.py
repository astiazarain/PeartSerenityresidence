# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

import requests

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)


def _html_result(title, message, ok=True):
    color = '#2e7d32' if ok else '#c62828'
    return f"""
    <html>
    <head><meta charset="utf-8"/><title>{title}</title></head>
    <body style="font-family: -apple-system, Arial, sans-serif; padding: 40px; text-align:center;">
        <h2 style="color:{color};">{title}</h2>
        <p>{message}</p>
        <p><a href="/odoo">Volver a Odoo</a></p>
    </body>
    </html>
    """


class SocialAgentOauthController(http.Controller):

    # ------------------------------------------------------------------
    # Facebook / Instagram
    # ------------------------------------------------------------------

    @http.route('/social_agent/oauth/facebook/callback', type='http', auth='user', csrf=False)
    def facebook_callback(self, code=None, state=None, error=None, **kwargs):
        if error:
            return _html_result(
                'Conexión cancelada', 'Facebook devolvió un error: %s' % error, ok=False
            )
        if not code or not state or ':' not in state:
            return _html_result(
                'Error', 'Faltan parámetros en la respuesta de Facebook.', ok=False
            )

        token, account_id = state.split(':', 1)
        account = request.env['social.media.account'].browse(int(account_id))
        if not account.exists() or account.oauth_state != token:
            return _html_result(
                'Error', 'El estado de la solicitud no es válido o expiró.', ok=False
            )

        app = request.env['social.oauth.app'].search(
            [('platform', '=', 'facebook'), ('active', '=', True)], limit=1
        )
        if not app:
            return _html_result('Error', 'No se encontró la Meta App configurada.', ok=False)

        redirect_uri = app._get_redirect_uri()

        try:
            # 1. Código -> token corto
            resp = requests.get(
                'https://graph.facebook.com/v21.0/oauth/access_token',
                params={
                    'client_id': app.client_id,
                    'redirect_uri': redirect_uri,
                    'client_secret': app.client_secret,
                    'code': code,
                },
                timeout=30,
            )
            resp.raise_for_status()
            short_token = resp.json()['access_token']

            # 2. Token corto -> token largo (~60 días)
            resp = requests.get(
                'https://graph.facebook.com/v21.0/oauth/access_token',
                params={
                    'grant_type': 'fb_exchange_token',
                    'client_id': app.client_id,
                    'client_secret': app.client_secret,
                    'fb_exchange_token': short_token,
                },
                timeout=30,
            )
            resp.raise_for_status()
            long_data = resp.json()
            long_user_token = long_data['access_token']
            expires_in = long_data.get('expires_in', 60 * 24 * 3600)

            # 3. Listar páginas administradas por el usuario
            resp = requests.get(
                'https://graph.facebook.com/v21.0/me/accounts',
                params={'access_token': long_user_token},
                timeout=30,
            )
            resp.raise_for_status()
            pages = resp.json().get('data', [])
            if not pages:
                return _html_result(
                    'Sin páginas',
                    'Tu usuario de Facebook no administra ninguna Página, o no '
                    'concediste el permiso pages_show_list.',
                    ok=False,
                )

            page = None
            if account.target_page_id:
                page = next((p for p in pages if p['id'] == account.target_page_id), None)
            if not page:
                page = pages[0]

            page_token = page['access_token']
            page_id = page['id']

            if account.platform == 'instagram':
                resp = requests.get(
                    f'https://graph.facebook.com/v21.0/{page_id}',
                    params={
                        'fields': 'instagram_business_account',
                        'access_token': page_token,
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                ig_data = resp.json().get('instagram_business_account')
                if not ig_data:
                    return _html_result(
                        'Sin cuenta de Instagram',
                        'La Página "%s" no tiene una cuenta de Instagram '
                        'Business/Creator vinculada.' % page.get('name'),
                        ok=False,
                    )
                account.write(
                    {
                        'access_token': page_token,
                        'account_identifier': ig_data['id'],
                        'token_expiry': fields.Datetime.now()
                        + timedelta(seconds=expires_in),
                        'oauth_state': False,
                    }
                )
                return _html_result(
                    '¡Instagram conectado!',
                    'Se conectó la cuenta de Instagram vinculada a la Página '
                    '"%s" correctamente.' % page.get('name'),
                )
            else:
                account.write(
                    {
                        'access_token': page_token,
                        'account_identifier': page_id,
                        'token_expiry': fields.Datetime.now()
                        + timedelta(seconds=expires_in),
                        'oauth_state': False,
                    }
                )
                return _html_result(
                    '¡Facebook conectado!',
                    'Se conectó la Página "%s" correctamente.' % page.get('name'),
                )
        except requests.exceptions.RequestException as exc:
            _logger.exception('Error en callback OAuth de Facebook')
            return _html_result('Error', 'Fallo comunicándose con Facebook: %s' % exc, ok=False)

    # ------------------------------------------------------------------
    # LinkedIn
    # ------------------------------------------------------------------

    @http.route('/social_agent/oauth/linkedin/callback', type='http', auth='user', csrf=False)
    def linkedin_callback(self, code=None, state=None, error=None, **kwargs):
        if error:
            return _html_result(
                'Conexión cancelada', 'LinkedIn devolvió un error: %s' % error, ok=False
            )
        if not code or not state or ':' not in state:
            return _html_result(
                'Error', 'Faltan parámetros en la respuesta de LinkedIn.', ok=False
            )

        token, account_id = state.split(':', 1)
        account = request.env['social.media.account'].browse(int(account_id))
        if not account.exists() or account.oauth_state != token:
            return _html_result(
                'Error', 'El estado de la solicitud no es válido o expiró.', ok=False
            )

        app = request.env['social.oauth.app'].search(
            [('platform', '=', 'linkedin'), ('active', '=', True)], limit=1
        )
        if not app:
            return _html_result('Error', 'No se encontró la app de LinkedIn configurada.', ok=False)

        redirect_uri = app._get_redirect_uri()

        try:
            resp = requests.post(
                'https://www.linkedin.com/oauth/v2/accessToken',
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': redirect_uri,
                    'client_id': app.client_id,
                    'client_secret': app.client_secret,
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            access_token = data['access_token']
            expires_in = data.get('expires_in', 60 * 24 * 3600)

            resp = requests.get(
                'https://api.linkedin.com/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=30,
            )
            resp.raise_for_status()
            member_id = resp.json().get('sub')

            account.write(
                {
                    'access_token': access_token,
                    'account_identifier': f'urn:li:person:{member_id}',
                    'token_expiry': fields.Datetime.now() + timedelta(seconds=expires_in),
                    'oauth_state': False,
                }
            )
            return _html_result('¡LinkedIn conectado!', 'Tu cuenta de LinkedIn se conectó correctamente.')
        except requests.exceptions.RequestException as exc:
            _logger.exception('Error en callback OAuth de LinkedIn')
            return _html_result('Error', 'Fallo comunicándose con LinkedIn: %s' % exc, ok=False)

    # ------------------------------------------------------------------
    # X (Twitter) — OAuth2 + PKCE
    # ------------------------------------------------------------------

    @http.route('/social_agent/oauth/twitter/callback', type='http', auth='user', csrf=False)
    def twitter_callback(self, code=None, state=None, error=None, **kwargs):
        if error:
            return _html_result(
                'Conexión cancelada', 'X (Twitter) devolvió un error: %s' % error, ok=False
            )
        if not code or not state or ':' not in state:
            return _html_result(
                'Error', 'Faltan parámetros en la respuesta de X (Twitter).', ok=False
            )

        token, account_id = state.split(':', 1)
        account = request.env['social.media.account'].browse(int(account_id))
        if not account.exists() or account.oauth_state != token:
            return _html_result(
                'Error', 'El estado de la solicitud no es válido o expiró.', ok=False
            )
        if not account.oauth_code_verifier:
            return _html_result(
                'Error', 'Falta el code_verifier de la sesión PKCE. Intenta de nuevo.', ok=False
            )

        app = request.env['social.oauth.app'].search(
            [('platform', '=', 'twitter'), ('active', '=', True)], limit=1
        )
        if not app:
            return _html_result('Error', 'No se encontró la app de X (Twitter) configurada.', ok=False)

        redirect_uri = app._get_redirect_uri()

        try:
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri,
                'client_id': app.client_id,
                'code_verifier': account.oauth_code_verifier,
            }
            auth = (app.client_id, app.client_secret) if app.client_secret else None
            resp = requests.post(
                'https://api.twitter.com/2/oauth2/token',
                data=data,
                auth=auth,
                timeout=30,
            )
            resp.raise_for_status()
            token_data = resp.json()
            access_token = token_data['access_token']
            refresh_token = token_data.get('refresh_token')
            expires_in = token_data.get('expires_in', 7200)

            resp = requests.get(
                'https://api.twitter.com/2/users/me',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=30,
            )
            resp.raise_for_status()
            user_data = resp.json().get('data', {})

            account.write(
                {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'account_identifier': user_data.get('id'),
                    'token_expiry': fields.Datetime.now() + timedelta(seconds=expires_in),
                    'oauth_state': False,
                    'oauth_code_verifier': False,
                }
            )
            return _html_result(
                '¡X (Twitter) conectado!',
                'Se conectó la cuenta @%s correctamente. El token se renovará '
                'automáticamente en segundo plano.' % user_data.get('username', ''),
            )
        except requests.exceptions.RequestException as exc:
            _logger.exception('Error en callback OAuth de X (Twitter)')
            return _html_result('Error', 'Fallo comunicándose con X (Twitter): %s' % exc, ok=False)

    # ------------------------------------------------------------------
    # TikTok
    # ------------------------------------------------------------------

    @http.route('/social_agent/oauth/tiktok/callback', type='http', auth='user', csrf=False)
    def tiktok_callback(self, code=None, state=None, error=None, **kwargs):
        if error:
            return _html_result(
                'Conexión cancelada', 'TikTok devolvió un error: %s' % error, ok=False
            )
        if not code or not state or ':' not in state:
            return _html_result(
                'Error', 'Faltan parámetros en la respuesta de TikTok.', ok=False
            )

        token, account_id = state.split(':', 1)
        account = request.env['social.media.account'].browse(int(account_id))
        if not account.exists() or account.oauth_state != token:
            return _html_result(
                'Error', 'El estado de la solicitud no es válido o expiró.', ok=False
            )

        app = request.env['social.oauth.app'].search(
            [('platform', '=', 'tiktok'), ('active', '=', True)], limit=1
        )
        if not app:
            return _html_result('Error', 'No se encontró la app de TikTok configurada.', ok=False)

        redirect_uri = app._get_redirect_uri()

        try:
            resp = requests.post(
                'https://open.tiktokapis.com/v2/oauth/token/',
                data={
                    'client_key': app.client_id,
                    'client_secret': app.client_secret,
                    'code': code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': redirect_uri,
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30,
            )
            resp.raise_for_status()
            token_data = resp.json()
            access_token = token_data['access_token']
            refresh_token = token_data.get('refresh_token')
            expires_in = token_data.get('expires_in', 86400)
            open_id = token_data.get('open_id')

            account.write(
                {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'account_identifier': open_id,
                    'token_expiry': fields.Datetime.now() + timedelta(seconds=expires_in),
                    'oauth_state': False,
                }
            )
            return _html_result(
                '¡TikTok conectado!',
                'Tu cuenta de TikTok se conectó correctamente. El token se '
                'renovará automáticamente en segundo plano.',
            )
        except requests.exceptions.RequestException as exc:
            _logger.exception('Error en callback OAuth de TikTok')
            return _html_result('Error', 'Fallo comunicándose con TikTok: %s' % exc, ok=False)
