# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SocialMediaPostLine(models.Model):
    _name = 'social.media.post.line'
    _description = 'Estado de publicación por cuenta'
    _order = 'id'

    post_id = fields.Many2one(
        'social.media.post', string='Publicación', required=True, ondelete='cascade'
    )
    account_id = fields.Many2one(
        'social.media.account', string='Cuenta', required=True
    )
    platform = fields.Selection(related='account_id.platform', string='Red', store=True)
    state = fields.Selection(
        [
            ('pending', 'Pendiente'),
            ('success', 'Publicado'),
            ('error', 'Error'),
        ],
        default='pending',
        required=True,
    )
    response_message = fields.Text(string='Respuesta / Error')
    published_date = fields.Datetime(string='Fecha de publicación')

    # Analítica / reportes
    remote_post_id = fields.Char(
        string='ID remoto',
        help='ID o URN que la red social devolvió al publicar. Se usa para '
             'consultar las métricas (likes, comentarios, etc.) después.',
    )
    likes_count = fields.Integer(string='Me gusta', default=0)
    comments_count = fields.Integer(string='Comentarios', default=0)
    shares_count = fields.Integer(string='Compartidos', default=0)
    impressions_count = fields.Integer(string='Impresiones / Alcance', default=0)
    engagement_count = fields.Integer(
        string='Interacciones', compute='_compute_engagement_count', store=True,
        help='Suma de me gusta + comentarios + compartidos.',
    )
    metrics_updated_at = fields.Datetime(string='Métricas actualizadas')
    metrics_supported = fields.Boolean(
        compute='_compute_metrics_supported',
        help='Indica si esta red permite consultar métricas automáticamente.',
    )

    @api.depends('likes_count', 'comments_count', 'shares_count')
    def _compute_engagement_count(self):
        for rec in self:
            rec.engagement_count = (
                (rec.likes_count or 0) + (rec.comments_count or 0) + (rec.shares_count or 0)
            )

    @api.depends('platform')
    def _compute_metrics_supported(self):
        for rec in self:
            rec.metrics_supported = rec.platform in ('facebook', 'instagram', 'linkedin', 'twitter')

    def action_fetch_metrics(self):
        """Consulta y actualiza las métricas de esta línea contra la red social."""
        for rec in self.filtered(lambda l: l.state == 'success' and l.remote_post_id):
            rec.account_id._fetch_metrics(rec)
        return True

    @api.model
    def _cron_fetch_metrics(self):
        from datetime import timedelta
        lines = self.search(
            [
                ('state', '=', 'success'),
                ('remote_post_id', '!=', False),
                ('platform', 'in', ('facebook', 'instagram', 'linkedin', 'twitter')),
                ('published_date', '>=', fields.Datetime.now() - timedelta(days=30)),
            ]
        )
        lines.action_fetch_metrics()
