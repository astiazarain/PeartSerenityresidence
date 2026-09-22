# -*- coding: utf-8 -*-
import json
import logging
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)


class AiApprovalRequest(models.Model):
    _name = 'ai.approval.request'
    _description = 'Solicitud de aprobación para una operación de un agente de IA'
    # mail.thread es necesario para que el tracking=True del campo state
    # funcione: sin él Odoo lo ignora en silencio y se pierde el rastro de
    # quién aprobó o rechazó cada operación de riesgo — justo lo que la
    # gobernanza de ARIA necesita auditar.
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(compute='_compute_name', store=True)
    conversation_id = fields.Many2one('ai.conversation', string='Conversación')
    requesting_user_id = fields.Many2one(
        'res.users', string='Solicitado por', default=lambda self: self.env.user, required=True,
    )
    approver_user_id = fields.Many2one('res.users', string='Aprobado/rechazado por')
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True,
    )

    agent_id = fields.Many2one('ai.agent', required=True)
    tool_id = fields.Many2one('ai.agent.tool', required=True)
    risk_level = fields.Selection(related='tool_id.risk_level', store=True)

    target_model = fields.Char(related='tool_id.target_model', store=True)
    target_res_id = fields.Integer(string='ID del registro objetivo')

    payload_json = fields.Text(
        string='Parámetros (JSON)',
        help="Parámetros con los que se ejecutará la herramienta si se aprueba.",
    )
    preview_text = fields.Text(
        string='Vista previa',
        help="Resumen legible de lo que va a ocurrir, mostrado al aprobador.",
    )

    state = fields.Selection(
        [('draft', 'Borrador'), ('pending', 'Pendiente'), ('approved', 'Aprobada'),
         ('rejected', 'Rechazada'), ('executing', 'Ejecutando'),
         ('executed', 'Ejecutada'), ('error', 'Error'),
         ('cancelled', 'Cancelada'), ('expired', 'Expirada')],
        default='draft', required=True, tracking=True,
    )

    requested_at = fields.Datetime(default=fields.Datetime.now)
    approved_at = fields.Datetime()
    executed_at = fields.Datetime()

    execution_result_json = fields.Text(string='Resultado (JSON)')
    error_message = fields.Text()
    idempotency_key = fields.Char(index=True)

    def _compute_name(self):
        for rec in self:
            rec.name = "%s - %s" % (rec.tool_id.label or '?', rec.agent_id.name or '?')

    def get_payload(self):
        self.ensure_one()
        return json.loads(self.payload_json) if self.payload_json else {}

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def action_submit(self):
        """Pasa de borrador a pendiente de aprobación (visible en el panel Vault)."""
        for rec in self:
            if rec.state != 'draft':
                continue
            rec.write({'state': 'pending', 'requested_at': fields.Datetime.now()})

    def action_approve(self):
        for rec in self:
            if rec.state != 'pending':
                raise UserError("Solo se pueden aprobar solicitudes en estado pendiente.")
            if rec.risk_level == '3' and self.env.user == rec.requesting_user_id:
                raise UserError(
                    "Las operaciones críticas (nivel 3) no pueden ser aprobadas por "
                    "quien las solicitó."
                )
            rec.write({
                'state': 'approved',
                'approver_user_id': self.env.user.id,
                'approved_at': fields.Datetime.now(),
            })
            rec._execute()

    def action_reject(self):
        for rec in self:
            if rec.state != 'pending':
                raise UserError("Solo se pueden rechazar solicitudes en estado pendiente.")
            rec.write({
                'state': 'rejected',
                'approver_user_id': self.env.user.id,
            })

    def action_cancel(self):
        for rec in self:
            if rec.state in ('executed', 'executing'):
                raise UserError("No se puede cancelar una solicitud ya ejecutada.")
            rec.state = 'cancelled'

    # ------------------------------------------------------------------
    # Ejecución
    # ------------------------------------------------------------------

    def _execute(self):
        self.ensure_one()
        if self.state != 'approved':
            raise UserError("Solo se ejecutan solicitudes aprobadas.")

        # Revalidación de idempotencia: si ya existe una ejecución exitosa con
        # la misma clave, no se repite la operación.
        if self.idempotency_key:
            twin = self.search([
                ('idempotency_key', '=', self.idempotency_key),
                ('state', '=', 'executed'),
                ('id', '!=', self.id),
            ], limit=1)
            if twin:
                self.write({
                    'state': 'executed',
                    'executed_at': fields.Datetime.now(),
                    'execution_result_json': json.dumps({
                        'skipped': True,
                        'reason': 'idempotency_key ya ejecutada en solicitud #%d' % twin.id,
                    }),
                })
                return

        # Revalidación de permisos justo antes de ejecutar (el usuario pudo
        # haber perdido el permiso entre la solicitud y la aprobación).
        if not self.tool_id.user_can_invoke(self.requesting_user_id):
            self.write({'state': 'error', 'error_message': 'Permiso revocado antes de ejecutar.'})
            raise AccessError("El usuario solicitante ya no tiene permiso para esta acción.")

        self.state = 'executing'
        audit_vals = {
            'agent_id': self.agent_id.id,
            'tool_name': self.tool_id.name,
            'user_id': self.requesting_user_id.id,
            'company_id': self.company_id.id,
            'conversation_id': self.conversation_id.id,
            'approval_request_id': self.id,
            'target_model': self.target_model,
            'target_res_id': self.target_res_id,
            'request_json': self.payload_json,
        }
        start = fields.Datetime.now()
        try:
            result = self.tool_id.execute(
                record_id=self.target_res_id or False,
                params=self.get_payload(),
            )
            self.write({
                'state': 'executed',
                'executed_at': fields.Datetime.now(),
                'execution_result_json': json.dumps(result) if result is not None else 'null',
            })
            audit_vals.update({
                'status': 'success',
                'response_json': self.execution_result_json,
            })
        except Exception as exc:  # noqa: BLE001 — se registra y se re-lanza controlado
            _logger.exception("Error ejecutando ai.approval.request #%s", self.id)
            self.write({'state': 'error', 'error_message': str(exc)})
            audit_vals.update({
                'status': 'error',
                'error_type': type(exc).__name__,
                'error_message': str(exc),
            })
            raise
        finally:
            duration_ms = int(
                (fields.Datetime.now() - start).total_seconds() * 1000
            )
            audit_vals['duration_ms'] = duration_ms
            self.env['ai.audit.log'].sudo().create(audit_vals)

    @api.model
    def _cron_expire_stale_requests(self, hours=48):
        """Expira solicitudes pendientes que nadie atendió, para que no queden
        indefinidamente accionables en el panel Vault."""
        threshold = fields.Datetime.now() - timedelta(hours=hours)
        stale = self.search([('state', '=', 'pending'), ('requested_at', '<', threshold)])
        stale.write({'state': 'expired'})
