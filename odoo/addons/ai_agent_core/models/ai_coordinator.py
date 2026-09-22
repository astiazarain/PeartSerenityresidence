# -*- coding: utf-8 -*-
import json
import logging
import re

from odoo import api, fields, models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

# Palabras demasiado comunes en español/inglés para aportar señal de
# clasificación — sin esto, el matching por palabra clave se volvía casi
# aleatorio: una herramienta con una descripción larga (muchos artículos y
# preposiciones) le ganaba a la herramienta realmente relevante solo por
# tener más palabras en común con CUALQUIER texto.
_STOPWORDS = {
    'a', 'al', 'con', 'de', 'del', 'el', 'en', 'es', 'está', 'esta', 'la',
    'las', 'lo', 'los', 'mi', 'no', 'o', 'para', 'per', 'por', 'que', 'se',
    'si', 'sin', 'su', 'sus', 'te', 'tu', 'un', 'una', 'uno', 'y', 'ya',
    'the', 'an', 'and', 'of', 'to', 'in', 'on', 'for', 'is', 'it', 'this',
    'that', 'be', 'or', 'if', 'my', 'me',
}
_ACCENT_MAP = str.maketrans('áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN')


def _tokenize(text):
    """Palabras significativas (sin acentos, sin stopwords, largo > 2) de un
    texto libre — se usa tanto para el mensaje del usuario como para el
    nombre+descripción de cada herramienta candidata, así el matching es
    palabra-a-palabra exacta y no `substring in text` (que hacía que
    prácticamente cualquier palabra corta de una descripción "matcheara"
    por aparecer como substring en casi cualquier mensaje)."""
    normalized = (text or '').lower().translate(_ACCENT_MAP)
    words = re.findall(r'[a-z0-9_]+', normalized)
    return {w for w in words if len(w) > 2 and w not in _STOPWORDS}


class AiCoordinator(models.AbstractModel):
    """Enrutador de intención del Agente Coordinador (ver ARIA_Especificacion_Tecnica.md §5.1).

    Implementación deliberadamente simple para el MVP: coincidencia de
    palabras clave contra el nombre/descripción de las herramientas
    registradas, con reintento vía LLM si no hay una coincidencia clara.
    Se evalúa un framework de agentes dedicado en Fase 2 (ver
    ARIA_Roadmap_Fase2.md §8) si esto empieza a fallar con más herramientas.
    """
    _name = 'ai.coordinator'
    _description = 'Coordinador — enrutamiento de intención hacia agente/herramienta'

    # ------------------------------------------------------------------
    # Punto de entrada único
    # ------------------------------------------------------------------

    @api.model
    def route_message(self, message, agent_code=None, conversation_id=None,
                       external_contact=None, params=None, idempotency_key=None):
        """Procesa un mensaje de entrada y devuelve un dict con la acción tomada.

        :param message: texto en lenguaje natural del usuario o cliente.
        :param agent_code: si se conoce de antemano a qué agente pertenece la
            conversación (p. ej. 'customer_service' desde el widget de chat).
            Si no se indica, se usa el agente marcado is_coordinator.
        :param conversation_id: id de ai.conversation existente, o False para
            crear una nueva.
        :param external_contact: identificador del tercero externo, cuando
            aplica (agentes external_facing).
        :param params: parámetros ya resueltos para la herramienta, si el
            llamador ya sabe qué quiere ejecutar (evita la clasificación).
        :param idempotency_key: clave estable que el llamador debe generar
            una vez por acción de usuario y reenviar sin cambios en cada
            reintento de la MISMA solicitud (ver ai.approval.request._execute:
            si ya existe una ejecución 'executed' con esta clave, no se
            repite la operación). Una clave generada de nuevo en cada
            llamada no protege nada — tiene que originarse en el cliente
            (HUD, widget) y sobrevivir al reintento.
        """
        Conversation = self.env['ai.conversation']
        Agent = self.env['ai.agent']

        agent = Agent.search([('code', '=', agent_code)], limit=1) if agent_code else \
            Agent.search([('is_coordinator', '=', True)], limit=1)
        if not agent:
            return {'error': "No hay un agente configurado para code=%s" % agent_code}

        conversation = Conversation.browse(conversation_id) if conversation_id else False
        if not conversation:
            conversation = Conversation.create({
                'agent_id': agent.id,
                'external_contact': external_contact or False,
            })
        conversation.add_message('user', message)

        tool = self._classify_intent(agent, message)

        if not tool:
            return self._handle_no_match(agent, conversation, message)

        if not tool.user_can_invoke(self.env.user):
            raise AccessError(
                "No tienes permiso para ejecutar la herramienta '%s'." % tool.label
            )

        # El Coordinador no tiene herramientas propias — su trabajo es
        # delegar. A partir de acá, el agente "activo" para auditoría y
        # aprobación es el dueño real de la herramienta (Redes Sociales,
        # Atención al Cliente...), no el Coordinador. La conversación en sí
        # sigue asociada al agente original: es un solo hilo en el HUD que
        # delega mensaje a mensaje, no una conversación por dominio.
        effective_agent = tool.agent_id or agent

        resolved_params = self._resolve_params(tool, message, params)

        if tool.requires_approval:
            return self._create_approval(effective_agent, conversation, tool, resolved_params, idempotency_key)

        return self._execute_direct(effective_agent, conversation, tool, resolved_params)

    # ------------------------------------------------------------------
    # Clasificación de intención
    # ------------------------------------------------------------------

    def _candidate_tools(self, agent):
        """Universo de herramientas que este agente puede resolver. El
        Coordinador no tiene herramientas propias (ver ai_agent_data.xml):
        su trabajo es delegar entre los agentes de dominio, así que su
        universo de búsqueda son TODAS las herramientas activas de esos
        agentes, no las suyas (que no existen). Un agente de dominio
        (Redes Sociales, Atención al Cliente) sigue buscando solo en las
        propias.

        Además, cuando el que enruta es el Coordinador, se excluyen las
        herramientas con requires_existing_record=True: necesitan un
        target_res_id (o un dato equivalente, como un pedido concreto) que
        el Coordinador no tiene forma de inventar a partir de un mensaje en
        lenguaje natural sin contexto previo. Enrutarlas de todos modos
        termina en una ejecución o aprobación condenada a fallar por falta
        de ese dato — mejor no ofrecerlas como candidatas todavía."""
        if agent.is_coordinator:
            return self.env['ai.agent.tool'].search([
                ('active', '=', True),
                ('agent_id.is_coordinator', '=', False),
                ('requires_existing_record', '=', False),
            ])
        return agent.tool_ids.filtered('active')

    def _classify_intent(self, agent, message):
        """Coincidencia simple por palabras clave. Devuelve un ai.agent.tool o
        False. No inventa una herramienta si no hay coincidencia razonable:
        es preferible pedir aclaración o escalar antes que ejecutar lo
        incorrecto."""
        text_words = _tokenize(message)
        candidate_tools = self._candidate_tools(agent)
        best_tool, best_score = False, 0
        for tool in candidate_tools:
            haystack_words = _tokenize("%s %s" % (tool.name.replace('_', ' '), tool.description or ''))
            score = len(haystack_words & text_words)
            if score > best_score:
                best_tool, best_score = tool, score
        if best_score > 0:
            return best_tool

        # Fallback: si el agente tiene proveedor de IA configurado, se le
        # pide que elija entre los nombres de herramienta disponibles. Si no
        # hay proveedor o falla, se trata como "sin coincidencia".
        provider = agent.get_provider()
        if not provider or not candidate_tools:
            return False
        try:
            tool_names = ", ".join(candidate_tools.mapped('name'))
            prompt = (
                "El usuario escribió: \"%s\".\n"
                "Elige, de esta lista de herramientas, cuál corresponde (responde "
                "solo con el nombre exacto, o la palabra NINGUNA si ninguna aplica): "
                "%s" % (message, tool_names)
            )
            answer = provider.generate_content(prompt).strip()
            return candidate_tools.filtered(lambda t: t.name == answer)[:1]
        except Exception:  # noqa: BLE001 — clasificación es best-effort
            _logger.warning("Fallback de clasificación por IA falló", exc_info=True)
            return False

    # ------------------------------------------------------------------
    # Resolución de parámetros a partir de texto libre
    # ------------------------------------------------------------------
    #
    # Deliberadamente acotado al caso concreto que sí se puede resolver sin
    # inventar datos: crear_publicacion_borrador (no requiere un registro
    # existente — ver requires_existing_record). Para el resto de las
    # herramientas, el Coordinador no completa parámetros por su cuenta;
    # si el llamador no los pasó ya resueltos en `params`, la herramienta
    # se ejecuta con lo que haya (o nada), y si eso no alcanza, el error
    # de la propia herramienta (o su ausencia de target_res_id) es lo que
    # se reporta — no se adivina un valor.

    _PLATFORM_KEYWORDS = {
        'facebook': 'facebook', 'fb': 'facebook',
        'instagram': 'instagram', 'insta': 'instagram', 'ig': 'instagram',
        'linkedin': 'linkedin',
        'twitter': 'twitter', 'tweet': 'twitter', 'x': 'twitter',
        'tiktok': 'tiktok',
    }

    def _resolve_params(self, tool, message, params):
        resolved = dict(params or {})
        if tool.name == 'crear_publicacion_borrador':
            resolved.setdefault('topic', message)
            if not resolved.get('account_ids'):
                resolved['account_ids'] = self._resolve_account_ids(message)
            if not resolved.get('ai_provider_id'):
                provider = self.env['ai.provider.config'].get_default_provider()
                if provider:
                    resolved['ai_provider_id'] = provider.id
        return resolved

    def _resolve_account_ids(self, message):
        """Detecta menciones de red social ('Facebook', 'Instagram',
        'LinkedIn', 'Twitter'/'X', 'TikTok') en el texto y devuelve los ids
        de las cuentas activas de esas plataformas. Sin menciones
        explícitas no adivina — devuelve vacío, y la propia herramienta
        pide que se indique la cuenta (ver action_create_draft).

        Nota: usa un split propio en vez de _tokenize, porque _tokenize
        descarta palabras de largo <= 2 ('x', 'ig', 'fb' — justo las que
        hacen falta acá) al estar pensado para reducir ruido en el
        matching de herramientas, no para esto."""
        normalized = (message or '').lower().translate(_ACCENT_MAP)
        words = set(re.findall(r'[a-z0-9]+', normalized))
        platforms = {self._PLATFORM_KEYWORDS[w] for w in words if w in self._PLATFORM_KEYWORDS}
        if not platforms:
            return []
        accounts = self.env['social.media.account'].search([
            ('platform', 'in', list(platforms)), ('active', '=', True),
        ])
        return accounts.ids

    def _handle_no_match(self, agent, conversation, message):
        if agent.external_facing and agent.escalation_tool_id:
            return self._execute_direct(
                agent, conversation, agent.escalation_tool_id,
                {'reason': 'No se identificó una herramienta para: %s' % message},
            )
        conversation.add_message(
            'agent',
            "No identifiqué una acción clara para esa solicitud. ¿Puedes darme más "
            "detalle o indicar qué quieres hacer?",
        )
        return {
            'conversation_id': conversation.id,
            'action': 'clarification_needed',
            'message': "No identifiqué una acción clara. Pide más detalle al usuario.",
        }

    # ------------------------------------------------------------------
    # Ejecución
    # ------------------------------------------------------------------

    def _execute_direct(self, agent, conversation, tool, params):
        """Para herramientas de riesgo 0/1: se ejecutan sin aprobación, pero
        igual quedan auditadas."""
        start = fields.Datetime.now()
        audit_vals = {
            'agent_id': agent.id,
            'tool_name': tool.name,
            'user_id': self.env.user.id,
            'company_id': self.env.company.id,
            'conversation_id': conversation.id,
            'request_json': json.dumps(params),
        }
        try:
            result = tool.execute(params=params)
            audit_vals.update({
                'status': 'success',
                'response_json': json.dumps(result) if result is not None else 'null',
            })
            conversation.add_message('agent', "Ejecutado: %s" % tool.label)
            outcome = {
                'conversation_id': conversation.id,
                'action': 'executed',
                'tool': tool.name,
                'result': result,
            }
        except Exception as exc:  # noqa: BLE001
            _logger.exception("Error ejecutando herramienta directa %s", tool.name)
            audit_vals.update({
                'status': 'error', 'error_type': type(exc).__name__, 'error_message': str(exc),
            })
            outcome = {
                'conversation_id': conversation.id, 'action': 'error', 'error': str(exc),
            }
        finally:
            audit_vals['duration_ms'] = int(
                (fields.Datetime.now() - start).total_seconds() * 1000
            )
            self.env['ai.audit.log'].sudo().create(audit_vals)
        return outcome

    def _create_approval(self, agent, conversation, tool, params, idempotency_key=None):
        approval = self.env['ai.approval.request'].create({
            'agent_id': agent.id,
            'tool_id': tool.id,
            'conversation_id': conversation.id,
            'requesting_user_id': self.env.user.id,
            'company_id': self.env.company.id,
            'payload_json': json.dumps(params),
            'preview_text': "%s: %s" % (tool.label, json.dumps(params)),
            'idempotency_key': idempotency_key or False,
        })
        approval.action_submit()
        conversation.add_message(
            'agent',
            "Esta acción (%s) requiere aprobación antes de ejecutarse. Queda "
            "pendiente en el Vault." % tool.label,
        )
        return {
            'conversation_id': conversation.id,
            'action': 'approval_pending',
            'approval_request_id': approval.id,
        }
