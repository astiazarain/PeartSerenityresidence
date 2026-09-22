# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AiAgent(models.Model):
    _name = 'ai.agent'
    _description = 'Agente de IA registrado en ARIA'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    code = fields.Char(
        required=True, index=True,
        help="Identificador técnico estable, usado por el Coordinador para enrutar. "
             "Ej: coordinator, social_media, customer_service.",
    )
    sequence = fields.Integer(default=10)
    description = fields.Text()
    active = fields.Boolean(default=True)
    is_coordinator = fields.Boolean(
        string='Es el Coordinador',
        help="Solo debe haber un agente marcado como Coordinador. Recibe toda "
             "solicitud entrante y delega a los demás agentes.",
    )
    ai_provider_id = fields.Many2one(
        'ai.provider.config', string='Proveedor de IA por defecto',
        help="Usado por este agente cuando una herramienta no especifica uno propio.",
    )
    tool_ids = fields.One2many('ai.agent.tool', 'agent_id', string='Herramientas')
    tool_count = fields.Integer(compute='_compute_tool_count')

    # Reglas de escalado / conversación con terceros externos (p.ej. clientes).
    # Vacío para agentes que solo conversan con el usuario interno.
    external_facing = fields.Boolean(
        string='Atiende a terceros externos',
        help="Marcar para agentes que conversan directamente con alguien que no es "
             "el usuario del sistema (p. ej. un cliente en el chat del sitio web). "
             "Este tipo de agente debe tener siempre disponible una herramienta de "
             "escalado a humano y nunca debe responder con información no verificada.",
    )
    escalation_tool_id = fields.Many2one(
        'ai.agent.tool', string='Herramienta de escalado',
        domain="[('agent_id', '=', id)]",
        help="Herramienta que este agente ejecuta cuando no puede resolver la "
             "consulta con confianza. Obligatoria si 'Atiende a terceros externos' "
             "está marcado.",
    )

    _code_unique = models.Constraint(
        'unique(code)',
        'Ya existe un agente con ese código.',
    )

    def _compute_tool_count(self):
        for agent in self:
            agent.tool_count = len(agent.tool_ids)

    @api.constrains('is_coordinator')
    def _check_single_coordinator(self):
        coordinators = self.search([('is_coordinator', '=', True)])
        if len(coordinators) > 1:
            from odoo.exceptions import ValidationError
            raise ValidationError("Solo puede existir un agente marcado como Coordinador.")

    @api.constrains('external_facing', 'escalation_tool_id')
    def _check_escalation_tool_required(self):
        from odoo.exceptions import ValidationError
        for agent in self:
            if agent.external_facing and not agent.escalation_tool_id:
                raise ValidationError(
                    "El agente '%s' atiende a terceros externos: debe tener una "
                    "herramienta de escalado a humano configurada." % agent.name
                )

    def get_provider(self):
        """Proveedor de IA efectivo para este agente, con fallback al default global."""
        self.ensure_one()
        provider = self.ai_provider_id or self.env['ai.provider.config'].get_default_provider()
        # ai_agent_id: la auditoría de la llamada queda ligada al agente.
        # ai_external_facing: un agente que atiende a terceros solo degrada
        # a Ollama local (ver ai.provider.config._fallback_chain).
        return provider.with_context(ai_agent_id=self.id, ai_external_facing=self.external_facing)
