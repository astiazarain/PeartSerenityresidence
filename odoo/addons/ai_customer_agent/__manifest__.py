{
    "name": "AI Customer Agent (Claude)",
    "version": "19.0.1.0.0",
    "category": "Website/Website",
    "summary": "Agente de atención al cliente basado en Claude, conectado a pedidos y helpdesk",
    "description": """
Agente de atención al cliente para tiendas Odoo Community
===========================================================

Expone un endpoint HTTP que recibe mensajes de un widget de chat en tu
sitio web, los responde usando la API de Claude (Anthropic), y puede:

- Responder preguntas usando políticas configuradas (envíos, devoluciones,
  pagos, FAQs).
- Consultar el estado real de un pedido (sale.order) cuando el cliente
  lo pide.
- Escalar a un ticket de Helpdesk (si el módulo helpdesk está instalado)
  o a una actividad de seguimiento cuando no puede resolver la consulta.
- Registrar cada conversación para auditoría y mejora del prompt.

No requiere Odoo Enterprise. Funciona sobre Community.
""",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": ["base", "sale", "mail", "website"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/ai_agent_log_views.xml",
        "views/ai_agent_pending_action_views.xml",
        "views/website_templates.xml",
    ],
    "installable": True,
    "application": False,
}
