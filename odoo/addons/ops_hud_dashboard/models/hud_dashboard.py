# -*- coding: utf-8 -*-
from datetime import timedelta
from collections import defaultdict

from odoo import api, fields, models

PLATFORM_LABELS = {
    'facebook': 'Facebook',
    'instagram': 'Instagram',
    'linkedin': 'LinkedIn',
    'twitter': 'X (Twitter)',
    'tiktok': 'TikTok',
    'generic': 'Genérico',
}

ORDER_STATE_LABELS = {
    'draft': 'Cotización',
    'sent': 'Enviada',
    'sale': 'Confirmado',
    'done': 'Bloqueado',
    'cancel': 'Cancelado',
}


class OpsHudDashboard(models.AbstractModel):
    _name = 'ops.hud.dashboard'
    _description = 'Agregaciones de datos para el HUD (sin persistencia propia)'

    # ------------------------------------------------------------------
    # Punto de entrada único: el frontend OWL llama a este método por RPC
    # estándar de Odoo (orm.call), sin necesidad de un controlador HTTP.
    # ------------------------------------------------------------------

    @api.model
    def get_hud_context(self):
        """Qué puede ver este usuario: pestañas y chat. Módulos de dominio
        (ej. ops_hud_clinical) extienden esto para sumar la suya. Una pestaña
        solo se ofrece si el usuario tiene acceso a los datos que consulta —
        antes el HUD entero fallaba con un error de acceso para quien no
        tuviera el grupo de IA."""
        def can(*models):
            return all(self.env[m].has_access('read') for m in models)

        tabs = []
        if can('social.media.post', 'ai.approval.request', 'ai.audit.log'):
            tabs.append('aria')
        if can('sale.order', 'account.move'):
            tabs.append('tienda')
        return {
            'tabs': tabs,
            'chat': self.env['ai.conversation'].has_access('create'),
        }

    @api.model
    def get_dashboard_data(self, days=30):
        return {
            'kpis': self._get_kpis(),
            'platform_breakdown': self._get_platform_breakdown(),
            'engagement_by_platform': self._get_engagement_by_platform(),
            'timeline': self._get_timeline(days),
            'ai_provider_usage': self._get_ai_provider_usage(),
            'ai_provider_success_rate': self._get_ai_provider_success_rate(),
            'account_status': self._get_account_status(),
            'top_posts': self._get_top_posts(),
            'skills': self._get_skills(),
            'attention_queue': self._get_attention_queue(),
            'activity_by_agent': self._get_activity_by_agent(days),
            'conversations_by_agent': self._get_conversations_by_agent(),
        }

    # ------------------------------------------------------------------
    # 1. KPIs globales
    # ------------------------------------------------------------------

    def _get_kpis(self):
        Post = self.env['social.media.post']
        Line = self.env['social.media.post.line']
        Approval = self.env['ai.approval.request']

        total_posts = Post.search_count([])
        published_posts = Post.search_count([('state', '=', 'done')])
        error_posts = Post.search_count([('state', '=', 'error')])

        lines = Line.search([('state', '=', 'success')])
        total_engagement = sum(lines.mapped('engagement_count'))

        total_lines = Line.search_count([])
        success_lines = len(lines)
        success_rate = round((success_lines / total_lines) * 100, 1) if total_lines else 0.0

        pending_approvals = Approval.search_count([('state', '=', 'pending')])

        return {
            'total_posts': total_posts,
            'published_posts': published_posts,
            'error_posts': error_posts,
            'total_engagement': total_engagement,
            'success_rate': success_rate,
            'pending_approvals': pending_approvals,
        }

    # ------------------------------------------------------------------
    # 2. Publicaciones por red social (dona)
    # ------------------------------------------------------------------

    def _get_platform_breakdown(self):
        Line = self.env['social.media.post.line']
        groups = Line.read_group(
            domain=[], fields=['platform'], groupby=['platform']
        )
        labels, values = [], []
        for g in groups:
            platform = g.get('platform')
            if not platform:
                continue
            labels.append(PLATFORM_LABELS.get(platform, platform))
            values.append(g.get('platform_count', 0))
        return {'labels': labels, 'values': values}

    # ------------------------------------------------------------------
    # 3. Interacciones por red social (barras apiladas)
    # ------------------------------------------------------------------

    def _get_engagement_by_platform(self):
        Line = self.env['social.media.post.line']
        lines = Line.search([('state', '=', 'success')])
        by_platform = defaultdict(lambda: {'likes': 0, 'comments': 0, 'shares': 0})
        for line in lines:
            key = line.platform or 'generic'
            by_platform[key]['likes'] += line.likes_count
            by_platform[key]['comments'] += line.comments_count
            by_platform[key]['shares'] += line.shares_count

        labels = [PLATFORM_LABELS.get(p, p) for p in by_platform.keys()]
        return {
            'labels': labels,
            'likes': [v['likes'] for v in by_platform.values()],
            'comments': [v['comments'] for v in by_platform.values()],
            'shares': [v['shares'] for v in by_platform.values()],
        }

    # ------------------------------------------------------------------
    # 4. Tendencia de publicaciones (línea, últimos N días)
    # ------------------------------------------------------------------

    def _get_timeline(self, days=30):
        Line = self.env['social.media.post.line']
        date_from = fields.Datetime.now() - timedelta(days=days)
        lines = Line.search(
            [('state', '=', 'success'), ('published_date', '>=', date_from)]
        )
        by_day = defaultdict(int)
        for line in lines:
            if line.published_date:
                day_key = line.published_date.strftime('%Y-%m-%d')
                by_day[day_key] += 1

        labels = sorted(by_day.keys())
        values = [by_day[d] for d in labels]
        return {'labels': labels, 'values': values}

    # ------------------------------------------------------------------
    # 5. Uso por proveedor de IA (dona)
    #    ai.provider.config vive en ai_agent_core desde la migración; el
    #    campo ai_provider_id de social.media.post no cambió, así que esta
    #    consulta sigue funcionando igual sin tocar nada.
    # ------------------------------------------------------------------

    def _get_ai_provider_usage(self):
        Post = self.env['social.media.post']
        groups = Post.read_group(
            domain=[('ai_provider_id', '!=', False)],
            fields=['ai_provider_id'],
            groupby=['ai_provider_id'],
        )
        labels, values = [], []
        for g in groups:
            provider = g.get('ai_provider_id')
            if not provider:
                continue
            labels.append(provider[1])
            values.append(g.get('ai_provider_id_count', 0))
        return {'labels': labels, 'values': values}

    # ------------------------------------------------------------------
    # 6. Tasa de éxito por proveedor de IA (barras horizontales)
    # ------------------------------------------------------------------

    def _get_ai_provider_success_rate(self):
        Post = self.env['social.media.post']
        providers = self.env['ai.provider.config'].search([])
        labels, values = [], []
        for provider in providers:
            posts = Post.search([('ai_provider_id', '=', provider.id)])
            total = len(posts)
            if not total:
                continue
            success = len(posts.filtered(lambda p: p.state == 'done'))
            labels.append(provider.name)
            values.append(round((success / total) * 100, 1))
        return {'labels': labels, 'values': values}

    # ------------------------------------------------------------------
    # 7. Estado de cuentas conectadas (chips)
    # ------------------------------------------------------------------

    def _get_account_status(self):
        Account = self.env['social.media.account']
        accounts = Account.search([('active', '=', True)])
        now = fields.Datetime.now()
        result = []
        for account in accounts:
            if not account.access_token and account.platform != 'generic':
                status = 'disconnected'
            elif account.token_expiry and account.token_expiry < now:
                status = 'expired'
            elif account.token_expiry and account.token_expiry < now + timedelta(days=3):
                status = 'expiring_soon'
            else:
                status = 'connected'
            result.append({
                'name': account.name,
                'platform': PLATFORM_LABELS.get(account.platform, account.platform),
                'status': status,
            })
        return result

    # ------------------------------------------------------------------
    # 8. Top 5 publicaciones por interacciones (tabla)
    # ------------------------------------------------------------------

    def _get_top_posts(self):
        Post = self.env['social.media.post']
        posts = Post.search([('state', '=', 'done')])
        posts = posts.filtered(lambda p: p.total_engagement > 0).sorted(
            key=lambda p: p.total_engagement, reverse=True
        )[:5]
        return [
            {
                'id': p.id,
                'name': p.name,
                'total_engagement': p.total_engagement,
                'total_likes': p.total_likes,
                'total_comments': p.total_comments,
                'total_shares': p.total_shares,
                'accounts': len(p.account_ids),
            }
            for p in posts
        ]

    # ------------------------------------------------------------------
    # 9. Skills activas (lista) — ahora real, desde ai.agent.tool
    # ------------------------------------------------------------------

    def _get_skills(self):
        Tool = self.env['ai.agent.tool']
        tools = Tool.search([('active', '=', True)], order='agent_id, risk_level, sequence')
        return [
            {
                'name': t.name,
                'label': t.label,
                'agent': t.agent_id.name,
                'risk': t.risk_level,
            }
            for t in tools
        ]

    # ------------------------------------------------------------------
    # 10. Vault — Cola de atención (real, desde ai.approval.request)
    # ------------------------------------------------------------------

    def _get_attention_queue(self):
        Approval = self.env['ai.approval.request']
        pending = Approval.search(
            [('state', '=', 'pending')], order='requested_at asc', limit=10
        )
        return [
            {
                'id': a.id,
                'name': a.tool_id.label or a.tool_id.name,
                'agent': a.agent_id.name,
                'risk': a.risk_level,
                'requested_by': a.requesting_user_id.name,
                'note': a.preview_text or '',
            }
            for a in pending
        ]

    # ------------------------------------------------------------------
    # 11. Actividad por agente (barras apiladas éxito/error, ai.audit.log)
    #     Esta es la vista que justifica ai_agent_core en el HUD: cruza
    #     Redes Sociales y Atención al Cliente en un solo reporte.
    # ------------------------------------------------------------------

    def _get_activity_by_agent(self, days=30):
        AuditLog = self.env['ai.audit.log']
        date_from = fields.Datetime.now() - timedelta(days=days)
        logs = AuditLog.search([('create_date', '>=', date_from)])
        by_agent = defaultdict(lambda: {'success': 0, 'error': 0})
        for log in logs:
            key = log.agent_id.name or 'Desconocido'
            if log.status == 'error':
                by_agent[key]['error'] += 1
            else:
                by_agent[key]['success'] += 1

        labels = list(by_agent.keys())
        return {
            'labels': labels,
            'success': [by_agent[a]['success'] for a in labels],
            'error': [by_agent[a]['error'] for a in labels],
        }

    # ------------------------------------------------------------------
    # 12. Conversaciones por agente y estado (tabla, ai.conversation)
    # ------------------------------------------------------------------

    def _get_conversations_by_agent(self):
        Conversation = self.env['ai.conversation']
        groups = Conversation.read_group(
            domain=[], fields=['agent_id'], groupby=['agent_id', 'state'], lazy=False,
        )
        by_agent = defaultdict(lambda: {'active': 0, 'escalated': 0, 'closed': 0})
        for g in groups:
            agent = g.get('agent_id')
            state = g.get('state')
            if not agent or not state:
                continue
            by_agent[agent[1]][state] = g.get('__count', 0)

        return [
            {'agent': agent, 'active': v['active'], 'escalated': v['escalated'], 'closed': v['closed']}
            for agent, v in by_agent.items()
        ]

    # ------------------------------------------------------------------
    # Pestaña Tienda — solo sale/account, que es lo que hay instalado y con
    # datos reales en esta base (sin purchase/stock/website_sale: ver
    # ARIA_Especificacion_Tecnica.md — el mismo principio de "nunca inventar
    # datos" aplica acá, no solo a los agentes de IA).
    # ------------------------------------------------------------------

    @api.model
    def get_store_dashboard_data(self):
        return {
            'currency_symbol': self.env.company.currency_id.symbol or '',
            'store_kpis': self._get_store_kpis(),
            'orders_by_state': self._get_orders_by_state(),
            'invoice_kpis': self._get_invoice_kpis(),
            'invoiced_trend': self._get_invoiced_trend(),
        }

    def _daily_series(self, model_name, domain, date_field, agg_field=None, days=14):
        """Serie diaria (últimos `days` días, incluye hoy) de conteo o suma
        de `agg_field`, agrupada en Python para no depender de las
        convenciones de fecha de read_group (que ya nos mordieron hoy con
        el cambio de __count) y para no dejar huecos: cada día del rango
        aparece, con 0 si no hubo actividad."""
        today = fields.Date.context_today(self)
        date_from = today - timedelta(days=days - 1)
        recs = self.env[model_name].search(domain + [(date_field, '>=', fields.Date.to_string(date_from))])
        by_day = defaultdict(float)
        for rec in recs:
            rec_date = rec[date_field]
            if not rec_date:
                continue
            if hasattr(rec_date, 'date'):
                rec_date = rec_date.date()
            by_day[rec_date.isoformat()] += (rec[agg_field] if agg_field else 1)
        labels = [(date_from + timedelta(days=i)).isoformat() for i in range(days)]
        values = [round(by_day.get(d, 0.0), 2) for d in labels]
        return labels, values

    def _pct_change(self, current, previous):
        """None (no 'N/A' ni 0 disfrazado) cuando ayer no hay base de
        comparación — un 0% real y una comparación imposible no son lo
        mismo, y el frontend decide cómo mostrar cada caso."""
        if not previous:
            return None
        return round(((current - previous) / previous) * 100, 1)

    def _get_store_kpis(self):
        domain = [('state', '!=', 'cancel')]
        _, sales_series = self._daily_series('sale.order', domain, 'date_order', 'amount_total', days=14)
        _, orders_series = self._daily_series('sale.order', domain, 'date_order', None, days=14)
        avg_series = [
            round(s / o, 2) if o else 0.0
            for s, o in zip(sales_series, orders_series)
        ]

        def kpi(series):
            return {
                'value': series[-1],
                'delta_pct': self._pct_change(series[-1], series[-2]),
                'trend': series,
            }

        return {
            'sales_today': kpi(sales_series),
            'avg_ticket': kpi(avg_series),
            'orders_today': kpi(orders_series),
        }

    def _get_orders_by_state(self):
        Order = self.env['sale.order']
        groups = Order.read_group(domain=[], fields=['state'], groupby=['state'])
        labels, values = [], []
        for g in groups:
            state = g.get('state')
            if not state:
                continue
            labels.append(ORDER_STATE_LABELS.get(state, state))
            values.append(g.get('state_count', 0))
        return {'labels': labels, 'values': values}

    def _get_invoice_kpis(self):
        Move = self.env['account.move']
        base_domain = [('move_type', 'in', ('out_invoice', 'out_refund')), ('state', '=', 'posted')]
        paid = Move.search_count(base_domain + [('payment_state', 'in', ('paid', 'in_payment'))])
        pending = Move.search_count(base_domain + [
            ('payment_state', 'not in', ('paid', 'in_payment', 'reversed')),
        ])
        today = fields.Date.context_today(self)
        overdue = Move.search_count(base_domain + [
            ('payment_state', 'not in', ('paid', 'in_payment', 'reversed')),
            ('invoice_date_due', '<', fields.Date.to_string(today)),
        ])
        return {'paid': paid, 'pending': pending, 'overdue': overdue}

    def _get_invoiced_trend(self, days=30):
        domain = [('move_type', 'in', ('out_invoice', 'out_refund')), ('state', '=', 'posted')]
        labels, values = self._daily_series('account.move', domain, 'invoice_date', 'amount_total', days=days)
        return {'labels': labels, 'values': values}
