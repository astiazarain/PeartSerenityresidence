# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AiAgentTool(models.Model):
    _name = 'ai.agent.tool'
    _description = 'Herramienta registrada para un agente de IA'
    _order = 'agent_id, risk_level, sequence, id'

    name = fields.Char(
        required=True, index=True,
        help="Nombre técnico estable de la herramienta, ej: publicar_ahora, "
             "consultar_estado_pedido. Usado por el Coordinador y en ai.audit.log.",
    )
    label = fields.Char(required=True, translate=True, help="Nombre visible para humanos.")
    sequence = fields.Integer(default=10)
    agent_id = fields.Many2one('ai.agent', required=True, ondelete='cascade', index=True)
    description = fields.Text(help="Descripción de qué hace, para el HUD y para el LLM.")
    active = fields.Boolean(default=True)

    risk_level = fields.Selection(
        [('0', '0 - Consulta'), ('1', '1 - Preparación'),
         ('2', '2 - Sensible'), ('3', '3 - Crítica')],
        required=True, default='0',
    )
    requires_approval = fields.Boolean(compute='_compute_requires_approval', store=True)

    # Referencia al método real que implementa la herramienta. Se resuelve por
    # nombre (no por referencia directa a Python) para que módulos de dominio
    # puedan registrar herramientas sin que este módulo dependa de ellos.
    target_model = fields.Char(
        required=True,
        help="Modelo Odoo sobre el que se invoca el método, ej: social.media.post",
    )
    target_method = fields.Char(
        required=True,
        help="Nombre del método a invocar en target_model, ej: action_publish_now",
    )
    required_group_id = fields.Many2one(
        'res.groups', string='Grupo requerido',
        help="Si se define, solo usuarios de este grupo pueden invocar la herramienta.",
    )

    idempotent = fields.Boolean(
        default=False,
        help="Si está marcado, reintentar con la misma clave de idempotencia no "
             "duplica el efecto. Las herramientas de escritura deberían serlo.",
    )
    requires_existing_record = fields.Boolean(
        string='Requiere un registro existente',
        default=False,
        help="Marcar si la herramienta necesita operar sobre un target_res_id "
             "concreto (o un parámetro equivalente como un pedido específico) "
             "que el Coordinador no puede inventar a partir de un mensaje en "
             "lenguaje natural. El Coordinador excluye estas herramientas de "
             "su enrutamiento por texto libre — evita crear una aprobación o "
             "ejecución condenada a fallar por falta de contexto. Se siguen "
             "invocando normalmente desde flujos que ya conocen el registro "
             "(botones de la UI, el widget de atención al cliente).",
    )

    @api.depends('risk_level')
    def _compute_requires_approval(self):
        for tool in self:
            tool.requires_approval = tool.risk_level in ('2', '3')

    def user_can_invoke(self, user):
        self.ensure_one()
        if not self.active:
            return False
        # all_group_ids, no group_ids: incluye los grupos implicados
        # (implied_ids). Un usuario con un rol que implica otros pasa el
        # chequeo aunque el grupo exigido no esté asignado directamente.
        if self.required_group_id and self.required_group_id not in user.all_group_ids:
            return False
        return True

    def execute(self, record_id=False, params=None, idempotency_key=False):
        """Invoca la herramienta subyacente. No hace ninguna comprobación de
        riesgo/aprobación por sí misma — eso es responsabilidad de quien llama
        (el Coordinador o el motor de aprobaciones), que debe llamar aquí solo
        una vez que la operación está autorizada a ejecutarse.
        """
        self.ensure_one()
        params = params or {}
        model = self.env[self.target_model]
        target = model.browse(record_id) if record_id else model
        method = getattr(target, self.target_method)
        return method(**params) if params else method()
