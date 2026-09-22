import json
import logging
from datetime import timedelta

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)

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
        "rate_limited": "You're sending messages a bit too fast — please wait a moment and try again.",
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
        "rate_limited": "Estás enviando mensajes muy rápido — esperá un momento y probá de nuevo.",
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
        provider = self._get_provider()
        widget_enabled = icp.get_param("ai_customer_agent.widget_enabled", "True") == "True"

        if not (widget_enabled and provider):
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

        if not self._check_rate_limit(icp, session_id):
            _logger.warning("AI Customer Agent: rate limit alcanzado para session_id=%s", session_id)
            return {"reply": _t(lang, "rate_limited"), "route": "rate_limited"}

        provider = self._get_provider()
        if not provider:
            _logger.error("AI Customer Agent: no hay un proveedor de IA configurado (ai.provider.config).")
            return {"reply": _t(lang, "not_configured"), "route": "error"}

        system_prompt = self._build_system_prompt(icp, lang)

        try:
            ai_reply_text = provider.generate_content(user_message, system_prompt=system_prompt)
        except Exception:
            _logger.exception("AI Customer Agent: error llamando al proveedor de IA (%s)", provider.name)
            self._log_conversation(session_id, user_message, _t(lang, "technical_error"), "error")
            return {"reply": _t(lang, "technical_error"), "route": "error"}

        order_lookup_enabled = icp.get_param("ai_customer_agent.enable_order_lookup") == "True"
        actions_enabled = order_lookup_enabled and icp.get_param("ai_customer_agent.enable_actions") == "True"
        approval_required = icp.get_param("ai_customer_agent.actions_require_approval", "True") == "True"
        discount_percent = float(icp.get_param("ai_customer_agent.discount_percent", "10.0") or 10.0)

        route, reply_text, extra = self._interpret_and_act(
            ai_reply_text,
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
    # Proveedor de IA (ai_agent_core): Claude o Gemini, intercambiable sin
    # tocar código — ver ai_customer_agent.ai_provider_id en Ajustes.
    # ------------------------------------------------------------------

    def _get_provider(self):
        """Proveedor de IA configurado para este agente. Si no se eligió uno
        explícitamente en Ajustes, cae al proveedor marcado por defecto en
        Agentes de IA → Proveedores de IA (mismo registro que usa
        social_agent_publisher)."""
        return request.env["ai.provider.config"].sudo().get_configured_provider(
            "ai_customer_agent.ai_provider_id"
        )

    # ------------------------------------------------------------------
    # Rate limiting: el endpoint es auth="public", sin esto cualquiera puede
    # agotar la cuota gratuita del proveedor de IA (o generar costo si es de
    # pago) a fuerza de pegarle al endpoint. Se apoya en ai.agent.log, que ya
    # registra cada turno de chat con session_id y create_date — no hace
    # falta un modelo nuevo.
    # ------------------------------------------------------------------

    def _check_rate_limit(self, icp, session_id):
        Log = request.env["ai.agent.log"].sudo()
        window_start = fields.Datetime.now() - timedelta(seconds=60)

        per_session_limit = int(icp.get_param("ai_customer_agent.rate_limit_per_session", "8") or 8)
        session_count = Log.search_count([
            ("session_id", "=", session_id), ("create_date", ">=", window_start),
        ])
        if session_count >= per_session_limit:
            return False

        global_limit = int(icp.get_param("ai_customer_agent.rate_limit_global", "60") or 60)
        global_count = Log.search_count([("create_date", ">=", window_start)])
        if global_count >= global_limit:
            return False

        return True

    # ------------------------------------------------------------------
    # Integración con ai_agent_core (ARIA): conversación, auditoría
    # ------------------------------------------------------------------

    def _get_or_create_conversation(self, session_id, lang=None):
        """Devuelve la ai.conversation de ARIA para esta sesión del widget,
        creándola si no existe. Nunca lanza excepción: si ai_agent_core no
        está instalado o falla por cualquier motivo, el chat debe seguir
        funcionando igual (esto es trazabilidad adicional, no una
        dependencia dura del flujo de respuesta al cliente)."""
        try:
            Conversation = request.env['ai.conversation'].sudo()
            conversation = Conversation.search([
                ('external_contact', '=', session_id),
                ('state', '=', 'active'),
            ], limit=1, order='write_date desc')
            if conversation:
                return conversation
            agent = request.env.ref('ai_agent_core.agent_customer_service', raise_if_not_found=False)
            if not agent:
                return False
            return Conversation.create({
                'agent_id': agent.id,
                'external_contact': session_id,
            })
        except Exception:
            _logger.exception("AI Customer Agent: no se pudo crear/obtener la conversación ARIA")
            return False

    ROUTE_TOOL_MAP = {
        "respuesta_directa": "responder_faq",
        "consultar_pedido": "consultar_estado_pedido",
        "escalar_humano": "escalar_a_humano",
        "accion_ejecutada": "ejecutar_accion_pedido",
        "error": "chat",
    }

    def _audit_log(self, conversation, route, user_message, reply_text, status="success"):
        """Registra la interacción en ai.audit.log de ai_agent_core, para
        que se refleje en el HUD y en el histórico de auditoría general.
        No reemplaza a ai.agent.log (que se conserva tal cual, es el log
        propio de este módulo); esto es adicional. 'accion_pendiente_aprobacion'
        no pasa por aquí: esa se audita sola cuando ai.approval.request la
        ejecuta al ser aprobada."""
        tool_name = self.ROUTE_TOOL_MAP.get(route)
        if not tool_name:
            return
        try:
            agent = request.env.ref('ai_agent_core.agent_customer_service', raise_if_not_found=False)
            if not agent:
                return
            request.env['ai.audit.log'].sudo().create({
                'agent_id': agent.id,
                'tool_name': tool_name,
                'user_id': request.env.user.id,
                'company_id': request.env.company.id,
                'conversation_id': conversation.id if conversation else False,
                'status': status,
                'request_json': json.dumps({'message': user_message}),
                'response_json': json.dumps({'reply': reply_text, 'route': route}),
            })
        except Exception:
            _logger.exception("AI Customer Agent: no se pudo escribir en ai.audit.log")

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

    def _interpret_and_act(self, ai_reply_text, original_message, session_id=None, lang=DEFAULT_LANG,
                            order_lookup_enabled=False, actions_enabled=False,
                            approval_required=True, discount_percent=10.0):
        """Decide si hay que consultar un pedido, proponer una acción,
        escalar a humano, o responder directo."""
        if ai_reply_text.startswith("NECESITA_CONSULTA_PEDIDO"):
            if not order_lookup_enabled:
                # Red de seguridad: Fase 2 apagada, no se ejecuta la consulta
                # aunque el modelo la haya pedido. Se escala a humano.
                ticket_ref = self._escalate_to_human(
                    original_message, "Cliente pregunta por estado de pedido (Fase 2 desactivada)")
                reply = _t(lang, "order_lookup_disabled")
                return "escalar_humano", reply, {"ticket_ref": ticket_ref}
            query = ai_reply_text.split(":", 1)[-1].strip()
            reply = self._lookup_order(query, lang)
            return "consultar_pedido", reply, {}

        if ai_reply_text.startswith("NECESITA_ACCION"):
            if not actions_enabled:
                # Red de seguridad: Fase 3 apagada, no se ejecuta nada.
                ticket_ref = self._escalate_to_human(
                    original_message, "Cliente pide una acción sobre su pedido (Fase 3 desactivada)")
                reply = _t(lang, "actions_disabled")
                return "escalar_humano", reply, {"ticket_ref": ticket_ref}
            return self._handle_action(ai_reply_text, original_message, session_id,
                                        approval_required, discount_percent, lang)

        if ai_reply_text.startswith("NECESITA_HUMANO"):
            summary = ai_reply_text.split(":", 1)[-1].strip()
            ticket_ref = self._escalate_to_human(original_message, summary)
            reply = (_t(lang, "escalated_with_ref", ref=ticket_ref) if ticket_ref
                     else _t(lang, "escalated_default"))
            return "escalar_humano", reply, {"ticket_ref": ticket_ref}

        return "respuesta_directa", ai_reply_text, {}

    def _handle_action(self, ai_reply_text, original_message, session_id, approval_required,
                        discount_percent, lang):
        """Parsea NECESITA_ACCION: TIPO | pedido | motivo y crea/ejecuta la
        acción según si requiere aprobación humana o no."""
        payload = ai_reply_text.split(":", 1)[-1].strip()
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
            tool = request.env['ai.agent.tool'].sudo().search(
                [('name', '=', 'ejecutar_accion_pedido')], limit=1)
            if not tool:
                # Red de seguridad: si por alguna razón el catálogo no tiene
                # la herramienta registrada (módulo ai_agent_core desactualizado
                # o no instalado todavía), no se pierde la solicitud: se
                # guarda como antes, directo en este módulo.
                _logger.warning(
                    "AI Customer Agent: herramienta 'ejecutar_accion_pedido' no "
                    "encontrada en ai.agent.tool; se crea la acción sin pasar "
                    "por el Vault de ai_agent_core."
                )
                PendingAction = request.env["ai.agent.pending_action"].sudo()
                PendingAction.create({
                    "session_id": session_id,
                    "order_id": order.id,
                    "action_type": action_type,
                    "reason": reason,
                    "discount_percent": discount_percent if action_type == "apply_discount" else 0.0,
                    "state": "pending",
                })
            else:
                conversation = self._get_or_create_conversation(session_id, lang)
                payload = {
                    "order_id": order.id,
                    "action_type": action_type,
                    "reason": reason,
                    "discount_percent": discount_percent if action_type == "apply_discount" else 0.0,
                }
                # Clave estable por (pedido, tipo de acción): si esta MISMA
                # acción ya se ejecutó con éxito para este pedido, un
                # reintento (doble clic, POST reenviado por la red) no la
                # vuelve a proponer/ejecutar — ver ai.approval.request._execute.
                idempotency_key = "ai_customer_agent:%s:%s" % (order.id, action_type)
                approval = request.env['ai.approval.request'].sudo().create({
                    'agent_id': tool.agent_id.id,
                    'tool_id': tool.id,
                    'conversation_id': conversation.id if conversation else False,
                    'payload_json': json.dumps(payload),
                    'preview_text': "%s sobre %s. Motivo: %s" % (
                        "Cancelar pedido" if action_type == "cancel_order" else "Aplicar descuento",
                        order.name, reason,
                    ),
                    'idempotency_key': idempotency_key,
                })
                approval.action_submit()

            action_label_es = "Cancelar pedido" if action_type == "cancel_order" else "Aplicar descuento"
            self._notify_humans(
                "🔔 Agente IA - Acción pendiente de aprobación\n\n"
                f"Pedido: {order.name}\n"
                f"Acción propuesta: {action_label_es}"
                + (f" ({discount_percent}%)" if action_type == "apply_discount" else "") +
                f"\nMotivo: {reason}\n\n"
                "Revisala en Odoo → Agentes de IA → Vault - Aprobaciones."
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

    def _escalate_to_human(self, original_message, summary, session_id=None):
        """Delegado a ai.agent.notifier (compartido con ai_agent_core, ver
        modelo ai_agent_notifier.py). Se conserva este método como wrapper
        fino para no tener que cambiar todas las llamadas existentes más
        abajo en este archivo."""
        result = request.env['ai.agent.notifier'].sudo().escalate_to_human(
            original_message, summary, session_id=session_id,
        )
        return result.get('ticket_ref')

    def _notify_humans(self, message):
        request.env['ai.agent.notifier'].sudo()._notify_humans(message)

    def _log_conversation(self, session_id, user_message, reply_text, route):
        request.env["ai.agent.log"].sudo().create({
            "session_id": session_id,
            "user_message": user_message,
            "reply_text": reply_text,
            "route": route,
        })
        conversation = self._get_or_create_conversation(session_id)
        if conversation:
            conversation.add_message('user', user_message)
            conversation.add_message('agent', reply_text)
            if route == 'escalar_humano':
                conversation.action_escalate()
        status = 'error' if route == 'error' else 'success'
        self._audit_log(conversation, route, user_message, reply_text, status=status)
