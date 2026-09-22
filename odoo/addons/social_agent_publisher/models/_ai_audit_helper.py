# -*- coding: utf-8 -*-
"""Helper de auditoría compartido por los modelos de social_agent_publisher.

No es un modelo Odoo (por eso el nombre empieza con "_" y no se importa
desde models/__init__.py como los demás archivos): es una función simple
para no duplicar la misma lógica de "buscar el agente y crear el log" en
cada método de acción.

IMPORTANTE — evitar doble conteo: estas acciones hoy se ejecutan casi
siempre directo desde botones del backend de Odoo (no a través del
Coordinador de ai_agent_core), así que este es el único punto donde quedan
auditadas. Si en el futuro se conecta social_agent_publisher al Coordinador
(ai.coordinator.route_message) o a ai.approval.request para estas mismas
herramientas, ese flujo también audita automáticamente — en ese caso, quitar
las llamadas de aquí para no duplicar filas en ai.audit.log.
"""
import logging

_logger = logging.getLogger(__name__)


def log_agent_audit(env, tool_name, status='success', request_json=None,
                     response_json=None, error_type=None, error_message=None):
    try:
        agent = env.ref('ai_agent_core.agent_social_media', raise_if_not_found=False)
        if not agent:
            return
        env['ai.audit.log'].sudo().create({
            'agent_id': agent.id,
            'tool_name': tool_name,
            'user_id': env.user.id,
            'company_id': env.company.id,
            'status': status,
            'request_json': request_json,
            'response_json': response_json,
            'error_type': error_type,
            'error_message': error_message,
        })
    except Exception:
        _logger.exception("No se pudo escribir en ai.audit.log para %s", tool_name)
