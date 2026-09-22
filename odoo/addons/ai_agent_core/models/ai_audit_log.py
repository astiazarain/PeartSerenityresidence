# -*- coding: utf-8 -*-
from odoo import api, fields, models

from odoo.addons.ai_agent_core.llm.errors import ERROR_KINDS


class AiAuditLog(models.Model):
    _name = 'ai.audit.log'
    _description = 'Registro de auditoría de una operación de un agente de IA'
    _order = 'create_date desc'

    event_type = fields.Selection(
        [
            ('tool', 'Herramienta de agente'),
            ('llm_call', 'Llamada a proveedor de IA'),
            ('health_check', 'Health check de proveedor'),
        ],
        string='Tipo de evento', default='tool', required=True,
    )
    conversation_id = fields.Many2one('ai.conversation', string='Conversación')
    # No obligatorio: las llamadas al proveedor también ocurren sin agente
    # (p. ej. al generar una publicación desde su ficha).
    agent_id = fields.Many2one('ai.agent')
    tool_name = fields.Char(required=True)
    user_id = fields.Many2one('res.users', string='Usuario', required=True)
    company_id = fields.Many2one('res.company', required=True)

    target_model = fields.Char()
    target_res_id = fields.Integer()

    request_json = fields.Text(string='Parámetros de la solicitud')
    response_json = fields.Text(string='Respuesta')

    approval_request_id = fields.Many2one('ai.approval.request', string='Aprobación asociada')
    status = fields.Selection(
        [('success', 'Éxito'), ('error', 'Error'), ('skipped', 'Omitida (idempotencia)')],
        required=True,
    )
    duration_ms = fields.Integer(string='Duración (ms)')
    error_type = fields.Char()
    error_message = fields.Text()

    # Llamadas a proveedores de IA
    provider_config_id = fields.Many2one(
        'ai.provider.config', string='Proveedor', ondelete='set null')
    provider_code = fields.Char(string='Tipo de proveedor')
    model_name = fields.Char(string='Modelo')
    input_tokens = fields.Integer(string='Tokens de entrada')
    output_tokens = fields.Integer(string='Tokens de salida')
    total_tokens = fields.Integer(
        string='Tokens totales', compute='_compute_total_tokens', store=True,
        help='Tokens de entrada + tokens de salida.')
    cost_usd = fields.Float(
        string='Costo estimado (USD)', digits=(16, 6),
        help='Si el proveedor informa el costo real (OpenRouter), ese. Si no, '
             'tokens de entrada × precio de entrada / 1e6 + tokens de salida × '
             'precio de salida / 1e6, con los precios de ai.model.spec. Vacío '
             'cuando el modelo no tiene precio conocido.')
    cost_source = fields.Selection(
        [('provider', 'Informado por el proveedor'), ('spec', 'Calculado con la ficha'),
         ('unknown', 'Sin precio conocido')],
        string='Origen del costo')
    attempt = fields.Integer(string='Intento', help='1 = primer intento; >1 = reintento tras un 429.')
    error_kind = fields.Selection(ERROR_KINDS, string='Tipo de fallo')
    fallback_from_id = fields.Many2one(
        'ai.provider.config', string='Degradado desde', ondelete='set null',
        help='Proveedor que se pidió originalmente, cuando esta llamada la '
             'atendió otro de la cadena de fallback.')

    # No se registran claves, contraseñas ni tokens de autenticación aquí
    # bajo ninguna circunstancia — ver ARIA_Especificacion_Tecnica.md §8. Los
    # "tokens" de arriba son unidades de consumo del modelo, no credenciales.

    @api.depends('input_tokens', 'output_tokens')
    def _compute_total_tokens(self):
        for rec in self:
            rec.total_tokens = (rec.input_tokens or 0) + (rec.output_tokens or 0)

    @api.depends('create_date', 'agent_id.name', 'tool_name', 'provider_config_id.name')
    def _compute_display_name(self):
        # Odoo 17+ sustituyó name_get() por este compute; name_get ya no se
        # invoca en ninguna parte, así que dejarlo aquí sería código muerto.
        for rec in self:
            rec.display_name = "%s · %s · %s" % (
                rec.create_date.strftime('%Y-%m-%d %H:%M') if rec.create_date else '?',
                rec.agent_id.name or rec.provider_config_id.name or '?',
                rec.tool_name or '?',
            )
