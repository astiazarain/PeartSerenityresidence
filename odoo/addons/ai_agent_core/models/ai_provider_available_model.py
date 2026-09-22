# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AiProviderAvailableModel(models.Model):
    _name = 'ai.provider.available.model'
    _description = 'Modelo de IA disponible (catálogo obtenido de la API del proveedor)'
    _order = 'kind, name'

    provider_config_id = fields.Many2one(
        'ai.provider.config', string='Proveedor de IA',
        required=True, ondelete='cascade',
    )
    model_id = fields.Char(string='ID del modelo', required=True)
    name = fields.Char(string='Nombre')
    kind = fields.Selection(
        [('text', 'Texto'), ('image', 'Imagen')],
        string='Tipo', required=True,
    )
    active = fields.Boolean(
        string='Seleccionable', default=True,
        help='Solo los modelos marcados aquí aparecen en los campos '
             '"Modelo" / "Modelo de imagen" del proveedor.',
    )
    spec_id = fields.Many2one(
        'ai.model.spec', string='Especificación', compute='_compute_spec_id',
        help='Ficha de ai.model.spec con el mismo proveedor e ID de modelo.',
    )
    context_window = fields.Integer(related='spec_id.context_window', aggregator=None)
    input_cost_per_mtok = fields.Float(related='spec_id.input_cost_per_mtok', aggregator=None)
    output_cost_per_mtok = fields.Float(related='spec_id.output_cost_per_mtok', aggregator=None)
    supports_tools = fields.Boolean(related='spec_id.supports_tools')
    supports_streaming = fields.Boolean(related='spec_id.supports_streaming')

    _model_uniq = models.Constraint(
        'unique(provider_config_id, model_id, kind)',
        'Ese modelo ya está registrado para este proveedor.',
    )

    @api.depends('provider_config_id.provider', 'model_id')
    def _compute_spec_id(self):
        specs = self.env['ai.model.spec'].with_context(active_test=False).search([
            ('provider', 'in', self.provider_config_id.mapped('provider')),
            ('model_id', 'in', self.mapped('model_id')),
        ])
        by_key = {(spec.provider, spec.model_id): spec for spec in specs}
        for rec in self:
            rec.spec_id = by_key.get((rec.provider_config_id.provider, rec.model_id), False)
