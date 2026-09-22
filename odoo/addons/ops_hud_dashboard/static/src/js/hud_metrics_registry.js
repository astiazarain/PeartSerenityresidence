/** @odoo-module **/

/**
 * Catálogo declarativo de todas las métricas del HUD, por pestaña. Único
 * lugar que hay que tocar para agregar/quitar una métrica — el componente
 * (hud_dashboard.js) y el panel de Métricas se dirigen enteramente por esta
 * lista, no hay bloques hardcodeados por métrica en la plantilla.
 *
 * Campos:
 *   id            identificador estable (se usa como key de metricsConfig
 *                 y se persiste en localStorage — no renombrar sin migrar)
 *   tab           id de una pestaña de TABS ('aria', 'tienda', ...)
 *   block         (opcional) bloque de acceso; solo se muestra si el servidor
 *                 lo incluye en data.allowed_blocks
 *   rich          (solo kind:'kpi') el dato es {value, display, status, hint,
 *                 action}: semáforo, texto de apoyo y clic que abre `action`
 *   columns       (solo kind:'table') [{key,label}] — tabla genérica; las
 *                 filas pueden traer `action` (clic) y `severity`
 *   category      agrupación en el panel de Métricas
 *   kind          'kpi' | 'chart' | 'table'
 *   label         título visible
 *   source        subtítulo técnico en el panel de Métricas (modelo · agregación)
 *   dataPath      ruta punteada dentro de la respuesta de get_dashboard_data()
 *                 o get_store_dashboard_data(), según la pestaña
 *   chartTypes    (solo kind:'chart') tipos disponibles; si tiene más de
 *                 uno, el badge en el panel de Métricas es clickeable
 *   defaultChartType
 *   series        (solo kind:'chart') claves de arrays de datos dentro del
 *                 objeto en dataPath, además de 'labels' — una key = single
 *                 series, varias = multi-serie (apilada en bar/area)
 *   seriesLabels  etiquetas de leyenda para cada entrada de `series`
 *   format        (solo kind:'kpi') 'number' | 'currency' | 'percent'
 *   sparkline     (solo kind:'kpi') si trae trend[] para mini-gráfico + Δ%
 *   wide          ocupa 2 columnas en la grilla
 *   defaultVisible
 */

/**
 * Pestañas del HUD. Otros módulos (ej. ops_hud_clinical) agregan la suya
 * con TABS.push({...}) y sus métricas con METRICS.push(...).
 *   id      identificador estable
 *   label   texto del botón
 *   model   modelo Odoo que sirve los datos (default 'ops.hud.dashboard')
 *   method  método que devuelve el JSON de la pestaña
 *   kwargs  argumentos opcionales
 * La pestaña solo aparece si get_hud_context() (Python) la incluye para
 * el usuario, así cada rol ve únicamente lo que puede consultar.
 */
export const TABS = [
    { id: 'aria', label: 'ARIA', method: 'get_dashboard_data', kwargs: { days: 30 } },
    { id: 'tienda', label: 'TIENDA', method: 'get_store_dashboard_data' },
];

export const METRICS = [
    // ------------------------------------------------------------------
    // ARIA — Publicaciones
    // ------------------------------------------------------------------
    { id: 'kpi_total_posts', tab: 'aria', category: 'Publicaciones', kind: 'kpi',
      label: 'Publicaciones totales', source: 'social.media.post · conteo',
      dataPath: 'kpis.total_posts', format: 'number', defaultVisible: true },
    { id: 'kpi_published_posts', tab: 'aria', category: 'Publicaciones', kind: 'kpi',
      label: 'Publicadas', source: 'social.media.post · conteo (done)',
      dataPath: 'kpis.published_posts', format: 'number', defaultVisible: true },
    { id: 'kpi_error_posts', tab: 'aria', category: 'Publicaciones', kind: 'kpi',
      label: 'Con error', source: 'social.media.post · conteo (error)',
      dataPath: 'kpis.error_posts', format: 'number', defaultVisible: true },
    { id: 'kpi_success_rate', tab: 'aria', category: 'Publicaciones', kind: 'kpi',
      label: 'Tasa de éxito', source: 'social.media.post.line · % éxito',
      dataPath: 'kpis.success_rate', format: 'percent', defaultVisible: true },
    { id: 'kpi_total_engagement', tab: 'aria', category: 'Publicaciones', kind: 'kpi',
      label: 'Interacciones totales', source: 'social.media.post.line · suma',
      dataPath: 'kpis.total_engagement', format: 'number', defaultVisible: true },
    { id: 'platform_breakdown', tab: 'aria', category: 'Publicaciones', kind: 'chart',
      label: 'Publicaciones por red social', source: 'social.media.post.line · conteo por plataforma',
      dataPath: 'platform_breakdown', series: ['values'], seriesLabels: ['Publicaciones'],
      chartTypes: ['doughnut', 'bar'], defaultChartType: 'doughnut', defaultVisible: true },
    { id: 'engagement_by_platform', tab: 'aria', category: 'Publicaciones', kind: 'chart',
      label: 'Interacciones por red social', source: 'social.media.post.line · me gusta/comentarios/compartidos',
      dataPath: 'engagement_by_platform', series: ['likes', 'comments', 'shares'],
      seriesLabels: ['Me gusta', 'Comentarios', 'Compartidos'],
      chartTypes: ['bar', 'area'], defaultChartType: 'bar', wide: true, defaultVisible: true },
    { id: 'timeline', tab: 'aria', category: 'Publicaciones', kind: 'chart',
      label: 'Tendencia de publicaciones (30 días)', source: 'social.media.post.line · conteo diario',
      dataPath: 'timeline', series: ['values'], seriesLabels: ['Publicaciones exitosas'],
      chartTypes: ['area', 'bar', 'step'], defaultChartType: 'area', wide: true, defaultVisible: true },
    { id: 'top_posts', tab: 'aria', category: 'Publicaciones', kind: 'table',
      label: 'Top publicaciones por interacciones', source: 'social.media.post · top 5',
      dataPath: 'top_posts', wide: true, defaultVisible: true },

    // ------------------------------------------------------------------
    // ARIA — IA
    // ------------------------------------------------------------------
    { id: 'kpi_pending_approvals', tab: 'aria', category: 'IA', kind: 'kpi',
      label: 'Aprobaciones pendientes', source: 'ai.approval.request · conteo (pending)',
      dataPath: 'kpis.pending_approvals', format: 'number', defaultVisible: true },
    { id: 'ai_provider_usage', tab: 'aria', category: 'IA', kind: 'chart',
      label: 'Uso por proveedor de IA', source: 'social.media.post · conteo por proveedor',
      dataPath: 'ai_provider_usage', series: ['values'], seriesLabels: ['Publicaciones'],
      chartTypes: ['doughnut', 'bar'], defaultChartType: 'doughnut', defaultVisible: true },
    { id: 'ai_provider_success_rate', tab: 'aria', category: 'IA', kind: 'chart',
      label: 'Tasa de éxito por proveedor de IA', source: 'social.media.post · % éxito por proveedor',
      dataPath: 'ai_provider_success_rate', series: ['values'], seriesLabels: ['% de éxito'],
      chartTypes: ['barh', 'doughnut'], defaultChartType: 'barh', defaultVisible: true },
    { id: 'activity_by_agent', tab: 'aria', category: 'IA', kind: 'chart',
      label: 'Actividad por agente (30 días)', source: 'ai.audit.log · éxito/error',
      dataPath: 'activity_by_agent', series: ['success', 'error'], seriesLabels: ['Éxito', 'Error'],
      chartTypes: ['bar', 'area'], defaultChartType: 'bar', wide: true, defaultVisible: true },

    // ------------------------------------------------------------------
    // ARIA — Agentes
    // ------------------------------------------------------------------
    { id: 'account_status', tab: 'aria', category: 'Agentes', kind: 'table',
      label: 'Estado de cuentas conectadas', source: 'social.media.account · estado OAuth',
      dataPath: 'account_status', defaultVisible: true },
    { id: 'skills', tab: 'aria', category: 'Agentes', kind: 'table',
      label: 'Skills activas', source: 'ai.agent.tool · catálogo',
      dataPath: 'skills', defaultVisible: true },
    { id: 'conversations_by_agent', tab: 'aria', category: 'Agentes', kind: 'table',
      label: 'Conversaciones por agente', source: 'ai.conversation · por estado',
      dataPath: 'conversations_by_agent', defaultVisible: true },
    { id: 'attention_queue', tab: 'aria', category: 'Agentes', kind: 'table',
      label: 'Vault — Cola de atención', source: 'ai.approval.request · pendientes',
      dataPath: 'attention_queue', wide: true, defaultVisible: true },

    // ------------------------------------------------------------------
    // Tienda — Ventas (sale.order)
    // ------------------------------------------------------------------
    { id: 'store_sales_today', tab: 'tienda', category: 'Ventas', kind: 'kpi',
      label: 'Ventas hoy', source: 'sale.order · monto (hoy vs. ayer)',
      dataPath: 'store_kpis.sales_today', format: 'currency', sparkline: true, defaultVisible: true },
    { id: 'store_avg_ticket', tab: 'tienda', category: 'Ventas', kind: 'kpi',
      label: 'Ticket promedio', source: 'sale.order · monto/pedidos (hoy vs. ayer)',
      dataPath: 'store_kpis.avg_ticket', format: 'currency', sparkline: true, defaultVisible: true },
    { id: 'store_orders_today', tab: 'tienda', category: 'Ventas', kind: 'kpi',
      label: 'Pedidos', source: 'sale.order · conteo (hoy vs. ayer)',
      dataPath: 'store_kpis.orders_today', format: 'number', sparkline: true, defaultVisible: true },
    { id: 'orders_by_state', tab: 'tienda', category: 'Ventas', kind: 'chart',
      label: 'Pedidos por estado', source: 'sale.order · conteo por estado',
      dataPath: 'orders_by_state', series: ['values'], seriesLabels: ['Pedidos'],
      chartTypes: ['doughnut', 'bar'], defaultChartType: 'doughnut', defaultVisible: true },

    // ------------------------------------------------------------------
    // Tienda — Finanzas (account.move)
    // ------------------------------------------------------------------
    { id: 'store_invoices_paid', tab: 'tienda', category: 'Finanzas', kind: 'kpi',
      label: 'Facturas pagadas', source: 'account.move · conteo (paid)',
      dataPath: 'invoice_kpis.paid', format: 'number', defaultVisible: true },
    { id: 'store_invoices_pending', tab: 'tienda', category: 'Finanzas', kind: 'kpi',
      label: 'Facturas pendientes', source: 'account.move · conteo (not_paid)',
      dataPath: 'invoice_kpis.pending', format: 'number', defaultVisible: true },
    { id: 'store_invoices_overdue', tab: 'tienda', category: 'Finanzas', kind: 'kpi',
      label: 'Facturas vencidas', source: 'account.move · vencimiento < hoy',
      dataPath: 'invoice_kpis.overdue', format: 'number', defaultVisible: true },
    { id: 'invoiced_trend', tab: 'tienda', category: 'Finanzas', kind: 'chart',
      label: 'Monto facturado — tendencia (30 días)', source: 'account.move · suma diaria',
      dataPath: 'invoiced_trend', series: ['values'], seriesLabels: ['Facturado'],
      chartTypes: ['area', 'bar', 'step'], defaultChartType: 'area', wide: true, defaultVisible: true },
];

export function getMetricsForTab(tab) {
    return METRICS.filter((m) => m.tab === tab);
}

export function getByPath(obj, path) {
    return path.split('.').reduce((acc, key) => (acc == null ? acc : acc[key]), obj);
}
