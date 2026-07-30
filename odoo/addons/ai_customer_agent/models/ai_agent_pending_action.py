from odoo import api, fields, models
from odoo.exceptions import UserError


class AIAgentPendingAction(models.Model):
    _name = "ai.agent.pending_action"
    _description = "Acción del agente de IA pendiente de aprobación"
    _order = "create_date desc"

    session_id = fields.Char(string="Sesión del chat")
    order_id = fields.Many2one("sale.order", string="Pedido", required=True)
    action_type = fields.Selection([
        ("cancel_order", "Cancelar pedido"),
        ("apply_discount", "Aplicar descuento de compensación"),
    ], string="Acción propuesta", required=True)
    reason = fields.Text(string="Motivo (según el cliente)")
    discount_percent = fields.Float(string="% de descuento propuesto")
    state = fields.Selection([
        ("pending", "Pendiente"),
        ("approved", "Aprobada y ejecutada"),
        ("rejected", "Rechazada"),
        ("error", "Error al ejecutar"),
    ], string="Estado", default="pending", required=True)
    result_note = fields.Text(string="Resultado", readonly=True)

    def action_approve(self):
        for rec in self:
            if rec.state != "pending":
                continue
            try:
                rec._execute()
                rec.state = "approved"
            except Exception as exc:
                rec.state = "error"
                rec.result_note = str(exc)
        return True

    def action_reject(self):
        self.write({"state": "rejected"})
        return True

    def _execute(self):
        """Ejecuta la acción sobre el pedido. Se usa tanto para aprobación
        manual como para ejecución automática (cuando no se requiere
        aprobación)."""
        self.ensure_one()
        order = self.order_id
        if not order:
            raise UserError("No se encontró el pedido asociado.")

        if self.action_type == "cancel_order":
            if order.state == "cancel":
                self.result_note = "El pedido ya estaba cancelado."
                return
            if hasattr(order, "action_cancel"):
                order.action_cancel()
            else:
                order.write({"state": "cancel"})
            self.result_note = f"Pedido {order.name} cancelado correctamente."

        elif self.action_type == "apply_discount":
            percent = self.discount_percent or 0.0
            if percent <= 0:
                raise UserError("El porcentaje de descuento debe ser mayor a 0.")
            for line in order.order_line:
                if not line.display_type:
                    line.discount = percent
            self.result_note = f"Descuento del {percent}% aplicado a {order.name}."

    @api.model
    def execute_immediately(self, order, action_type, reason=None, discount_percent=0.0):
        """Crea el registro ya en estado ejecutado, usado cuando la
        configuración no requiere aprobación humana."""
        rec = self.create({
            "order_id": order.id,
            "action_type": action_type,
            "reason": reason,
            "discount_percent": discount_percent,
            "state": "pending",
        })
        rec.action_approve()
        return rec
