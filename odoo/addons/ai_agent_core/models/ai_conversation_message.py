# -*- coding: utf-8 -*-
from odoo import fields, models


class AiConversationMessage(models.Model):
    _name = 'ai.conversation.message'
    _description = 'Mensaje dentro de una conversación con un agente de IA'
    _order = 'create_date asc, id asc'

    conversation_id = fields.Many2one(
        'ai.conversation', required=True, ondelete='cascade', index=True,
    )
    role = fields.Selection(
        [('user', 'Usuario / cliente'), ('agent', 'Agente'), ('system', 'Sistema')],
        required=True,
    )
    content = fields.Text(required=True)
    tool_name = fields.Char(help="Si este mensaje representa una llamada a herramienta.")
    approval_request_id = fields.Many2one('ai.approval.request', string='Aprobación asociada')
