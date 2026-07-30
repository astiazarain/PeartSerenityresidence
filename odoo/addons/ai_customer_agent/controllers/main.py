import json
import logging

import requests

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS = 500

DEFAULT_LANG = "en"

# Every string the customer can actually see (chat replies, widget UI) is
# looked up here by language code, never hardcoded inline - that's what
# broke language consistency before: a Spanish system prompt plus hardcoded
# Spanish fallback replies made the agent answer in Spanish even on an
# English-only site. Internal ops notifications (WhatsApp/Telegram to staff)
# are intentionally left out of this - not customer-facing, not in scope.
STRINGS = {
    "en": {
        "language_name": "English",
        "not_configured": "The agent isn't set up yet. Please contact our team.",
        "technical_error": "We had a technical issue answering your message. A team member will reach out.",
        "order_lookup_disabled": "I can't look up orders automatically yet, but I've already notified our team.",
        "actions_disabled": "I'll pass your order along to our team to sort out.",
        "escalated_default": "I'm passing your question along to our team, they'll be in touch shortly.",
        "escalated_with_ref": "I'm passing your question along to our team, they'll be in touch shortly. Reference: {ref}",
        "action_malformed": "I'll pass this along to a team member.",
        "order_not_found_for_action": "I couldn't find that order to process your request. Can you confirm the exact order number?",
        "action_pending_approval": "I've logged your request about order {order}. A team member will review and confirm it shortly.",
        "action_error": "I had a problem processing this, passing it along to a team member.",
        "action_done_fallback": "Done, I've processed your request for order {order}.",
        "order_not_found": "I couldn't find an order with that information. Please check the order number or the email used for the purchase, or ask me to connect you with a team member.",
        "order_status_reply": "Your order {order} is {status}. Total: {total} {currency}.",
        "status_map": {
            "draft": "in quotation",
            "sent": "quotation sent",
            "sale": "confirmed",
            "done": "completed",
            "cancel": "cancelled",
        },
    },
    "es": {
        "language_name": "español",
        "not_configured": "El agente no está configurado todavía. Contacta al equipo de la tienda.",
        "technical_error": "Tuvimos un problema técnico respondiendo tu mensaje. Un humano te va a contactar.",
        "order_lookup_disabled": "Por ahora no puedo consultar pedidos automáticamente, pero ya avisé a nuestro equipo.",
        "actions_disabled": "Voy a derivar tu pedido a nuestro equipo para que lo resuelvan.",
        "escalated_default": "Voy a derivar tu consulta a nuestro equipo, te van a contactar a la brevedad.",
        "escalated_with_ref": "Voy a derivar tu consulta a nuestro equipo, te van a contactar a la brevedad. Referencia: {ref}",
        "action_malformed": "Voy a derivar tu consulta a una persona.",
        "order_not_found_for_action": "No encontré ese pedido para procesar la solicitud. ¿Podés confirmarme el número exacto?",
        "action_pending_approval": "Registré tu solicitud sobre el pedido {order}. Un miembro de nuestro equipo la va a revisar y confirmar en breve.",
        "action_error": "Tuve un problema procesando esto, lo derivo a una persona.",
        "action_done_fallback": "Listo, procesé tu solicitud sobre el pedido {order}.",
        "order_not_found": "No encontré un pedido con ese dato. Verificá el número de pedido o el email usado en la compra, o pedime que te derive con una persona.",
        "order_status_reply": "Tu pedido {order} está {status}. Total: {total} {currency}.",
        "status_map": {
            "draft": "en cotización",
            "sent": "cotización enviada",
            "sale": "confirmado",
            "done": "completado",
            "cancel": "cancelado",
        },
    },
}


def _t(lang, key, **kwargs):
    strings = STRINGS.get(lang, STRINGS[DEFAULT_LANG])
    text = strings.get(key, STRINGS[DEFAULT_LANG][key])
    return text.format(**kwargs) if kwargs else text


class AICustomerAgentController(http.Controller):

    @http.route("/ai_agent/widget_config", type="jsonrpc", auth="public", methods=["POST"], csrf=False)
    def widget_config(self, **kwargs):
        """Endpoint público de solo lectura para que un frontend externo (no
        renderizado por Odoo, ej. una SPA aparte) sepa si debe mostrar el
        widget y con qué configuración. Nunca devuelve la API key."""
        icp = request.env["ir.config_parameter"].sudo()
        api_key = icp.get_param("ai_customer_agent.anthropic_api_key")
        widget_enabled = icp.get_param("ai_customer_agent.widget_enabled", "True") == "True"

        if not (widget_enabled and api_key):
            return {"enabled": False}

        return {
            "enabled": True,
            "language": icp.get_param("ai_customer_agent.agent_language", DEFAULT_LANG),
            "store_name": icp.get_param("ai_customer_agent.store_name") or None,
            "primary_color": icp.get_param("ai_customer_agent.widget_primary_color", "#1E2A4A"),
            "accent_color": icp.get_param("ai_customer_agent.widget_accent_color", "#E8A33D"),
            "welcome_message": icp.get_param("ai_customer_agent.widget_welcome_message") or None,
        }

    @http.route("/ai_agent/chat", type="jsonrpc", auth="public", methods=["POST"], csrf=False)
    def chat(self, **kwargs):
        """Endpoint público que recibe el mensaje del widget de chat.

        Espera un body JSON-RPC estándar de Odoo con params:
            { "message": "...", "session_id": "..." }
        """
        params = request.jsonrequest.get("params", {}) if hasattr(request, "jsonrequest") else kwargs
        user_message = (params.get("message") or "").strip()
        session_id = params.get("session_id") or "anon"

        icp = request.env["ir.config_parameter"].sudo()
        lang = icp.get_param("ai_customer_agent.agent_language", DEFAULT_LANG)

        if not user_message:
            return {"error": "Falta el campo 'message'."}

        api_key = icp.get_param("ai_customer_agent.anthropic_api_key")
        if not api_key:
            _logger.error("AI Customer Agent: falta configurar la API key de Anthropic.")
            return {"reply": _t(lang, "not_configured"), "route": "error"}

        system_prompt = self._build_system_prompt(icp, lang)

        try:
            claude_text = self._call_claude(api_key, system_prompt, user_message)
        except Exception:
            _logger.exception("AI Customer Agent: error llamando a Claude")
            return {"reply": _t(lang, "technical_error"), "route": "error"}

        order_lookup_enabled = icp.get_param("ai_customer_agent.enable_order_lookup") == "True"
        actions_enabled = order_lookup_enabled and icp.get_param("ai_customer_agent.enable_actions") == "True"
        approval_required = icp.get_param("ai_customer_agent.actions_require_approval", "True") == "True"
        discount_percent = float(icp.get_param("ai_customer_agent.discount_percent", "10.0") or 10.0)

        route, reply_text, extra = self._interpret_and_act(
            claude_text,
            user_message,
            session_id=session_id,
            lang=lang,
            order_lookup_enabled=order_lookup_enabled,
            actions_enabled=actions_enabled,
            approval_required=approval_required,
            discount_percent=discount_percent,
        )

        self._log_conversation(session_id, user_message, reply_text, route)

        return {"reply": reply_text, "route": route, **extra}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_system_prompt(self, icp, lang):
        store_name = icp.get_param("ai_customer_agent.store_name", "the store")
        shipping = icp.get_param("ai_customer_agent.shipping_policy", "(not configured)")
        returns = icp.get_param("ai_customer_agent.returns_policy", "(not configured)")
        payments = icp.get_param("ai_customer_agent.payment_methods", "(not configured)")
        faqs = icp.get_param("ai_customer_agent.faqs", "(not configured)")
        order_lookup_enabled = icp.get_param("ai_customer_agent.enable_order_lookup") == "True"
        actions_enabled = order_lookup_enabled and icp.get_param("ai_customer_agent.enable_actions") == "True"
        discount_percent = icp.get_param("ai_customer_agent.discount_percent", "10.0")
        language_name = _t(lang, "language_name")

        if lang == "es":
            return self._build_system_prompt_es(
                store_name, shipping, returns, payments, faqs,
                order_lookup_enabled, actions_enabled, discount_percent, language_name,
            )
        return self._build_system_prompt_en(
            store_name, shipping, returns, payments, faqs,
            order_lookup_enabled, actions_enabled, discount_percent, language_name,
        )

    def _build_system_prompt_en(self, store_name, shipping, returns, payments, faqs,
                                 order_lookup_enabled, actions_enabled, discount_percent, language_name):
        if order_lookup_enabled:
            order_lookup_block = """
If the customer asks for the STATUS of a specific order (they gave an order \
number, or an email), respond EXACTLY with:
NECESITA_CONSULTA_PEDIDO: <the detail the customer gave>
Do not make up the order status yourself."""
        else:
            order_lookup_block = """
You can't look up real orders yet. If the customer asks about an order's \
status, kindly let them know you can't access that information right now \
and that a human will confirm it (using NECESITA_HUMANO)."""

        if actions_enabled:
            actions_block = f"""
If the customer asks to CANCEL an order, or asks for compensation/a discount \
for a problem (delay, damaged product, etc.), you may propose an action. \
You need the exact order number (if you don't have it, ask for it before \
proposing the action). Respond EXACTLY with one of these two forms:
NECESITA_ACCION: CANCELAR_PEDIDO | <order_number> | <brief reason>
NECESITA_ACCION: APLICAR_DESCUENTO | <order_number> | <brief reason>
The maximum discount you can offer is {discount_percent}%. Don't promise the \
customer the action is already done: tell them you'll process/confirm it."""
        else:
            actions_block = """
You can't cancel orders or apply discounts yet. If the customer asks for \
that, let them know you'll route their order to a person (using NECESITA_HUMANO)."""

        return f"""You are the customer service agent for {store_name}.
Answer using ONLY the information provided below. Don't invent policies, prices, or timelines.

SHIPPING: {shipping}
RETURNS: {returns}
PAYMENT METHODS: {payments}
FAQS: {faqs}
{order_lookup_block}
{actions_block}

If you don't have the information to answer, or the customer asks for a human, or there's a \
serious complaint, respond EXACTLY with:
NECESITA_HUMANO: <brief summary of the issue>

Tone: warm, personable, professional. Keep answers brief.

IMPORTANT: Always answer in {language_name}, regardless of the language the customer writes in."""

    def _build_system_prompt_es(self, store_name, shipping, returns, payments, faqs,
                                 order_lookup_enabled, actions_enabled, discount_percent, language_name):
        if order_lookup_enabled:
            order_lookup_block = """
Si el cliente pregunta por el ESTADO de un pedido específico (dio un número de \
pedido, o un email), responde EXACTAMENTE con:
NECESITA_CONSULTA_PEDIDO: <dato que dio el cliente>
No inventes el estado del pedido tú mismo."""
        else:
            order_lookup_block = """
Todavía no podés consultar pedidos reales. Si el cliente pregunta por el \
estado de un pedido, indicale amablemente que por ahora no podés acceder a \
esa información y que un humano se lo va a confirmar (usando NECESITA_HUMANO)."""

        if actions_enabled:
            actions_block = f"""
Si el cliente pide CANCELAR un pedido, o pide una compensación/descuento por \
un problema (demora, producto dañado, etc.), podés proponer una acción. \
Necesitás el número de pedido exacto (si no lo tenés, pedíselo antes de \
proponer la acción). Respondé EXACTAMENTE con una de estas dos formas:
NECESITA_ACCION: CANCELAR_PEDIDO | <numero_pedido> | <motivo breve>
NECESITA_ACCION: APLICAR_DESCUENTO | <numero_pedido> | <motivo breve>
El descuento máximo que podés ofrecer es {discount_percent}%. No prometas al \
cliente que la acción ya se ejecutó: decile que la vas a procesar/confirmar."""
        else:
            actions_block = """
No podés cancelar pedidos ni aplicar descuentos todavía. Si el cliente lo \
pide, indicale que vas a derivar su pedido a una persona (usando NECESITA_HUMANO)."""

        return f"""Eres el agente de atención al cliente de {store_name}.
Responde SOLO con la información entregada abajo. No inventes políticas, precios ni plazos.

ENVÍOS: {shipping}
DEVOLUCIONES: {returns}
MÉTODOS DE PAGO: {payments}
FAQS: {faqs}
{order_lookup_block}
{actions_block}

Si no tienes información para responder, o el cliente pide un humano, o hay un \
reclamo serio, responde EXACTAMENTE con:
NECESITA_HUMANO: <resumen breve del problema>

Tono cordial, cercano, profesional. Respuestas breves.

IMPORTANTE: Responde siempre en {language_name}, sin importar en qué idioma escriba el cliente."""

    def _call_claude(self, api_key, system_prompt, user_message):
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": CLAUDE_MODEL,
            "max_tokens": CLAUDE_MAX_TOKENS,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        }
        resp = requests.post(CLAUDE_API_URL, headers=headers, data=json.dumps(body), timeout=20)
        if resp.status_code >= 400:
            _logger.error("AI Customer Agent: Claude respondió %s: %s", resp.status_code, resp.text[:500])
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]

    def _interpret_and_act(self, claude_text, original_message, session_id=None, lang=DEFAULT_LANG,
                            order_lookup_enabled=False, actions_enabled=False,
                            approval_required=True, discount_percent=10.0):
        """Decide si hay que consultar un pedido, proponer una acción,
        escalar a humano, o responder directo."""
        if claude_text.startswith("NECESITA_CONSULTA_PEDIDO"):
            if not order_lookup_enabled:
                # Red de seguridad: Fase 2 apagada, no se ejecuta la consulta
                # aunque el modelo la haya pedido. Se escala a humano.
                ticket_ref = self._escalate_to_human(
                    original_message, "Cliente pregunta por estado de pedido (Fase 2 desactivada)")
                reply = _t(lang, "order_lookup_disabled")
                return "escalar_humano", reply, {"ticket_ref": ticket_ref}
            query = claude_text.split(":", 1)[-1].strip()
            reply = self._lookup_order(query, lang)
            return "consultar_pedido", reply, {}

        if claude_text.startswith("NECESITA_ACCION"):
            if not actions_enabled:
                # Red de seguridad: Fase 3 apagada, no se ejecuta nada.
                ticket_ref = self._escalate_to_human(
                    original_message, "Cliente pide una acción sobre su pedido (Fase 3 desactivada)")
                reply = _t(lang, "actions_disabled")
                return "escalar_humano", reply, {"ticket_ref": ticket_ref}
            return self._handle_action(claude_text, original_message, session_id,
                                        approval_required, discount_percent, lang)

        if claude_text.startswith("NECESITA_HUMANO"):
            summary = claude_text.split(":", 1)[-1].strip()
            ticket_ref = self._escalate_to_human(original_message, summary)
            reply = (_t(lang, "escalated_with_ref", ref=ticket_ref) if ticket_ref
                     else _t(lang, "escalated_default"))
            return "escalar_humano", reply, {"ticket_ref": ticket_ref}

        return "respuesta_directa", claude_text, {}

    def _handle_action(self, claude_text, original_message, session_id, approval_required,
                        discount_percent, lang):
        """Parsea NECESITA_ACCION: TIPO | pedido | motivo y crea/ejecuta la
        acción según si requiere aprobación humana o no."""
        payload = claude_text.split(":", 1)[-1].strip()
        parts = [p.strip() for p in payload.split("|")]
        if len(parts) < 2:
            ticket_ref = self._escalate_to_human(original_message, "Acción mal formada por el agente")
            return "escalar_humano", _t(lang, "action_malformed"), {"ticket_ref": ticket_ref}

        action_label, order_query = parts[0], parts[1]
        reason = parts[2] if len(parts) > 2 else "Solicitado por el cliente vía chat"
        action_type = "cancel_order" if action_label == "CANCELAR_PEDIDO" else "apply_discount"

        SaleOrder = request.env["sale.order"].sudo()
        order = SaleOrder.search([("name", "=", order_query)], limit=1)
        if not order:
            return "respuesta_directa", _t(lang, "order_not_found_for_action"), {}

        PendingAction = request.env["ai.agent.pending_action"].sudo()

        if approval_required:
            PendingAction.create({
                "session_id": session_id,
                "order_id": order.id,
                "action_type": action_type,
                "reason": reason,
                "discount_percent": discount_percent if action_type == "apply_discount" else 0.0,
                "state": "pending",
            })
            action_label_es = "Cancelar pedido" if action_type == "cancel_order" else "Aplicar descuento"
            self._notify_humans(
                "🔔 Agente IA - Acción pendiente de aprobación\n\n"
                f"Pedido: {order.name}\n"
                f"Acción propuesta: {action_label_es}"
                + (f" ({discount_percent}%)" if action_type == "apply_discount" else "") +
                f"\nMotivo: {reason}\n\n"
                "Revisala en Odoo → AI Customer Agent → Acciones pendientes."
            )
            reply = _t(lang, "action_pending_approval", order=order.name)
            return "accion_pendiente_aprobacion", reply, {}

        rec = PendingAction.execute_immediately(
            order, action_type, reason=reason,
            discount_percent=discount_percent if action_type == "apply_discount" else 0.0,
        )
        if rec.state == "error":
            ticket_ref = self._escalate_to_human(original_message, f"Error ejecutando acción: {rec.result_note}")
            return "escalar_humano", _t(lang, "action_error"), {"ticket_ref": ticket_ref}

        self._notify_humans(
            "✅ Agente IA - Acción ejecutada automáticamente\n\n"
            f"Pedido: {order.name}\n"
            f"Acción: {rec.result_note}\n"
            "(Aprobación humana desactivada para esta acción — revisá si hace falta.)"
        )
        reply = rec.result_note or _t(lang, "action_done_fallback", order=order.name)
        return "accion_ejecutada", reply, {}

    def _lookup_order(self, query, lang=DEFAULT_LANG):
        """Busca un pedido por número o por email del cliente. Solo lectura."""
        SaleOrder = request.env["sale.order"].sudo()
        order = SaleOrder.search([("name", "=", query)], limit=1)
        if not order:
            order = SaleOrder.search(
                [("partner_id.email", "=", query)], limit=1, order="create_date desc"
            )
        if not order:
            return _t(lang, "order_not_found")

        status_map = STRINGS.get(lang, STRINGS[DEFAULT_LANG])["status_map"]
        estado = status_map.get(order.state, order.state)
        return _t(lang, "order_status_reply", order=order.name, status=estado,
                   total=order.amount_total, currency=order.currency_id.name)

    def _notify_humans(self, message):
        """Envía el aviso por todos los canales que estén activados.
        Cada canal está aislado en su propio try/except: si uno falla,
        no debe afectar a los demás ni al flujo del chat."""
        icp = request.env["ir.config_parameter"].sudo()

        if icp.get_param("ai_customer_agent.whatsapp_callmebot_enabled") == "True":
            self._send_whatsapp_callmebot(icp, message)

        if icp.get_param("ai_customer_agent.whatsapp_meta_enabled") == "True":
            self._send_whatsapp_meta(icp, message)

        if icp.get_param("ai_customer_agent.telegram_enabled") == "True":
            self._send_telegram(icp, message)

    def _send_whatsapp_callmebot(self, icp, message):
        """Canal no oficial, gratuito, vía CallMeBot."""
        number = icp.get_param("ai_customer_agent.whatsapp_callmebot_number")
        apikey = icp.get_param("ai_customer_agent.whatsapp_callmebot_apikey")
        if not number or not apikey:
            _logger.warning("AI Customer Agent: CallMeBot activado pero falta número o apikey.")
            return
        try:
            requests.get(
                "https://api.callmebot.com/whatsapp.php",
                params={"phone": number, "text": message, "apikey": apikey},
                timeout=10,
            )
        except Exception:
            _logger.exception("AI Customer Agent: error enviando notificación por CallMeBot")

    def _send_whatsapp_meta(self, icp, message):
        """Canal oficial, WhatsApp Cloud API (Meta Business)."""
        phone_number_id = icp.get_param("ai_customer_agent.whatsapp_meta_phone_number_id")
        access_token = icp.get_param("ai_customer_agent.whatsapp_meta_access_token")
        to_number = icp.get_param("ai_customer_agent.whatsapp_meta_to_number")
        if not phone_number_id or not access_token or not to_number:
            _logger.warning("AI Customer Agent: WhatsApp Meta activado pero falta configuración.")
            return

        template_name = icp.get_param("ai_customer_agent.whatsapp_meta_template_name")
        url = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        if template_name:
            # Fuera de la ventana de 24hs, Meta exige una plantilla aprobada.
            template_lang = icp.get_param("ai_customer_agent.whatsapp_meta_template_lang", "es")
            body = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": template_lang},
                    "components": [{
                        "type": "body",
                        "parameters": [{"type": "text", "text": message[:1024]}],
                    }],
                },
            }
        else:
            # Texto libre: solo funciona si el destinatario escribió al
            # número de negocio en las últimas 24hs.
            body = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {"body": message},
            }
        try:
            resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=15)
            if resp.status_code >= 400:
                _logger.warning("AI Customer Agent: WhatsApp Meta respondió %s: %s",
                                 resp.status_code, resp.text[:500])
        except Exception:
            _logger.exception("AI Customer Agent: error enviando notificación por WhatsApp Meta")

    def _send_telegram(self, icp, message):
        """Canal oficial, gratuito, sin ventana de 24hs ni plantillas."""
        token = icp.get_param("ai_customer_agent.telegram_bot_token")
        chat_id = icp.get_param("ai_customer_agent.telegram_chat_id")
        if not token or not chat_id:
            _logger.warning("AI Customer Agent: Telegram activado pero falta token o chat_id.")
            return
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": chat_id, "text": message},
                timeout=10,
            )
        except Exception:
            _logger.exception("AI Customer Agent: error enviando notificación por Telegram")

    def _escalate_to_human(self, original_message, summary):
        """Crea un ticket de Helpdesk si el módulo está instalado; si no, una actividad."""
        env = request.env
        HelpdeskTicket = env.get("helpdesk.ticket")
        if HelpdeskTicket is not None:
            ticket = HelpdeskTicket.sudo().create({
                "name": f"Consulta de agente IA: {summary[:80]}",
                "description": f"Mensaje original del cliente:\n{original_message}\n\nResumen: {summary}",
            })
            ticket_ref = ticket.name if hasattr(ticket, "name") else str(ticket.id)
        else:
            # Fallback si no está instalado el módulo Helpdesk: actividad para el admin.
            env["mail.activity"].sudo().create({
                "res_model_id": env["ir.model"].sudo().search([("model", "=", "res.partner")], limit=1).id,
                "res_id": env.ref("base.main_partner").id,
                "activity_type_id": env.ref("mail.mail_activity_data_todo").id,
                "summary": f"Consulta escalada por agente IA: {summary[:80]}",
                "note": original_message,
            })
            ticket_ref = None

        self._notify_humans(
            "🔔 Agente IA - Se necesita una persona\n\n"
            f"Resumen: {summary}\n"
            f"Mensaje del cliente: {original_message}"
            + (f"\nRef: {ticket_ref}" if ticket_ref else "")
        )
        return ticket_ref

    def _log_conversation(self, session_id, user_message, reply_text, route):
        request.env["ai.agent.log"].sudo().create({
            "session_id": session_id,
            "user_message": user_message,
            "reply_text": reply_text,
            "route": route,
        })
