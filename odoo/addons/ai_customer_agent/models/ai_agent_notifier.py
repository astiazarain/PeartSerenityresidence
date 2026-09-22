# -*- coding: utf-8 -*-
import json
import logging

import requests

from odoo import models

_logger = logging.getLogger(__name__)


class AIAgentNotifier(models.AbstractModel):
    """Notificaciones a humanos (WhatsApp/Telegram) y escalado a Helpdesk.

    Extraído de controllers/main.py para que sea invocable como una
    herramienta real registrada en ai_agent_core (ai.agent.tool
    'escalar_a_humano'), y no solo desde el controlador del widget. Misma
    lógica que ya estaba probada, solo movida de self.request.env a self.env
    para que funcione igual desde un controlador HTTP que desde un contexto
    de backend (p. ej. una ai.approval.request ejecutándose sin request).
    """
    _name = 'ai.agent.notifier'
    _description = 'Notificaciones y escalado a humano del agente de atención al cliente'

    def _notify_humans(self, message):
        """Envía el aviso por todos los canales que estén activados. Cada
        canal está aislado en su propio try/except: si uno falla, no debe
        afectar a los demás."""
        icp = self.env['ir.config_parameter'].sudo()

        if icp.get_param('ai_customer_agent.whatsapp_callmebot_enabled') == 'True':
            self._send_whatsapp_callmebot(icp, message)

        if icp.get_param('ai_customer_agent.whatsapp_meta_enabled') == 'True':
            self._send_whatsapp_meta(icp, message)

        if icp.get_param('ai_customer_agent.telegram_enabled') == 'True':
            self._send_telegram(icp, message)

    def _send_whatsapp_callmebot(self, icp, message):
        number = icp.get_param('ai_customer_agent.whatsapp_callmebot_number')
        apikey = icp.get_param('ai_customer_agent.whatsapp_callmebot_apikey')
        if not number or not apikey:
            _logger.warning('AI Customer Agent: CallMeBot activado pero falta número o apikey.')
            return
        try:
            requests.get(
                'https://api.callmebot.com/whatsapp.php',
                params={'phone': number, 'text': message, 'apikey': apikey},
                timeout=10,
            )
        except Exception:
            _logger.exception('AI Customer Agent: error enviando notificación por CallMeBot')

    def _send_whatsapp_meta(self, icp, message):
        phone_number_id = icp.get_param('ai_customer_agent.whatsapp_meta_phone_number_id')
        access_token = icp.get_param('ai_customer_agent.whatsapp_meta_access_token')
        to_number = icp.get_param('ai_customer_agent.whatsapp_meta_to_number')
        if not phone_number_id or not access_token or not to_number:
            _logger.warning('AI Customer Agent: WhatsApp Meta activado pero falta configuración.')
            return

        template_name = icp.get_param('ai_customer_agent.whatsapp_meta_template_name')
        url = f'https://graph.facebook.com/v20.0/{phone_number_id}/messages'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }
        if template_name:
            template_lang = icp.get_param('ai_customer_agent.whatsapp_meta_template_lang', 'es')
            body = {
                'messaging_product': 'whatsapp',
                'to': to_number,
                'type': 'template',
                'template': {
                    'name': template_name,
                    'language': {'code': template_lang},
                    'components': [{
                        'type': 'body',
                        'parameters': [{'type': 'text', 'text': message[:1024]}],
                    }],
                },
            }
        else:
            body = {
                'messaging_product': 'whatsapp',
                'to': to_number,
                'type': 'text',
                'text': {'body': message},
            }
        try:
            resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=15)
            if resp.status_code >= 400:
                _logger.warning('AI Customer Agent: WhatsApp Meta respondió %s: %s',
                                 resp.status_code, resp.text[:500])
        except Exception:
            _logger.exception('AI Customer Agent: error enviando notificación por WhatsApp Meta')

    def _send_telegram(self, icp, message):
        token = icp.get_param('ai_customer_agent.telegram_bot_token')
        chat_id = icp.get_param('ai_customer_agent.telegram_chat_id')
        if not token or not chat_id:
            _logger.warning('AI Customer Agent: Telegram activado pero falta token o chat_id.')
            return
        try:
            requests.post(
                f'https://api.telegram.org/bot{token}/sendMessage',
                data={'chat_id': chat_id, 'text': message},
                timeout=10,
            )
        except Exception:
            _logger.exception('AI Customer Agent: error enviando notificación por Telegram')

    # ------------------------------------------------------------------
    # Punto de entrada para la herramienta ARIA 'escalar_a_humano'
    # ------------------------------------------------------------------

    def escalate_to_human(self, original_message, summary, session_id=None):
        """Crea un ticket de Helpdesk (si el módulo está instalado) o una
        actividad de seguimiento, y notifica por los canales activados.
        Devuelve un dict serializable (convención de ai.agent.tool.execute()).
        """
        env = self.env
        HelpdeskTicket = env.get('helpdesk.ticket')
        if HelpdeskTicket is not None:
            ticket = HelpdeskTicket.sudo().create({
                'name': f'Consulta de agente IA: {summary[:80]}',
                'description': f'Mensaje original del cliente:\n{original_message}\n\nResumen: {summary}',
            })
            ticket_ref = ticket.name if hasattr(ticket, 'name') else str(ticket.id)
        else:
            env['mail.activity'].sudo().create({
                'res_model_id': env['ir.model'].sudo().search([('model', '=', 'res.partner')], limit=1).id,
                'res_id': env.ref('base.main_partner').id,
                'activity_type_id': env.ref('mail.mail_activity_data_todo').id,
                'summary': f'Consulta escalada por agente IA: {summary[:80]}',
                'note': original_message,
            })
            ticket_ref = None

        self._notify_humans(
            '🔔 Agente IA - Se necesita una persona\n\n'
            f'Resumen: {summary}\n'
            f'Mensaje del cliente: {original_message}'
            + (f'\nRef: {ticket_ref}' if ticket_ref else '')
        )
        return {'ticket_ref': ticket_ref}
