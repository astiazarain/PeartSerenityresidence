/** @odoo-module **/

/**
 * Pestaña RESIDENCIA del Centro de Control. Se registra sobre el catálogo del
 * HUD (ops_hud_dashboard): agrega su pestaña y sus métricas. Cada métrica
 * lleva `block`; el servidor decide qué bloques recibe cada rol
 * (data.allowed_blocks), así que un rol nunca ve —ni recibe— lo que no le toca.
 */
import { TABS, METRICS } from "@ops_hud_dashboard/js/hud_metrics_registry";

TABS.push({ id: "residencia", label: "RESIDENCIA", method: "get_residence_dashboard_data" });

const kpi = (id, category, block, label, source, key) => ({
    id: `res_${id}`, tab: "residencia", category, block, kind: "kpi", rich: true,
    label, source, dataPath: `kpis.${key || id}`, defaultVisible: true,
});

METRICS.push(
    // Seguridad clínica
    kpi("meds", "Seguridad clínica", "meds", "Dosis atrasadas o no dadas hoy",
        "peart.medication.administration · atrasadas >60 min + rechazadas/omitidas/retenidas"),
    kpi("logs", "Seguridad clínica", "logs", "Registros de turno cerrados",
        "peart.daily.log · % cerrados del último turno vencido"),
    kpi("alerts", "Seguridad clínica", "logs", "Valores fuera de rango (24 h)",
        "peart.daily.log · signos vitales fuera de rango"),
    kpi("incidents", "Seguridad clínica", "incidents", "Incidentes abiertos",
        "peart.incident · abiertos, graves y con aviso pendiente"),
    kpi("falls", "Seguridad clínica", "incidents", "Caídas (30 días)",
        "peart.incident · tipo caída, vs. 30 días anteriores"),
    // Cumplimiento
    kpi("compliance", "Cumplimiento", "compliance", "Cumplimiento vencido",
        "valoraciones, planes de cuidados, ingresos y consentimientos"),
    // Ocupación
    kpi("occupancy", "Ocupación", "occupancy", "Ocupación",
        "peart.resident · en residencia + hospitalizados, admisiones en curso"),
    // Familias y ARIA
    kpi("aria", "Familias y ARIA", "family", "ARIA para familias (30 días)",
        "peart.family.access.log · preguntas, escaladas y errores", "aria"),
    kpi("family_pending", "Familias y ARIA", "family_q", "Preguntas de familias sin responder",
        "mail.activity · preguntas que ARIA pasó a enfermería", "family_pending"),
    kpi("portal", "Familias y ARIA", "portal", "Portal familiar",
        "peart.resident.family.link · vínculos y familias activas"),
    // Trazabilidad
    kpi("handover", "Entrega de turno", "handover", "Resumen de entrega de turno",
        "peart.shift.handover · generado a las 06:45 y 18:45"),
    kpi("approvals", "Aprobaciones pendientes", "approvals", "Aprobaciones pendientes (ARIA Clínica)",
        "peart.clinical.action.request · pendientes de aprobación del médico"),
    kpi("access", "Trazabilidad", "trace", "Accesos e informes (7 días)",
        "peart.family.access.log · aperturas de expediente e informes impresos"),

    { id: "res_trend_occupancy", tab: "residencia", category: "Ocupación", block: "occupancy", kind: "chart",
      label: "Ocupación (30 días)", source: "peart.resident · ingresos y altas por día",
      dataPath: "trend_occupancy", series: ["values"], seriesLabels: ["Residentes"],
      chartTypes: ["area", "bar", "step"], defaultChartType: "area", wide: true, defaultVisible: true },
    { id: "res_trend_safety", tab: "residencia", category: "Seguridad clínica", block: "incidents", kind: "chart",
      label: "Seguridad (30 días)", source: "incidentes, valores fuera de rango y dosis no dadas por día",
      dataPath: "trend_safety", series: ["incidents", "alerts", "not_given"],
      seriesLabels: ["Incidentes", "Valores fuera de rango", "Dosis no dadas"],
      chartTypes: ["bar", "area"], defaultChartType: "bar", wide: true, defaultVisible: true },

    { id: "res_aria_chat", tab: "residencia", category: "Familias y ARIA", block: "aria_chat", kind: "assistant",
      label: "ARIA Clínica", source: "Preguntas de solo lectura sobre residentes o el estado del turno. No receta ni cambia medicación.",
      model: "ai.clinical.assistant", method: "ask",
      placeholder: "Preguntá algo como \"¿qué dosis están atrasadas?\" o \"¿cómo está Winston Peart hoy?\"",
      inputPlaceholder: "Escribí tu pregunta para ARIA Clínica...", wide: true, defaultVisible: true },

    { id: "res_attention", tab: "residencia", category: "Cola de atención", block: "attention", kind: "table",
      label: "Cola de atención", source: "pendientes accionables; clic para abrir el registro",
      dataPath: "attention", wide: true, defaultVisible: true, emptyText: "Nada requiere atención en este momento.",
      columns: [
          { key: "severity", label: "Prioridad" }, { key: "area", label: "Área" },
          { key: "title", label: "Qué" }, { key: "detail", label: "Detalle" }, { key: "when", label: "Cuándo" },
      ] },
);
