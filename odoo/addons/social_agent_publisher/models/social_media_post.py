# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class SocialMediaPost(models.Model):
    _name = 'social.media.post'
    _description = 'Publicación en redes sociales'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date desc, id desc'

    name = fields.Char(
        string='Referencia', compute='_compute_name', store=True
    )
    topic = fields.Char(
        string='Tema / Instrucción',
        help='Breve descripción de qué debe publicarse (se usa como prompt para la IA).',
    )
    content = fields.Text(string='Contenido', tracking=True)
    image = fields.Binary(string='Imagen adjunta', attachment=True)
    image_filename = fields.Char(string='Nombre de archivo')
    image_url = fields.Char(
        string='URL pública de imagen',
        help='Necesaria para redes como Instagram, que requieren una imagen accesible por URL.',
    )

    ai_provider_id = fields.Many2one(
        'ai.provider.config', string='Proveedor de IA'
    )
    ai_generated = fields.Boolean(string='Generado con IA', default=False)

    account_ids = fields.Many2many(
        'social.media.account', string='Cuentas destino', required=True
    )
    line_ids = fields.One2many(
        'social.media.post.line', 'post_id', string='Estado por cuenta'
    )

    scheduled_date = fields.Datetime(string='Fecha programada', tracking=True)
    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('scheduled', 'Programado'),
            ('publishing', 'Publicando'),
            ('done', 'Publicado'),
            ('error', 'Con errores'),
            ('cancelled', 'Cancelado'),
        ],
        default='draft',
        tracking=True,
        required=True,
    )
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        'res.users', string='Responsable', default=lambda self: self.env.user
    )

    # Analítica / reportes
    total_accounts = fields.Integer(compute='_compute_analytics', string='Cuentas')
    success_count = fields.Integer(compute='_compute_analytics', string='Exitosas')
    error_count = fields.Integer(compute='_compute_analytics', string='Con error')
    total_likes = fields.Integer(compute='_compute_analytics', string='Me gusta')
    total_comments = fields.Integer(compute='_compute_analytics', string='Comentarios')
    total_shares = fields.Integer(compute='_compute_analytics', string='Compartidos')
    total_engagement = fields.Integer(
        compute='_compute_analytics', string='Interacciones totales'
    )

    @api.depends(
        'line_ids.state', 'line_ids.likes_count', 'line_ids.comments_count',
        'line_ids.shares_count',
    )
    def _compute_analytics(self):
        for rec in self:
            lines = rec.line_ids
            rec.total_accounts = len(lines)
            rec.success_count = len(lines.filtered(lambda l: l.state == 'success'))
            rec.error_count = len(lines.filtered(lambda l: l.state == 'error'))
            rec.total_likes = sum(lines.mapped('likes_count'))
            rec.total_comments = sum(lines.mapped('comments_count'))
            rec.total_shares = sum(lines.mapped('shares_count'))
            rec.total_engagement = rec.total_likes + rec.total_comments + rec.total_shares

    @api.depends('topic', 'create_date')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.topic or 'Publicación #%s' % (rec.id or 'Nuevo')

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def action_generate_with_ai(self):
        self.ensure_one()
        if not self.ai_provider_id:
            raise UserError('Selecciona un proveedor de IA (Claude o Gemini) primero.')
        if not self.topic:
            raise UserError('Escribe un tema/instrucción para que la IA genere el contenido.')
        generated = self.ai_provider_id.generate_content(self.topic)
        self.write({'content': generated, 'ai_generated': True})
        return True

    def action_schedule(self):
        for rec in self:
            if not rec.content:
                raise UserError('No se puede programar una publicación sin contenido.')
            if not rec.account_ids:
                raise UserError('Selecciona al menos una cuenta destino.')
            rec._sync_lines()
            rec.state = 'scheduled'
        return True

    def action_publish_now(self):
        for rec in self:
            if not rec.content:
                raise UserError('No se puede publicar una publicación sin contenido.')
            if not rec.account_ids:
                raise UserError('Selecciona al menos una cuenta destino.')
            rec._sync_lines()
            rec._publish()
        return True

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

    def action_fetch_metrics(self):
        for rec in self:
            rec.line_ids.action_fetch_metrics()
        return True

    def _sync_lines(self):
        """Crea líneas de estado para las cuentas que aún no las tengan."""
        for rec in self:
            existing_accounts = rec.line_ids.mapped('account_id')
            missing = rec.account_ids - existing_accounts
            for account in missing:
                self.env['social.media.post.line'].create(
                    {'post_id': rec.id, 'account_id': account.id, 'state': 'pending'}
                )

    def _publish(self):
        """Publica el contenido en todas las cuentas asociadas."""
        for rec in self:
            rec.state = 'publishing'
            any_error = False
            for line in rec.line_ids.filtered(lambda l: l.state != 'success'):
                success, message, remote_id = line.account_id.publish(rec)
                line.write(
                    {
                        'state': 'success' if success else 'error',
                        'response_message': message,
                        'remote_post_id': remote_id or False,
                        'published_date': fields.Datetime.now() if success else False,
                    }
                )
                if not success:
                    any_error = True
            rec.state = 'error' if any_error else 'done'

    # ------------------------------------------------------------------
    # Cron
    # ------------------------------------------------------------------

    @api.model
    def _cron_publish_scheduled(self):
        now = fields.Datetime.now()
        posts = self.search(
            [('state', '=', 'scheduled'), ('scheduled_date', '<=', now)]
        )
        posts._publish()
