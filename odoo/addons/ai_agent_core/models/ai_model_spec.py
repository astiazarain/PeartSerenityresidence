# -*- coding: utf-8 -*-
from odoo import api, fields, models

from odoo.addons.ai_agent_core.llm.registry import PROVIDER_SELECTION

# Campos que la API de un proveedor puede informar sobre un modelo.
API_FIELDS = (
    'context_window', 'max_output_tokens', 'input_cost_per_mtok',
    'output_cost_per_mtok', 'pricing_known', 'supports_tools',
    'free_rpm', 'free_rpd', 'free_tpm', 'free_tpd',
)


class AiModelSpec(models.Model):
    """Ficha de referencia de un modelo: contexto, precio y límites.

    Es independiente de los proveedores configurados (``ai.provider.config``)
    porque describe el modelo, no la cuenta: la ven igual dos compañías con
    claves distintas. Precios y límites cambian cada pocos meses, así que
    son datos editables con su fuente y su fecha, no constantes de código.
    """
    _name = 'ai.model.spec'
    _description = 'Especificación de un modelo de IA (contexto, precio, límites)'
    _order = 'provider, model_id'
    _rec_name = 'model_id'

    provider = fields.Selection(PROVIDER_SELECTION, required=True)
    model_id = fields.Char(string='ID del modelo', required=True)
    name = fields.Char(string='Nombre')
    active = fields.Boolean(default=True)

    # aggregator=None: agrupar por proveedor sumaría ventanas, precios y
    # límites de modelos distintos, cifras sin significado.
    context_window = fields.Integer(string='Ventana de contexto (tokens)', aggregator=None)
    max_output_tokens = fields.Integer(string='Salida máxima (tokens)', aggregator=None)
    input_cost_per_mtok = fields.Float(
        string='USD / 1M tokens de entrada', digits=(16, 6), aggregator=None)
    output_cost_per_mtok = fields.Float(
        string='USD / 1M tokens de salida', digits=(16, 6), aggregator=None)
    pricing_known = fields.Boolean(
        string='Precio conocido', default=False,
        help='Sin marcar, el costo de las llamadas queda vacío en la auditoría '
             'en lugar de calcularse como 0.')

    free_rpm = fields.Integer(string='Tier gratuito: peticiones/min', aggregator=None)
    free_rpd = fields.Integer(string='Tier gratuito: peticiones/día', aggregator=None)
    free_tpm = fields.Integer(string='Tier gratuito: tokens/min', aggregator=None)
    free_tpd = fields.Integer(string='Tier gratuito: tokens/día', aggregator=None)

    supports_tools = fields.Boolean(string='Tool calling')
    supports_streaming = fields.Boolean(string='Streaming', default=True)

    source = fields.Selection(
        [
            ('official', 'Documentación oficial'),
            ('secondary', 'Fuente secundaria'),
            ('api', 'API del proveedor'),
            ('manual', 'Manual'),
        ],
        string='Fuente', default='manual', required=True,
        help='"API del proveedor": se reescribe en cada actualización del '
             'catálogo. Las demás solo se completan donde estén vacías, para '
             'no pisar un precio verificado a mano.')
    source_url = fields.Char(string='URL de la fuente')
    verified_on = fields.Date(string='Verificado el')
    notes = fields.Text(string='Notas')

    _provider_model_uniq = models.Constraint(
        'unique(provider, model_id)',
        'Ya hay una especificación para ese modelo de ese proveedor.',
    )

    @api.model
    def _lookup(self, provider, model_id):
        if not provider or not model_id:
            return self.browse()
        return self.with_context(active_test=False).search(
            [('provider', '=', provider), ('model_id', '=', model_id)], limit=1)

    def _estimate_cost(self, input_tokens, output_tokens):
        """USD = entrada × precio_entrada / 1e6 + salida × precio_salida / 1e6.
        None si no hay ficha o su precio no es conocido."""
        if not self or not self.pricing_known:
            return None
        return (
            (input_tokens or 0) * self.input_cost_per_mtok
            + (output_tokens or 0) * self.output_cost_per_mtok
        ) / 1_000_000

    @api.model
    def _upsert_from_api(self, provider, entries):
        """Vuelca lo que la API informa de cada modelo. Crea la ficha si no
        existe; si su fuente es la API la reescribe; si no, solo rellena
        huecos."""
        entries = [entry for entry in entries if entry.get('spec')]
        if not entries:
            return
        existing = {
            spec.model_id: spec
            for spec in self.with_context(active_test=False).search([
                ('provider', '=', provider),
                ('model_id', 'in', [entry['model_id'] for entry in entries]),
            ])
        }
        today = fields.Date.context_today(self)
        to_create = []
        for entry in entries:
            values = {k: v for k, v in entry['spec'].items() if k in API_FIELDS}
            spec = existing.get(entry['model_id'])
            if not spec:
                to_create.append(dict(
                    values, provider=provider, model_id=entry['model_id'],
                    name=entry.get('display_name'), source='api', verified_on=today,
                    pricing_known=values.get('pricing_known', False),
                ))
            elif spec.source == 'api':
                spec.write(dict(values, verified_on=today))
            else:
                gaps = {k: v for k, v in values.items() if k != 'pricing_known' and not spec[k]}
                if gaps:
                    spec.write(gaps)
        if to_create:
            self.create(to_create)
