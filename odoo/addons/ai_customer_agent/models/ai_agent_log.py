from odoo import fields, models


class AIAgentLog(models.Model):
    _name = "ai.agent.log"
    _description = "Registro de conversaciones del agente de IA"
    _order = "create_date desc"

    session_id = fields.Char(string="Sesión", index=True)
    user_message = fields.Text(string="Mensaje del cliente")
    reply_text = fields.Text(string="Respuesta del agente")
    route = fields.Selection([
        ("respuesta_directa", "Respuesta directa"),
        ("consultar_pedido", "Consulta de pedido"),
        ("escalar_humano", "Escalado a humano"),
        ("error", "Error"),
    ], string="Ruta", index=True)
