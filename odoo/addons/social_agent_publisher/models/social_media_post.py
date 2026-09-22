# -*- coding: utf-8 -*-
import json
import logging
import re

from odoo import api, fields, models
from odoo.exceptions import UserError

from ._ai_audit_helper import log_agent_audit

_logger = logging.getLogger(__name__)

TITLE_MAX_LENGTH = 80
TITLE_SYSTEM_PROMPT = (
    "Eres editor de redes sociales. Escribe un título breve y descriptivo "
    "(máximo 8 palabras) que identifique esta publicación en un tablero "
    "interno. Responde solo con el título: sin comillas, sin emojis, sin "
    "hashtags y sin punto final."
)


class SocialMediaPost(models.Model):
    _name = 'social.media.post'
    _description = 'Publicación en redes sociales'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date desc, id desc'

    name = fields.Char(
        string='Referencia', compute='_compute_name', store=True,
        help='Título de la publicación; si no tiene, "Publicación #<id>".',
    )
    title = fields.Char(
        string='Título', tracking=True,
        help='Nombre con el que se identifica la publicación en el tablero. '
             'Si está vacío al pulsar "Generar con IA", la IA lo propone a '
             'partir del contenido generado.',
    )
    topic = fields.Text(
        string='Tema / Instrucción',
        help='Qué debe publicarse (se usa como prompt para la IA, tanto para '
             'el texto como para la imagen).',
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

    @api.depends('title')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.title or 'Publicación #%s' % (rec.id or 'Nuevo')

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _check_ai_ready(self):
        self.ensure_one()
        if not self.ai_provider_id:
            raise UserError('Selecciona un proveedor de IA (Claude, Gemini o ChatGPT) primero.')
        if not self.topic:
            raise UserError('Escribe un tema/instrucción para que la IA genere el contenido.')

    def action_generate_with_ai(self):
        """Genera el texto y, si el proveedor tiene modelo de imagen, la
        imagen. Si la publicación no tiene título, la IA lo propone. Un
        fallo de la imagen o del título no descarta el texto: se avisa en
        el chatter."""
        self._check_ai_ready()
        try:
            generated = self.ai_provider_id.generate_content(self.topic)
        except Exception as exc:
            log_agent_audit(
                self.env, 'generar_contenido_ia', status='error',
                request_json=json.dumps({'post_id': self.id, 'topic': self.topic}),
                error_type=type(exc).__name__, error_message=str(exc),
            )
            raise
        vals = {'content': generated, 'ai_generated': True}
        if not self.title:
            title = self._generate_title(generated)
            if title:
                vals['title'] = title
        if self.ai_provider_id.image_model_name_id:
            try:
                vals.update(self._generate_image_vals())
            except Exception as exc:
                self.message_post(
                    body='No se pudo generar la imagen automáticamente: %s' % exc
                )
        self.write(vals)
        log_agent_audit(
            self.env, 'generar_contenido_ia', status='success',
            request_json=json.dumps({'post_id': self.id, 'topic': self.topic}),
        )
        return True

    def action_generate_image(self):
        """Genera (o vuelve a generar) solo la imagen, sin tocar el texto
        ni el título."""
        self._check_ai_ready()
        if not self.ai_provider_id.image_model_name_id:
            raise UserError(
                'El proveedor de IA "%s" no tiene "Modelo de imagen" configurado. '
                'Elígelo en Agentes de IA > Proveedores.' % self.ai_provider_id.name
            )
        self.write(self._generate_image_vals())
        return True

    def _generate_image_vals(self):
        self.ensure_one()
        request_json = json.dumps({'post_id': self.id, 'topic': self.topic})
        try:
            image_data, image_name = self.ai_provider_id.generate_image(self.topic)
        except Exception as exc:
            log_agent_audit(
                self.env, 'generar_imagen_ia', status='error', request_json=request_json,
                error_type=type(exc).__name__, error_message=str(exc),
            )
            raise
        log_agent_audit(self.env, 'generar_imagen_ia', status='success', request_json=request_json)
        return {'image': image_data, 'image_filename': image_name}

    def _generate_title(self, content):
        self.ensure_one()
        prompt = 'Instrucción: %s\n\nPublicación:\n%s' % (self.topic, content)
        try:
            raw = self.ai_provider_id.generate_content(prompt, system_prompt=TITLE_SYSTEM_PROMPT)
        except Exception as exc:
            _logger.warning('No se pudo generar el título de la publicación %s: %s', self.id, exc)
            self.message_post(body='No se pudo generar el título automáticamente: %s' % exc)
            return False
        return self._clean_title(raw)

    @api.model
    def _clean_title(self, raw):
        """Primera línea con texto, sin markdown, comillas, prefijo
        "Título:" ni punto final, recortada a TITLE_MAX_LENGTH por palabra."""
        line = next((l for l in (raw or '').splitlines() if l.strip()), '')
        line = re.sub(r'^\s*(#+\s*)?(\*\*)?\s*t[ií]tulo\s*:\s*', '', line, flags=re.IGNORECASE)
        line = re.sub(r'\s+', ' ', line.strip(' \t*_#"\'«»“”`.'))
        if len(line) > TITLE_MAX_LENGTH:
            line = line[:TITLE_MAX_LENGTH].rsplit(' ', 1)[0]
        return line.strip()

    def action_schedule(self):
        for rec in self:
            try:
                if not rec.content:
                    raise UserError('No se puede programar una publicación sin contenido.')
                if not rec.account_ids:
                    raise UserError('Selecciona al menos una cuenta destino.')
                rec._sync_lines()
                rec.state = 'scheduled'
            except Exception as exc:
                log_agent_audit(
                    self.env, 'programar_publicacion', status='error',
                    request_json=json.dumps({'post_id': rec.id}),
                    error_type=type(exc).__name__, error_message=str(exc),
                )
                raise
            log_agent_audit(
                self.env, 'programar_publicacion', status='success',
                request_json=json.dumps({'post_id': rec.id}),
            )
        return True

    def action_publish_now(self):
        for rec in self:
            try:
                if not rec.content:
                    raise UserError('No se puede publicar una publicación sin contenido.')
                if not rec.account_ids:
                    raise UserError('Selecciona al menos una cuenta destino.')
                rec._sync_lines()
                rec._publish()
            except Exception as exc:
                log_agent_audit(
                    self.env, 'publicar_ahora', status='error',
                    request_json=json.dumps({'post_id': rec.id}),
                    error_type=type(exc).__name__, error_message=str(exc),
                )
                raise
            # _publish() no lanza excepción ante fallos parciales por cuenta:
            # deja rec.state en 'error' si alguna cuenta falló. La auditoría
            # se basa en ese estado final, no en si hubo excepción.
            log_agent_audit(
                self.env, 'publicar_ahora',
                status='error' if rec.state == 'error' else 'success',
                request_json=json.dumps({'post_id': rec.id}),
                response_json=json.dumps({
                    'lines': [
                        {'account': l.account_id.name, 'state': l.state, 'message': l.response_message}
                        for l in rec.line_ids
                    ]
                }),
                error_message=('Una o más cuentas fallaron al publicar.' if rec.state == 'error' else None),
            )
        return True

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

    def action_fetch_metrics(self):
        for rec in self:
            try:
                rec.line_ids.action_fetch_metrics()
            except Exception as exc:
                log_agent_audit(
                    self.env, 'consultar_metricas', status='error',
                    request_json=json.dumps({'post_id': rec.id}),
                    error_type=type(exc).__name__, error_message=str(exc),
                )
                raise
            log_agent_audit(
                self.env, 'consultar_metricas', status='success',
                request_json=json.dumps({'post_id': rec.id}),
            )
        return True

    # ------------------------------------------------------------------
    # Wrappers para el catálogo de herramientas de ai_agent_core (ARIA).
    # Existen porque ai.agent.tool.execute() invoca métodos con kwargs
    # simples (model.method(**params)); create() y action_schedule() no
    # encajan directamente en esa convención.
    # ------------------------------------------------------------------

    @api.model
    def action_create_draft(self, topic=False, account_ids=False, ai_provider_id=False):
        """Herramienta 'crear_publicacion_borrador'. Devuelve el id creado.

        Si hay tema y proveedor de IA (el pasado o el que ai_provider_id
        toma por default en el registro recién creado), genera el
        contenido de una — sin este paso, pedir "generá una publicación
        sobre X" por el chat dejaría un borrador vacío, obligando a un
        segundo llamado manual a generar_contenido_ia que el Coordinador
        no encadena por su cuenta."""
        if not account_ids:
            raise UserError('Debes indicar al menos una cuenta destino.')
        vals = {
            'topic': topic,
            'account_ids': [(6, 0, account_ids)],
        }
        if ai_provider_id:
            vals['ai_provider_id'] = ai_provider_id
        post = self.create(vals)
        if topic and post.ai_provider_id:
            post.action_generate_with_ai()
        return {'post_id': post.id}

    def action_schedule_at(self, scheduled_date):
        """Herramienta 'programar_publicacion'. scheduled_date en formato
        '%Y-%m-%d %H:%M:%S'."""
        self.ensure_one()
        self.scheduled_date = scheduled_date
        return self.action_schedule()

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
