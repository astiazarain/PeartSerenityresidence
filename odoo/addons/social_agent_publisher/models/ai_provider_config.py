# -*- coding: utf-8 -*-
import logging

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
GEMINI_API_URL_TMPL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

DEFAULT_MODELS = {
    'anthropic': 'claude-sonnet-4-6',
    'google': 'gemini-2.5-flash',
}


class AiProviderConfig(models.Model):
    _name = 'ai.provider.config'
    _description = 'Proveedor de IA para generación de contenido (Claude / Gemini)'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    provider = fields.Selection(
        [
            ('anthropic', 'Claude (Anthropic)'),
            ('google', 'Gemini (Google)'),
        ],
        required=True,
        default='anthropic',
    )
    api_key = fields.Char(
        string='API Key',
        required=True,
        groups='social_agent_publisher.group_social_agent_manager',
    )
    model_name = fields.Char(
        string='Modelo',
        help='Ej: claude-sonnet-4-6 (Anthropic) o gemini-2.5-flash (Google)',
    )
    system_prompt = fields.Text(
        string='Instrucción de sistema',
        default=(
            "Eres un asistente que redacta publicaciones para redes sociales. "
            "Responde únicamente con el texto final de la publicación, sin "
            "explicaciones ni comillas adicionales."
        ),
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company
    )

    @api.onchange('provider')
    def _onchange_provider(self):
        for rec in self:
            if not rec.model_name:
                rec.model_name = DEFAULT_MODELS.get(rec.provider, '')

    def generate_content(self, prompt, system_prompt=None):
        """Genera texto usando el proveedor de IA configurado.

        :param prompt: instrucción / tema para la publicación.
        :param system_prompt: instrucción de sistema opcional (si no se
            indica, se usa la configurada en el registro).
        :return: str con el contenido generado.
        """
        self.ensure_one()
        if not self.api_key:
            raise UserError('Este proveedor de IA no tiene una API Key configurada.')

        system_prompt = system_prompt or self.system_prompt or ''
        model = self.model_name or DEFAULT_MODELS.get(self.provider)

        try:
            if self.provider == 'anthropic':
                return self._generate_anthropic(prompt, system_prompt, model)
            elif self.provider == 'google':
                return self._generate_gemini(prompt, system_prompt, model)
            raise UserError('Proveedor de IA no soportado: %s' % self.provider)
        except requests.exceptions.RequestException as exc:
            _logger.exception('Error llamando a la API de %s', self.provider)
            raise UserError(
                'No se pudo generar el contenido con %s: %s' % (self.name, exc)
            )

    def _generate_anthropic(self, prompt, system_prompt, model):
        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': ANTHROPIC_VERSION,
            'content-type': 'application/json',
        }
        payload = {
            'model': model,
            'max_tokens': 1024,
            'system': system_prompt,
            'messages': [{'role': 'user', 'content': prompt}],
        }
        response = requests.post(
            ANTHROPIC_API_URL, headers=headers, json=payload, timeout=60
        )
        if response.status_code != 200:
            raise UserError(
                'Error de Anthropic (%s): %s' % (response.status_code, response.text)
            )
        data = response.json()
        text_blocks = [
            block.get('text', '')
            for block in data.get('content', [])
            if block.get('type') == 'text'
        ]
        return ''.join(text_blocks).strip()

    def _generate_gemini(self, prompt, system_prompt, model):
        url = GEMINI_API_URL_TMPL.format(model=model)
        headers = {'content-type': 'application/json'}
        params = {'key': self.api_key}
        payload = {
            'system_instruction': {'parts': [{'text': system_prompt}]},
            'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        }
        response = requests.post(
            url, headers=headers, params=params, json=payload, timeout=60
        )
        if response.status_code != 200:
            raise UserError(
                'Error de Gemini (%s): %s' % (response.status_code, response.text)
            )
        data = response.json()
        try:
            candidates = data.get('candidates', [])
            parts = candidates[0].get('content', {}).get('parts', [])
            return ''.join(part.get('text', '') for part in parts).strip()
        except (IndexError, KeyError, AttributeError):
            raise UserError('Respuesta inesperada de Gemini: %s' % data)
