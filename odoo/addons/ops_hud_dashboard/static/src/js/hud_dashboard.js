/** @odoo-module **/

import { Component, useState, useRef, onWillStart, onMounted, useEffect } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { METRICS, TABS, getMetricsForTab, getByPath } from "@ops_hud_dashboard/js/hud_metrics_registry";

const METRICS_STORAGE_KEY = "ops_hud_metrics_v1";

const PALETTE = {
    gold: "#d4af37",
    goldLight: "#f0cf6b",
    amber: "#e8a33d",
    red: "#e05c5c",
    green: "#4caf7d",
    blue: "#5c9de0",
    grid: "rgba(212, 175, 55, 0.15)",
    text: "#e8dfc8",
};

const CHART_TYPE_LABELS = {
    doughnut: "DONA",
    bar: "BARRAS",
    barh: "BARRAS",
    area: "ÁREA",
    step: "ESCALÓN",
};

const STATUS_LABELS = {
    connected: "Conectada",
    expiring_soon: "Expira pronto",
    expired: "Expirada",
    disconnected: "Desconectada",
};

const RISK_LABELS = {
    0: "Consulta",
    1: "Preparación",
    2: "Sensible",
    3: "Crítica",
};

export class OpsHudDashboard extends Component {
    static template = "ops_hud_dashboard.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            tabs: [],
            tabData: {},
            tabLoading: {},
            canChat: false,
            ready: false,
            assistants: {},
            clock: this._now(),
            activeTab: null,
            drawerOpen: false,
            metricsConfig: this._loadMetricsConfig(),
            chat: { messages: [], input: "", sending: false, conversationId: false },
        });
        this.statusLabels = STATUS_LABELS;
        this.riskLabels = RISK_LABELS;

        this.rootRef = useRef("dashboardRoot");
        this.chatMessagesRef = useRef("chatMessages");
        this.charts = {};

        onWillStart(async () => {
            // Qué pestañas puede ver este usuario lo decide el servidor.
            const ctx = await this.orm.call("ops.hud.dashboard", "get_hud_context", []);
            this.state.tabs = TABS.filter((t) => ctx.tabs.includes(t.id));
            this.state.canChat = !!ctx.chat;
            if (this.state.tabs.length) {
                this.state.activeTab = this.state.tabs[0].id;
                await this._loadTab(this.state.activeTab);
            }
            this.state.ready = true;
        });

        onMounted(() => {
            this._clockInterval = setInterval(() => {
                this.state.clock = this._now();
            }, 1000);
        });

        // Se re-renderizan los gráficos cuando cambia la pestaña activa, los
        // datos, o la config de métricas (visibilidad/tipo) — no en cada
        // patch del DOM (evita reconstruir charts en cada tick del reloj o
        // mensaje de chat). JSON.stringify de metricsConfig es un detector
        // de cambios simple para un objeto chico (~25 entradas).
        useEffect(
            () => {
                this._renderCharts();
            },
            () => [
                this.state.activeTab,
                this.state.tabData[this.state.activeTab],
                JSON.stringify(this.state.metricsConfig),
            ]
        );
    }

    _now() {
        return new Date().toLocaleTimeString("es-ES", { hour12: false });
    }

    // ------------------------------------------------------------------
    // Carga de datos
    // ------------------------------------------------------------------

    async _loadTab(tabId) {
        const tab = TABS.find((t) => t.id === tabId);
        if (!tab) {
            return;
        }
        this.state.tabLoading[tabId] = true;
        try {
            this.state.tabData[tabId] = await this.orm.call(
                tab.model || "ops.hud.dashboard", tab.method, [], tab.kwargs || {}
            );
        } finally {
            this.state.tabLoading[tabId] = false;
        }
        for (const m of getMetricsForTab(tabId).filter((x) => x.kind === "assistant")) {
            if (!this.state.assistants[m.id]) {
                this.state.assistants[m.id] = { messages: [], input: "", sending: false };
            }
        }
    }

    async refresh() {
        if (this.state.activeTab) {
            await this._loadTab(this.state.activeTab);
        }
    }

    async switchTab(tab) {
        if (this.state.activeTab === tab) {
            return;
        }
        this.state.activeTab = tab;
        if (!this.state.tabData[tab]) {
            await this._loadTab(tab);
        }
    }

    // Un bloque es visible solo si el servidor lo incluyó para este usuario.
    _blockAllowed(metric) {
        if (!metric.block) {
            return true;
        }
        const data = this.state.tabData[metric.tab];
        return !data || !data.allowed_blocks || data.allowed_blocks.includes(metric.block);
    }

    openAction(action) {
        if (action) {
            this.action.doAction(action);
        }
    }

    // ------------------------------------------------------------------
    // Panel de Métricas: visibilidad + tipo de gráfico por métrica,
    // persistido en localStorage (preferencia de este navegador, no dato
    // de negocio — no amerita un modelo Odoo).
    // ------------------------------------------------------------------

    _loadMetricsConfig() {
        const config = {};
        for (const m of METRICS) {
            config[m.id] = {
                visible: m.defaultVisible !== false,
                chartType: m.defaultChartType,
            };
        }
        try {
            const stored = JSON.parse(localStorage.getItem(METRICS_STORAGE_KEY) || "{}");
            for (const id of Object.keys(stored)) {
                if (config[id]) {
                    Object.assign(config[id], stored[id]);
                }
            }
        } catch {
            // localStorage corrupto, deshabilitado (modo privado), etc. —
            // seguimos con los defaults del registry, no rompemos el HUD.
        }
        return config;
    }

    _persistMetricsConfig() {
        try {
            localStorage.setItem(METRICS_STORAGE_KEY, JSON.stringify(this.state.metricsConfig));
        } catch {
            // idem — persistencia es best-effort.
        }
    }

    toggleDrawer() {
        this.state.drawerOpen = !this.state.drawerOpen;
    }

    toggleMetric(id) {
        const cfg = this.state.metricsConfig[id];
        if (!cfg) {
            return;
        }
        cfg.visible = !cfg.visible;
        this._persistMetricsConfig();
    }

    cycleChartType(id) {
        const metric = METRICS.find((m) => m.id === id);
        const cfg = this.state.metricsConfig[id];
        if (!metric || !cfg || !metric.chartTypes || metric.chartTypes.length < 2) {
            return;
        }
        const idx = metric.chartTypes.indexOf(cfg.chartType);
        cfg.chartType = metric.chartTypes[(idx + 1) % metric.chartTypes.length];
        this._persistMetricsConfig();
    }

    toggleAllActiveTab(visible) {
        for (const m of getMetricsForTab(this.state.activeTab)) {
            this.state.metricsConfig[m.id].visible = visible;
        }
        this._persistMetricsConfig();
    }

    activeCount() {
        const all = getMetricsForTab(this.state.activeTab).filter((m) => this._blockAllowed(m));
        const active = all.filter((m) => this.state.metricsConfig[m.id] && this.state.metricsConfig[m.id].visible).length;
        return { active, total: all.length };
    }

    metricGroups() {
        const order = [];
        const byCategory = {};
        for (const m of getMetricsForTab(this.state.activeTab).filter((x) => this._blockAllowed(x))) {
            if (!byCategory[m.category]) {
                byCategory[m.category] = [];
                order.push(m.category);
            }
            byCategory[m.category].push(m);
        }
        return order.map((category) => ({ category, metrics: byCategory[category] }));
    }

    chartTypeLabel(type) {
        return CHART_TYPE_LABELS[type] || (type || "").toUpperCase();
    }

    // ------------------------------------------------------------------
    // Lectura de métricas para la plantilla (genérico por registry)
    // ------------------------------------------------------------------

    visibleMetrics(kind) {
        return getMetricsForTab(this.state.activeTab).filter(
            (m) => m.kind === kind && this._blockAllowed(m)
                && this.state.metricsConfig[m.id] && this.state.metricsConfig[m.id].visible
        );
    }

    _dataForMetric(metric) {
        return this.state.tabData[metric.tab];
    }

    metricKpi(metric) {
        const data = this._dataForMetric(metric);
        return data ? getByPath(data, metric.dataPath) : null;
    }

    kpiStatusClass(metric) {
        const raw = metric.rich ? this.metricKpi(metric) : null;
        if (!raw) {
            return "";
        }
        return `o_hud_status_${raw.status || "info"}${raw.action ? " o_hud_kpi_clickable" : ""}`;
    }

    kpiHint(metric) {
        const raw = metric.rich ? this.metricKpi(metric) : null;
        return raw ? raw.hint : "";
    }

    onKpiClick(metric) {
        const raw = metric.rich ? this.metricKpi(metric) : null;
        if (raw && raw.action) {
            this.openAction(raw.action);
        }
    }

    formatKpiValue(metric) {
        const raw = this.metricKpi(metric);
        if (metric.rich) {
            if (!raw || raw.value === null || raw.value === undefined) {
                return "—";
            }
            return raw.display !== undefined && raw.display !== null ? raw.display : Number(raw.value).toLocaleString("es-AR");
        }
        const value = metric.sparkline ? (raw ? raw.value : null) : raw;
        if (value === null || value === undefined) {
            return "—";
        }
        if (metric.format === "currency") {
            const store = this.state.tabData.tienda;
            const symbol = (store && store.currency_symbol) || "$";
            return symbol + Number(value).toLocaleString("es-AR", { maximumFractionDigits: 0 });
        }
        if (metric.format === "percent") {
            return value + "%";
        }
        return Number(value).toLocaleString("es-AR");
    }

    tableData(metric) {
        const data = this._dataForMetric(metric);
        return data ? getByPath(data, metric.dataPath) : null;
    }

    // ------------------------------------------------------------------
    // Chat con el Coordinador (ai.coordinator.route_message)
    // ------------------------------------------------------------------

    _onChatKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendChatMessage();
        }
    }

    async sendChatMessage() {
        const text = this.state.chat.input.trim();
        if (!text || this.state.chat.sending) {
            return;
        }
        this.state.chat.messages.push({ role: "user", content: text });
        this.state.chat.input = "";
        this.state.chat.sending = true;
        this._scrollChatToBottom();

        try {
            const result = await this.orm.call("ai.coordinator", "route_message", [text], {
                conversation_id: this.state.chat.conversationId || false,
            });
            if (result.conversation_id) {
                this.state.chat.conversationId = result.conversation_id;
            }
            this.state.chat.messages.push(this._formatCoordinatorReply(result));
            if (result.action === "approval_pending" || result.action === "executed") {
                // Refleja de inmediato el nuevo pendiente en el Vault / los KPIs.
                await this.refresh();
            }
        } catch (error) {
            const message = error?.data?.message || error?.message || "Ocurrió un error inesperado.";
            this.state.chat.messages.push({ role: "agent", content: message, isError: true });
        } finally {
            this.state.chat.sending = false;
            this._scrollChatToBottom();
        }
    }

    _formatCoordinatorReply(result) {
        if (result.error) {
            return { role: "agent", content: result.error, isError: true };
        }
        if (result.action === "executed") {
            const extra = result.result ? ` — ${JSON.stringify(result.result)}` : "";
            return { role: "agent", content: `✓ Ejecutado: ${result.tool}${extra}` };
        }
        if (result.action === "approval_pending") {
            return {
                role: "agent",
                content: `Esta acción requiere aprobación — quedó pendiente en el Vault (solicitud #${result.approval_request_id}).`,
            };
        }
        if (result.action === "clarification_needed") {
            return { role: "agent", content: result.message };
        }
        if (result.action === "error") {
            return { role: "agent", content: `Error: ${result.error}`, isError: true };
        }
        return { role: "agent", content: JSON.stringify(result) };
    }

    _scrollChatToBottom() {
        requestAnimationFrame(() => {
            const el = this.chatMessagesRef.el;
            if (el) {
                el.scrollTop = el.scrollHeight;
            }
        });
    }

    // ------------------------------------------------------------------
    // Chat genérico de "asistente" (metric.kind === "assistant") — para
    // asistentes de solo pregunta/respuesta (sin aprobaciones ni acciones),
    // distinto del chat del Coordinador. Cada metric.id tiene su propio
    // estado e historial; el modelo/método a invocar los da la métrica.
    // ------------------------------------------------------------------

    _onAssistantKeydown(ev, metric) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendAssistantMessage(metric);
        }
    }

    async sendAssistantMessage(metric) {
        const chat = this.state.assistants[metric.id];
        const text = (chat.input || "").trim();
        if (!text || chat.sending) {
            return;
        }
        const history = chat.messages.map((m) => ({ role: m.role, content: m.content }));
        chat.messages.push({ role: "user", content: text });
        chat.input = "";
        chat.sending = true;
        try {
            const result = await this.orm.call(metric.model, metric.method, [], {
                message: text, history, ...(metric.extraKwargs || {}),
            });
            chat.messages.push({ role: "agent", content: result.reply, isError: result.route === "error" });
        } catch (error) {
            const message = error?.data?.message || error?.message || "Ocurrió un error inesperado.";
            chat.messages.push({ role: "agent", content: message, isError: true });
        } finally {
            chat.sending = false;
        }
    }

    // ------------------------------------------------------------------
    // Render de gráficos (genérico, dirigido por hud_metrics_registry)
    // ------------------------------------------------------------------

    _baseOptions(extra = {}) {
        const base = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: PALETTE.text, font: { size: 11 } } },
            },
            scales: {
                x: { ticks: { color: PALETTE.text }, grid: { color: PALETTE.grid } },
                y: { ticks: { color: PALETTE.text }, grid: { color: PALETTE.grid } },
            },
        };
        return Object.assign(base, extra);
    }

    _withAlpha(hexColor, alpha) {
        const r = parseInt(hexColor.slice(1, 3), 16);
        const g = parseInt(hexColor.slice(3, 5), 16);
        const b = parseInt(hexColor.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    _buildChart(canvas, metric, payload, chartType) {
        const colors = [PALETTE.gold, PALETTE.blue, PALETTE.amber, PALETTE.green, PALETTE.red, PALETTE.goldLight];
        const labels = payload.labels || [];
        const seriesKeys = metric.series || ["values"];
        const seriesLabels = metric.seriesLabels || seriesKeys;

        if (chartType === "doughnut") {
            const values = payload[seriesKeys[0]] || [];
            return new window.Chart(canvas, {
                type: "doughnut",
                data: {
                    labels,
                    datasets: [{ data: values, backgroundColor: colors, borderColor: "#0d0d0d", borderWidth: 2 }],
                },
                options: this._baseOptions({ scales: undefined, cutout: "62%" }),
            });
        }

        if (chartType === "barh") {
            const values = payload[seriesKeys[0]] || [];
            return new window.Chart(canvas, {
                type: "bar",
                data: { labels, datasets: [{ label: seriesLabels[0], data: values, backgroundColor: PALETTE.gold }] },
                options: this._baseOptions({
                    indexAxis: "y",
                    scales: {
                        x: { min: 0, max: 100, ticks: { color: PALETTE.text }, grid: { color: PALETTE.grid } },
                        y: { ticks: { color: PALETTE.text }, grid: { color: PALETTE.grid } },
                    },
                }),
            });
        }

        const stacked = seriesKeys.length > 1;
        const isArea = chartType === "area";
        const isStep = chartType === "step";
        const datasets = seriesKeys.map((key, i) => ({
            label: seriesLabels[i],
            data: payload[key] || [],
            backgroundColor: isArea ? this._withAlpha(colors[i % colors.length], 0.18) : colors[i % colors.length],
            borderColor: colors[i % colors.length],
            fill: isArea,
            stepped: isStep,
            tension: isArea ? 0.3 : 0,
            pointRadius: isArea || isStep ? 2 : 0,
        }));

        return new window.Chart(canvas, {
            type: isArea || isStep ? "line" : "bar",
            data: { labels, datasets },
            options: this._baseOptions({
                scales: {
                    x: { stacked, ticks: { color: PALETTE.text }, grid: { color: PALETTE.grid } },
                    y: { stacked, ticks: { color: PALETTE.text, precision: 0 }, grid: { color: PALETTE.grid } },
                },
            }),
        });
    }

    _renderSparklines(data) {
        const metrics = getMetricsForTab(this.state.activeTab).filter(
            (m) => m.kind === "kpi" && m.sparkline && this.state.metricsConfig[m.id] && this.state.metricsConfig[m.id].visible
        );
        for (const metric of metrics) {
            const canvas = this.rootRef.el.querySelector(`[data-spark-id="${metric.id}"]`);
            const kpi = getByPath(data, metric.dataPath);
            if (!canvas || !kpi || !kpi.trend) {
                continue;
            }
            const positive = (kpi.delta_pct || 0) >= 0;
            const color = positive ? PALETTE.green : PALETTE.red;
            this.charts["spark_" + metric.id] = new window.Chart(canvas, {
                type: "line",
                data: {
                    labels: kpi.trend.map((_, i) => i),
                    datasets: [{
                        data: kpi.trend,
                        borderColor: color,
                        backgroundColor: this._withAlpha(color, 0.15),
                        fill: true,
                        tension: 0.35,
                        pointRadius: 0,
                        borderWidth: 1.5,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    plugins: { legend: { display: false }, tooltip: { enabled: false } },
                    scales: { x: { display: false }, y: { display: false } },
                },
            });
        }
    }

    _renderCharts() {
        Object.values(this.charts).forEach((c) => c && c.destroy());
        this.charts = {};

        const data = this.state.tabData[this.state.activeTab];
        if (!data || !window.Chart || !this.rootRef.el) {
            return;
        }

        const chartMetrics = getMetricsForTab(this.state.activeTab).filter(
            (m) => m.kind === "chart" && this._blockAllowed(m)
                && this.state.metricsConfig[m.id] && this.state.metricsConfig[m.id].visible
        );
        for (const metric of chartMetrics) {
            const canvas = this.rootRef.el.querySelector(`[data-chart-id="${metric.id}"]`);
            const payload = getByPath(data, metric.dataPath);
            if (!canvas || !payload) {
                continue;
            }
            const chartType = this.state.metricsConfig[metric.id].chartType || metric.defaultChartType;
            this.charts[metric.id] = this._buildChart(canvas, metric, payload, chartType);
        }

        this._renderSparklines(data);
    }
}

registry.category("actions").add("ops_hud_dashboard", OpsHudDashboard);
