from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ai_agent_anthropic_api_key = fields.Char(
        string="Anthropic API Key",
        config_parameter="ai_customer_agent.anthropic_api_key",
        help="API key de Claude (Anthropic). Se guarda en System Parameters.",
    )
    ai_agent_store_name = fields.Char(
        string="Nombre de la tienda (para el agente)",
        config_parameter="ai_customer_agent.store_name",
    )
    ai_agent_language = fields.Selection(
        selection=[("en", "English"), ("es", "Español")],
        string="Idioma del agente y del widget",
        config_parameter="ai_customer_agent.agent_language",
        default="en",
        help="Idioma en el que responde Claude y en el que se muestran los "
             "textos del widget (saludo por defecto, placeholder, botones). "
             "Tiene que coincidir con el idioma del sitio público.",
    )
    ai_agent_shipping_policy = fields.Char(
        string="Política de envíos",
        config_parameter="ai_customer_agent.shipping_policy",
    )
    ai_agent_returns_policy = fields.Char(
        string="Política de devoluciones",
        config_parameter="ai_customer_agent.returns_policy",
    )
    ai_agent_payment_methods = fields.Char(
        string="Métodos de pago",
        config_parameter="ai_customer_agent.payment_methods",
    )
    ai_agent_faqs = fields.Char(
        string="Preguntas frecuentes (FAQs)",
        config_parameter="ai_customer_agent.faqs",
    )
    ai_agent_widget_enabled = fields.Boolean(
        string="Mostrar widget de chat en el sitio web",
        config_parameter="ai_customer_agent.widget_enabled",
        default=True,
    )
    ai_agent_enable_order_lookup = fields.Boolean(
        string="Fase 2: permitir que el agente consulte pedidos reales",
        config_parameter="ai_customer_agent.enable_order_lookup",
        default=False,
        help="Si está desactivado, el agente solo responde con FAQs y "
             "políticas (Fase 1) y nunca intenta buscar pedidos en Odoo. "
             "Activalo cuando ya hayas validado el piloto de FAQs.",
    )
    ai_agent_enable_actions = fields.Boolean(
        string="Fase 3: permitir que el agente proponga acciones (cancelar, descuento)",
        config_parameter="ai_customer_agent.enable_actions",
        default=False,
        help="Habilita que el agente pueda cancelar un pedido o aplicar un "
             "descuento de compensación. Requiere que la Fase 2 esté activa.",
    )
    ai_agent_actions_require_approval = fields.Boolean(
        string="Requerir aprobación humana antes de ejecutar la acción",
        config_parameter="ai_customer_agent.actions_require_approval",
        default=True,
        help="Recomendado mantener activado al principio: la acción queda "
             "pendiente en Odoo hasta que alguien la apruebe. Desactivalo "
             "solo cuando confíes en la precisión del agente.",
    )
    ai_agent_discount_percent = fields.Float(
        string="% de descuento que el agente puede ofrecer como compensación",
        config_parameter="ai_customer_agent.discount_percent",
        default=10.0,
    )
    ai_agent_whatsapp_callmebot_enabled = fields.Boolean(
        string="Canal: WhatsApp vía CallMeBot (no oficial)",
        config_parameter="ai_customer_agent.whatsapp_callmebot_enabled",
        default=False,
        help="Servicio gratuito no oficial, pensado para notificar a tu "
             "propio número/equipo. No requiere cuenta de Meta Business.",
    )
    ai_agent_whatsapp_callmebot_number = fields.Char(
        string="Número a notificar (CallMeBot)",
        config_parameter="ai_customer_agent.whatsapp_callmebot_number",
        help="Formato internacional con '+', sin espacios. Ej: +5491122334455",
    )
    ai_agent_whatsapp_callmebot_apikey = fields.Char(
        string="API Key de CallMeBot",
        config_parameter="ai_customer_agent.whatsapp_callmebot_apikey",
        help="Se obtiene activando el bot de CallMeBot desde el número que "
             "vas a notificar.",
    )
    ai_agent_whatsapp_meta_enabled = fields.Boolean(
        string="Canal: WhatsApp Cloud API (oficial, Meta Business)",
        config_parameter="ai_customer_agent.whatsapp_meta_enabled",
        default=False,
        help="Requiere una cuenta de Meta Business con WhatsApp Cloud API "
             "configurada: Phone Number ID y Access Token.",
    )
    ai_agent_whatsapp_meta_phone_number_id = fields.Char(
        string="Phone Number ID (Meta)",
        config_parameter="ai_customer_agent.whatsapp_meta_phone_number_id",
    )
    ai_agent_whatsapp_meta_access_token = fields.Char(
        string="Access Token (Meta)",
        config_parameter="ai_customer_agent.whatsapp_meta_access_token",
    )
    ai_agent_whatsapp_meta_to_number = fields.Char(
        string="Número a notificar (Meta, sin '+')",
        config_parameter="ai_customer_agent.whatsapp_meta_to_number",
        help="Formato: código de país + número, sin '+' ni espacios. Ej: 5491122334455",
    )
    ai_agent_whatsapp_meta_template_name = fields.Char(
        string="Nombre de plantilla aprobada (opcional)",
        config_parameter="ai_customer_agent.whatsapp_meta_template_name",
        help="Si el número a notificar no te escribió en las últimas 24hs, "
             "Meta exige usar una plantilla pre-aprobada en vez de texto "
             "libre. Dejalo vacío si vas a notificar dentro de la ventana "
             "de 24hs (por ejemplo, escribiéndole primero vos al bot).",
    )
    ai_agent_whatsapp_meta_template_lang = fields.Char(
        string="Idioma de la plantilla",
        config_parameter="ai_customer_agent.whatsapp_meta_template_lang",
        default="es",
    )
    ai_agent_telegram_enabled = fields.Boolean(
        string="Canal: Telegram",
        config_parameter="ai_customer_agent.telegram_enabled",
        default=False,
        help="Oficial, gratuito, sin ventana de 24hs ni restricciones de "
             "plantillas. Requiere crear un bot con @BotFather.",
    )
    ai_agent_telegram_bot_token = fields.Char(
        string="Token del bot de Telegram",
        config_parameter="ai_customer_agent.telegram_bot_token",
    )
    ai_agent_telegram_chat_id = fields.Char(
        string="Chat ID a notificar",
        config_parameter="ai_customer_agent.telegram_chat_id",
    )
    ai_agent_primary_color = fields.Char(
        string="Color principal del widget",
        config_parameter="ai_customer_agent.widget_primary_color",
        default="#1E2A4A",
    )
    ai_agent_accent_color = fields.Char(
        string="Color de acento del widget",
        config_parameter="ai_customer_agent.widget_accent_color",
        default="#E8A33D",
    )
    ai_agent_welcome_message = fields.Char(
        string="Mensaje de bienvenida",
        config_parameter="ai_customer_agent.widget_welcome_message",
        help="Si se deja vacío, se usa un saludo genérico con el nombre de la tienda.",
    )
