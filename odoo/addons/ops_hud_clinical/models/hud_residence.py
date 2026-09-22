# -*- coding: utf-8 -*-
"""Datos de la pestaña RESIDENCIA del Centro de Control.

Reglas de diseño:
* Todo se calcula en el servidor y con el entorno del usuario que consulta,
  de modo que las ACL de peart_clinical_record siguen mandando. Las únicas
  lecturas con sudo son conteos agregados de tablas de configuración o de
  auditoría (sin datos de pacientes).
* Cada rol recibe solo sus bloques (ROLE_BLOCKS). Un bloque que el rol no
  tiene ni se calcula, así que no viaja por la red.
"""
from collections import defaultdict
from datetime import datetime, time, timedelta

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import AccessError

from .ops_hud_threshold import STATUS_RANK, worst

ALL_BLOCKS = {'meds', 'logs', 'incidents', 'compliance', 'occupancy',
              'family', 'family_q', 'portal', 'trace', 'aria_chat', 'handover', 'approvals'}
ROLE_BLOCKS = {
    'peart_clinical_record.group_clinical_ceo': ALL_BLOCKS,
    'peart_clinical_record.group_clinical_doctor': {
        'meds', 'logs', 'incidents', 'compliance', 'family', 'family_q',
        'aria_chat', 'handover', 'approvals'},
    'peart_clinical_record.group_clinical_nurse': {
        'meds', 'logs', 'incidents', 'family_q', 'aria_chat', 'handover'},
    'peart_clinical_record.group_clinical_admin': {'occupancy', 'portal'},
}
SEV_LABEL = {'danger': 'URGENTE', 'warn': 'ATENCIÓN', 'info': 'INFO'}
SERIOUS = ('serious', 'sentinel')
MODERATE_UP = ('moderate', 'serious', 'sentinel')
PORTAL_ACTIONS = ('summary', 'timeline', 'record', 'documents', 'download', 'aria')
QUEUE_LIMIT = 25
PER_SOURCE = 8
TREND_DAYS = 30


def _act_form(model, res_id):
    return {'type': 'ir.actions.act_window', 'res_model': model, 'res_id': res_id,
            'views': [[False, 'form']], 'target': 'current'}


def _act_list(name, model, domain):
    return {'type': 'ir.actions.act_window', 'name': name, 'res_model': model,
            'domain': domain, 'views': [[False, 'list'], [False, 'form']], 'target': 'current'}


def _kpi(value, status, hint='', action=None, display=None):
    out = {'value': value, 'status': status, 'hint': hint, 'action': action}
    if display is not None:
        out['display'] = display
    return out


def _minutes(delta):
    return int(delta.total_seconds() // 60)


def _human(minutes):
    if minutes < 90:
        return '%d min' % minutes
    if minutes < 48 * 60:
        return '%d h' % round(minutes / 60)
    return '%d días' % round(minutes / 1440)


class OpsHudDashboard(models.AbstractModel):
    _inherit = 'ops.hud.dashboard'

    # ------------------------------------------------------------------
    # Acceso
    # ------------------------------------------------------------------

    @api.model
    def _residence_blocks(self):
        blocks = set()
        for xmlid, role_blocks in ROLE_BLOCKS.items():
            if self.env.user.has_group(xmlid):
                blocks |= role_blocks
        return blocks

    @api.model
    def get_hud_context(self):
        ctx = super().get_hud_context()
        if self._residence_blocks():
            ctx['tabs'].append('residencia')
        return ctx

    # ------------------------------------------------------------------
    # Tiempo (zona horaria de la residencia)
    # ------------------------------------------------------------------

    def _res_clock(self):
        tz = pytz.timezone(self.env.company.partner_id.tz or 'America/Jamaica')
        now_utc = fields.Datetime.now()
        local = pytz.utc.localize(now_utc).astimezone(tz)

        def bounds(day):
            start = tz.localize(datetime.combine(day, time.min))
            return (start.astimezone(pytz.utc).replace(tzinfo=None),
                    (start + timedelta(days=1)).astimezone(pytz.utc).replace(tzinfo=None))

        def to_local_date(dt):
            return pytz.utc.localize(dt).astimezone(tz).date()

        return {'tz': tz, 'now': now_utc, 'local': local, 'today': local.date(),
                'bounds': bounds, 'local_date': to_local_date}

    def _res_due_shift(self, clock):
        """Último turno cuyo cierre ya venció (1 h después de terminar).
        Turnos: día 07-19, noche 19-07 (la noche pertenece al día en que empieza)."""
        t, today = clock['local'].time(), clock['today']
        if t >= time(20, 0):
            return today, 'day'
        if t >= time(8, 0):
            return today - timedelta(days=1), 'night'
        return today - timedelta(days=1), 'day'

    # ------------------------------------------------------------------
    # Punto de entrada
    # ------------------------------------------------------------------

    @api.model
    def get_residence_dashboard_data(self):
        blocks = self._residence_blocks()
        if not blocks:
            raise AccessError(_('Su usuario no tiene un rol clínico.'))
        # El HUD está en español: nombres de escalas y tipos salen traducidos
        # (si el idioma no está instalado, Odoo cae al texto original).
        if self.env['res.lang'].search_count([('code', '=', 'es_ES'), ('active', '=', True)]):
            self = self.with_context(lang='es_ES')
        clock = self._res_clock()
        Th = self.env['ops.hud.threshold']
        kpis, rows = {}, []
        ctx = {'clock': clock, 'Th': Th, 'rows': rows}

        if 'meds' in blocks:
            kpis['meds'] = self._res_meds(ctx)
        if 'logs' in blocks:
            kpis['logs'], kpis['alerts'] = self._res_logs(ctx)
        if 'incidents' in blocks:
            kpis['incidents'], kpis['falls'] = self._res_incidents(ctx)
        if 'compliance' in blocks:
            kpis['compliance'] = self._res_compliance(ctx)
        if 'occupancy' in blocks:
            kpis['occupancy'] = self._res_occupancy(ctx)
        if 'family' in blocks:
            kpis['aria'] = self._res_aria(ctx)
        if 'family_q' in blocks:
            kpis['family_pending'] = self._res_family_questions(ctx)
        if 'portal' in blocks:
            kpis['portal'] = self._res_portal(ctx)
        if 'trace' in blocks:
            kpis['access'] = self._res_trace(ctx)
        if 'handover' in blocks:
            kpis['handover'] = self._res_handover(ctx)
        if 'approvals' in blocks:
            kpis['approvals'] = self._res_approvals(ctx)

        rows.sort(key=lambda r: -STATUS_RANK[r['severity']])
        queue = rows[:QUEUE_LIMIT]
        for row in queue:
            row['severity_label'] = SEV_LABEL[row['severity']]

        data = {
            'allowed_blocks': sorted(blocks | {'attention'}),
            'generated_at': clock['local'].strftime('%H:%M'),
            'kpis': kpis,
            'attention': queue,
            'attention_total': len(rows),
        }
        if 'occupancy' in blocks:
            data['trend_occupancy'] = self._res_trend_occupancy(clock)
        if 'incidents' in blocks:
            data['trend_safety'] = self._res_trend_safety(clock)
        return data

    def _row(self, ctx, severity, area, title, detail, when, action):
        ctx['rows'].append({
            'severity': severity, 'area': area, 'title': title,
            'detail': detail, 'when': when, 'action': action})

    # ------------------------------------------------------------------
    # Seguridad clínica
    # ------------------------------------------------------------------

    def _res_meds(self, ctx):
        c, Th = ctx['clock'], ctx['Th']
        Admin = self.env['peart.medication.administration']
        late_from = c['now'] - timedelta(minutes=60)
        overdue = Admin.search(
            [('state', '=', 'pending'), ('scheduled_datetime', '<', late_from)], order='scheduled_datetime')
        max_delay = _minutes(c['now'] - overdue[0].scheduled_datetime) if overdue else 0
        start, end = c['bounds'](c['today'])
        not_given = Admin.search_count([
            ('state', 'in', ('refused', 'omitted', 'held')),
            ('scheduled_datetime', '>=', start), ('scheduled_datetime', '<', end)])

        status = worst(Th.status('meds_overdue', len(overdue)),
                       Th.status('meds_max_delay', max_delay) if overdue else 'ok')
        if status == 'ok' and not_given:
            status = 'warn'
        for dose in overdue[:PER_SOURCE]:
            delay = _minutes(c['now'] - dose.scheduled_datetime)
            local = pytz.utc.localize(dose.scheduled_datetime).astimezone(c['tz'])
            self._row(ctx, 'danger' if Th.status('meds_max_delay', delay) == 'danger' else 'warn',
                      'Medicación', '%s · %s %s' % (dose.resident_id.name, dose.drug, dose.dose or ''),
                      'Dosis de las %s sin registrar' % local.strftime('%H:%M'),
                      'hace %s' % _human(delay), _act_form('peart.medication.administration', dose.id))
        hint = '%d atrasadas' % len(overdue)
        if overdue:
            hint += ' (la mayor, %s)' % _human(max_delay)
        hint += ' · %d rechazadas/omitidas/retenidas hoy' % not_given
        return _kpi(len(overdue) + not_given, status, hint, _act_list(
            'Dosis atrasadas', 'peart.medication.administration',
            [('state', '=', 'pending'), ('scheduled_datetime', '<', fields.Datetime.to_string(late_from))]))

    def _res_logs(self, ctx):
        c, Th = ctx['clock'], ctx['Th']
        Resident, Log = self.env['peart.resident'], self.env['peart.daily.log']
        date, shift = self._res_due_shift(c)
        shift_label = 'día' if shift == 'day' else 'noche'
        expected = Resident.search([
            ('state', '=', 'active'), '|', ('admission_date', '=', False), ('admission_date', '<=', date)])
        logs = Log.search([('date', '=', date), ('shift', '=', shift)])
        closed = logs.filtered(lambda l: l.state == 'closed')
        drafts = logs - closed
        missing = expected - logs.resident_id
        pct = round(len(closed) / len(expected) * 100) if expected else None
        status = Th.status('logs_closed_pct', pct) if expected else 'none'
        when = 'turno %s del %s' % (shift_label, date.strftime('%d/%m'))
        for log in drafts[:PER_SOURCE]:
            self._row(ctx, 'warn', 'Registro de turno', log.resident_id.name,
                      'Registro sin cerrar', when, _act_form('peart.daily.log', log.id))
        if missing:
            self._row(ctx, 'danger' if status == 'danger' else 'warn', 'Registro de turno',
                      '%d residente(s) sin registro' % len(missing),
                      ', '.join(missing[:4].mapped('name')) + ('…' if len(missing) > 4 else ''), when,
                      _act_list('Sin registro de turno', 'peart.resident', [('id', 'in', missing.ids)]))
        logs_kpi = _kpi(
            pct, status,
            '%d/%d cerrados · %d en borrador · %d sin registro (%s)' % (
                len(closed), len(expected), len(drafts), len(missing), when) if expected
            else 'No hay residentes en residencia',
            _act_list('Registros del turno', 'peart.daily.log',
                      [('date', '=', fields.Date.to_string(date)), ('shift', '=', shift)]),
            display=('%d%%' % pct) if pct is not None else '—')

        since = c['today'] - timedelta(days=1)
        flagged = Log.search([('has_alert', '=', True), ('date', '>=', since)], order='date desc')
        for log in flagged[:PER_SOURCE]:
            self._row(ctx, 'warn', 'Signos vitales', '%s · %s' % (log.resident_id.name, log.alert_flags),
                      'Valores fuera de rango', 'turno %s del %s' % (
                          'día' if log.shift == 'day' else 'noche', log.date.strftime('%d/%m')),
                      _act_form('peart.daily.log', log.id))
        alerts_kpi = _kpi(len(flagged), Th.status('logs_alerts', len(flagged)),
                          'Registros de las últimas 24 h con signos fuera de rango',
                          _act_list('Valores fuera de rango', 'peart.daily.log',
                                    [('has_alert', '=', True), ('date', '>=', fields.Date.to_string(since))]))
        return logs_kpi, alerts_kpi

    def _res_incidents(self, ctx):
        c = ctx['clock']
        Incident = self.env['peart.incident']
        open_ = Incident.search([('state', '!=', 'closed')], order='occurred_at desc')
        serious = open_.filtered(lambda i: i.severity in SERIOUS)
        no_notice = open_.filtered(
            lambda i: i.severity in MODERATE_UP and not (i.physician_notified and i.family_notified))
        status = 'danger' if (serious or no_notice) else 'warn' if open_ else 'ok'
        for inc in open_[:PER_SOURCE]:
            missing = []
            if inc.severity in MODERATE_UP:
                if not inc.physician_notified:
                    missing.append('falta avisar al médico')
                if not inc.family_notified:
                    missing.append('falta avisar a la familia')
            sev = 'danger' if (inc.severity in SERIOUS or missing) else 'warn'
            self._row(ctx, sev, 'Incidente', '%s · %s' % (inc.name, inc.resident_id.name),
                      '; '.join([dict(inc._fields['kind']._description_selection(inc.env))[inc.kind]] + missing),
                      'hace %s' % _human(_minutes(c['now'] - inc.occurred_at)),
                      _act_form('peart.incident', inc.id))
        incidents_kpi = _kpi(
            len(open_), status,
            '%d graves/centinela · %d con aviso pendiente' % (len(serious), len(no_notice)),
            _act_list('Incidentes abiertos', 'peart.incident', [('state', '!=', 'closed')]))

        d30 = fields.Datetime.subtract(c['now'], days=30)
        d60 = fields.Datetime.subtract(c['now'], days=60)
        falls = Incident.search_count([('kind', '=', 'fall'), ('occurred_at', '>=', d30)])
        prev = Incident.search_count([('kind', '=', 'fall'), ('occurred_at', '>=', d60), ('occurred_at', '<', d30)])
        falls_kpi = _kpi(falls, 'info', 'Los 30 días anteriores: %d' % prev, _act_list(
            'Caídas (30 días)', 'peart.incident',
            [('kind', '=', 'fall'), ('occurred_at', '>=', fields.Datetime.to_string(d30))]))
        return incidents_kpi, falls_kpi

    # ------------------------------------------------------------------
    # Cumplimiento
    # ------------------------------------------------------------------

    def _res_compliance(self, ctx):
        c, Th = ctx['clock'], ctx['Th']
        today = c['today']
        residents = self.env['peart.resident'].search([('state', '=', 'active')])
        items = []   # (days_overdue, title, detail, action)

        scales = self.env['peart.scale'].search([('active', '=', True), ('frequency_days', '>', 0)])
        last = {}
        for a in self.env['peart.resident.assessment'].search(
                [('state', '=', 'done'), ('resident_id', 'in', residents.ids)], order='date desc'):
            last.setdefault((a.resident_id.id, a.scale_id.id), a.date.date())
        by_resident = defaultdict(list)     # residente -> [(días de retraso, escala)]
        for r in residents:
            for s in scales:
                seen = last.get((r.id, s.id))
                if seen:
                    days = (today - (seen + timedelta(days=s.frequency_days))).days
                    if days <= 0:
                        continue
                else:
                    days = (today - (r.admission_date or today)).days - 7    # 7 días de gracia tras el ingreso
                    if days < 0:
                        continue
                by_resident[r].append((days, s))
        n_assess = sum(len(v) for v in by_resident.values())
        for r, due in by_resident.items():
            due.sort(key=lambda d: -d[0])
            items.append((due[0][0], '%s · %d valoración(es) vencida(s)' % (r.name, len(due)),
                          ', '.join(s.code.upper() for _d, s in due),
                          _act_form('peart.resident', r.id), 'Valoración vencida'))
        # cada valoración cuenta en el indicador, aunque la cola las agrupe por residente
        extra_assess = n_assess - len(by_resident)

        plans = self.env['peart.resident.care.plan'].search(
            [('state', '=', 'active'), ('review_date', '<', today)])
        for p in plans:
            items.append(((today - p.review_date).days, '%s · %s' % (p.resident_id.name, p.name),
                          'Revisión del plan debía hacerse el %s' % p.review_date.strftime('%d/%m/%Y'),
                          _act_form('peart.resident', p.resident_id.id), 'Plan de cuidados'))
        no_intake = residents.filtered(lambda r: not r.intake_ids)
        for r in no_intake:
            items.append(((today - (r.admission_date or today)).days, r.name,
                          'Sin ingreso clínico', _act_form('peart.resident', r.id), 'Ingreso clínico'))
        n_consent = 0
        for r in residents:
            missing = [label for kind, label in (('data_processing', 'datos de salud'), ('treatment', 'tratamiento'))
                       if not r.has_consent(kind)]
            if missing:
                n_consent += 1
                items.append(((today - (r.admission_date or today)).days, r.name,
                              'Falta consentimiento: ' + ', '.join(missing),
                              _act_form('peart.resident', r.id), 'Consentimiento'))

        max_days = max((i[0] for i in items), default=0)
        total = len(items) + extra_assess
        status = worst(Th.status('compliance_overdue', total),
                       Th.status('compliance_days', max_days) if items else 'ok')
        items.sort(key=lambda i: -i[0])
        for days, title, detail, action, area in items[:PER_SOURCE]:
            self._row(ctx, 'danger' if Th.status('compliance_days', days) == 'danger' else 'warn',
                      area, title, detail, 'hace %s' % _human(days * 1440) if days > 0 else 'ahora', action)
        return _kpi(
            total, status,
            'Valoraciones: %d · Planes de cuidados: %d · Sin ingreso clínico: %d · Consentimientos: %d' % (
                n_assess, len(plans), len(no_intake), n_consent),
            _act_list('Residentes en residencia', 'peart.resident', [('state', '=', 'active')]))

    # ------------------------------------------------------------------
    # Ocupación
    # ------------------------------------------------------------------

    def _res_occupancy(self, ctx):
        Resident = self.env['peart.resident']
        active = Resident.search_count([('state', '=', 'active')])
        hosp = Resident.search_count([('state', '=', 'hospitalized')])
        occupied = active + hosp
        capacity = int(self.env['ir.config_parameter'].sudo().get_param('ops_hud_clinical.bed_capacity') or 0)
        pipeline = self.env['peart.admission'].search_count([('state', 'in', ('new', 'assessed', 'quoted'))])
        display = '%d/%d (%d%%)' % (occupied, capacity, round(occupied / capacity * 100)) if capacity else str(occupied)
        hint = '%d en residencia · %d hospitalizados · %d admisiones en curso' % (active, hosp, pipeline)
        if not capacity:
            hint += ' · defina la capacidad en Ajustes para ver el %'
        return _kpi(occupied, 'info', hint, _act_list(
            'Residentes', 'peart.resident', [('state', 'in', ('active', 'hospitalized'))]), display=display)

    # ------------------------------------------------------------------
    # Familias, portal y ARIA
    # ------------------------------------------------------------------

    def _res_family_activities(self):
        act_type = self.env.ref('peart_clinical_record.mail_activity_type_family_question', raise_if_not_found=False)
        if not act_type:
            return self.env['mail.activity']
        # Conteo operativo de todo el equipo: sudo (no expone datos del paciente).
        return self.env['mail.activity'].sudo().search(
            [('activity_type_id', '=', act_type.id), ('res_model', '=', 'peart.resident')], order='create_date')

    def _res_family_questions(self, ctx):
        c, Th = ctx['clock'], ctx['Th']
        acts = self._res_family_activities()
        # Una pregunta se envía a todas las enfermeras: se cuenta una vez por residente y fecha.
        seen, unique = set(), []
        for a in acts:
            key = (a.res_id, a.create_date.replace(second=0, microsecond=0))
            if key not in seen:
                seen.add(key)
                unique.append(a)
        oldest = _minutes(c['now'] - unique[0].create_date) / 60 if unique else 0
        status = Th.status('family_question_hours', oldest) if unique else 'ok'
        residents = {r.id: r for r in self.env['peart.resident'].browse([a.res_id for a in unique]).exists()}
        for a in unique[:PER_SOURCE]:
            r = residents.get(a.res_id)
            if not r:
                continue
            age = _minutes(c['now'] - a.create_date)
            self._row(ctx, 'danger' if Th.status('family_question_hours', age / 60) == 'danger' else 'warn',
                      'Pregunta de familia', r.name, 'ARIA pasó una pregunta a enfermería',
                      'hace %s' % _human(age), _act_form('peart.resident', r.id))
        return _kpi(len(unique), status,
                    'La más antigua: %s' % _human(int(oldest * 60)) if unique else 'Ninguna pendiente',
                    None)

    def _res_aria(self, ctx):
        c = ctx['clock']
        Log = self.env['peart.family.access.log'].sudo()
        since = fields.Datetime.subtract(c['now'], days=30)
        base = [('action', '=', 'aria'), ('create_date', '>=', since)]
        questions = Log.search_count(base)
        errors = Log.search_count(base + [('error', '=', True)])
        escalated = Log.search_count(base + [('escalated', '=', True)])
        provider = self.env['peart.resident']._aria_provider()
        consents = self.env['peart.resident.consent'].sudo().search_count(
            [('kind', '=', 'ai_assistant'), ('state', '=', 'granted')])
        if consents and not provider:
            status, extra = 'danger', ' · ARIA de familias APAGADA: elija un proveedor en Ajustes'
            self._row(ctx, 'danger', 'ARIA', 'ARIA para familias está apagada',
                      'Hay %d consentimiento(s) de ARIA pero no hay proveedor de IA elegido' % consents,
                      'ahora', None)
        elif errors:
            status, extra = 'warn', ''
        else:
            status, extra = ('ok' if consents else 'info'), ''
        return _kpi(questions, status, '%d escaladas a enfermería · %d con error (30 días)%s' % (
            escalated, errors, extra), None)

    def _res_portal(self, ctx):
        c = ctx['clock']
        Link = self.env['peart.resident.family.link']
        enabled = Link.search_count([('access_enabled', '=', True)])
        pending = Link.search([('access_enabled', '=', False)], order='id desc')
        since = fields.Datetime.subtract(c['now'], days=30)
        active = self.env['peart.family.access.log'].sudo().read_group(
            [('action', 'in', PORTAL_ACTIONS), ('create_date', '>=', since)], ['user_id'], ['user_id'])
        for link in pending[:PER_SOURCE]:
            ready = link.resident_id.has_consent('family_access')
            self._row(ctx, 'warn', 'Portal familiar', '%s → %s' % (link.user_id.name, link.resident_id.name),
                      'Consentimiento registrado: falta habilitar el acceso' if ready
                      else 'Falta registrar el consentimiento de acceso familiar',
                      'pendiente', _act_form('peart.resident', link.resident_id.id))
        return _kpi(enabled, 'warn' if pending else ('ok' if enabled else 'info'),
                    '%d vínculos sin habilitar · %d familias activas (30 días)' % (len(pending), len(active)),
                    _act_list('Vínculos familiares', 'peart.resident.family.link', []))

    def _res_handover(self, ctx):
        Handover = self.env['peart.shift.handover']
        clock = ctx['clock']
        date, shift = Handover._due_shift(Handover._clock())
        record = Handover.search([('date', '=', date), ('shift', '=', shift)], limit=1)
        if not record:
            return _kpi(0, 'warn', _('Not generated yet for this shift (runs at 06:45/18:45).'), None)
        total = (record.overdue_doses_count + record.unclosed_logs_count
                + record.open_incidents_count + record.vital_alerts_count)
        status = 'danger' if record.open_incidents_count or record.overdue_doses_count else (
            'warn' if total else 'ok')
        return _kpi(total, status, '%s · dosis: %d · registros: %d · incidentes: %d · alertas: %d · familia: %d' % (
            record.name, record.overdue_doses_count, record.unclosed_logs_count,
            record.open_incidents_count, record.vital_alerts_count, record.family_questions_count),
            _act_form('peart.shift.handover', record.id))

    def _res_approvals(self, ctx):
        c = ctx['clock']
        Request = self.env['peart.clinical.action.request']
        pending = Request.search([('state', '=', 'pending')], order='create_date')
        for req in pending[:PER_SOURCE]:
            self._row(ctx, 'warn', 'Aprobación pendiente', req.name, req.preview,
                      'hace %s' % _human(_minutes(c['now'] - req.create_date)),
                      _act_form('peart.clinical.action.request', req.id))
        return _kpi(len(pending), 'warn' if pending else 'ok',
                    'Solicitudes de ARIA Clínica esperando aprobación del médico.' if pending
                    else 'Sin solicitudes pendientes.',
                    _act_list('Pending Actions', 'peart.clinical.action.request', [('state', '=', 'pending')]))

    def _res_trace(self, ctx):
        c = ctx['clock']
        Log = self.env['peart.family.access.log'].sudo()
        since = fields.Datetime.subtract(c['now'], days=7)
        views = Log.search_count([('action', '=', 'staff_view'), ('create_date', '>=', since)])
        reports = Log.search_count([('action', '=', 'report'), ('create_date', '>=', since)])
        return _kpi(views + reports, 'info', '%d aperturas de expediente · %d informes impresos (7 días)' % (
            views, reports), _act_list('Registro de accesos', 'peart.family.access.log', []))

    # ------------------------------------------------------------------
    # Tendencias (calculadas sobre los propios datos; no requieren snapshots)
    # ------------------------------------------------------------------

    def _res_days(self, clock):
        today = clock['today']
        return [today - timedelta(days=i) for i in range(TREND_DAYS - 1, -1, -1)]

    def _res_trend_occupancy(self, clock):
        days = self._res_days(clock)
        residents = self.env['peart.resident'].with_context(active_test=False).search([])
        values = []
        for d in days:
            values.append(sum(
                1 for r in residents
                if (r.admission_date or d) <= d and not (r.discharge_date and r.discharge_date <= d)))
        return {'labels': [d.strftime('%d/%m') for d in days], 'values': values}

    def _res_trend_safety(self, clock):
        days = self._res_days(clock)
        first = days[0]
        start = clock['bounds'](first)[0]
        by = {'incidents': defaultdict(int), 'alerts': defaultdict(int), 'not_given': defaultdict(int)}
        for inc in self.env['peart.incident'].search([('occurred_at', '>=', start)]):
            by['incidents'][clock['local_date'](inc.occurred_at)] += 1
        for log in self.env['peart.daily.log'].search([('has_alert', '=', True), ('date', '>=', first)]):
            by['alerts'][log.date] += 1
        for dose in self.env['peart.medication.administration'].search([
                ('state', 'in', ('refused', 'omitted', 'held')), ('scheduled_datetime', '>=', start)]):
            by['not_given'][clock['local_date'](dose.scheduled_datetime)] += 1
        return {'labels': [d.strftime('%d/%m') for d in days],
                'incidents': [by['incidents'][d] for d in days],
                'alerts': [by['alerts'][d] for d in days],
                'not_given': [by['not_given'][d] for d in days]}
