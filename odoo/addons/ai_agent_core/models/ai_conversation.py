# -*- coding: utf-8 -*-
from odoo import fields, models


class AiConversation(models.Model):
    _name = 'ai.conversation'
    _description = 'Conversación con un agente de IA'
    _order = 'write_date desc'

    name = fields.Char(compute='_compute_name', store=True)
    user_id = fields.Many2one(
        'res.users', string='Usuario', default=lambda self: self.env.user,
        help="Vacío cuando la conversación es con un tercero externo (p. ej. un "
             "cliente en el chat del sitio web) en vez de un usuario interno.",
    )
    external_contact = fields.Char(
        string='Contacto externo',
        help="Identificador del tercero externo cuando no hay user_id (email, "
             "teléfono, id de sesión del chat web, etc.).",
    )
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True,
    )
    agent_id = fields.Many2one('ai.agent', string='Agente', required=True)
    state = fields.Selection(
        [('active', 'Activa'), ('escalated', 'Escalada a humano'), ('closed', 'Cerrada')],
        default='active', required=True,
    )
    message_ids = fields.One2many('ai.conversation.message', 'conversation_id', string='Mensajes')
    message_count = fields.Integer(compute='_compute_message_count')

    def _compute_name(self):
        for conv in self:
            who = conv.user_id.name or conv.external_contact or 'Desconocido'
            conv.name = "%s - %s" % (conv.agent_id.name or '?', who)

    def _compute_message_count(self):
        for conv in self:
            conv.message_count = len(conv.message_ids)

    def add_message(self, role, content):
        self.ensure_one()
        return self.env['ai.conversation.message'].create({
            'conversation_id': self.id,
            'role': role,
            'content': content,
        })

    def action_escalate(self):
        self.write({'state': 'escalated'})

    def action_close(self):
        self.write({'state': 'closed'})
