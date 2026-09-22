# -*- coding: utf-8 -*-
{
    'name': 'Ops HUD Dashboard',
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Centro de comando visual (HUD) para métricas, IA y aprobaciones',
    'description': """
Ops HUD Dashboard
==================
Panel de control estilo "centro de comando" con estética oscura/dorada.

Paneles incluidos en esta primera versión:

* Chat con el Agente Coordinador (ai.coordinator.route_message): lenguaje
  natural, delega a la herramienta correspondiente, crea aprobaciones en
  el Vault cuando el riesgo lo exige.
* KPIs globales de publicaciones en redes sociales.
* Gráfica de publicaciones por red social (dona).
* Gráfica de interacciones por red social (barras apiladas).
* Tendencia de publicaciones de los últimos 30 días (línea).
* Uso comparado entre proveedores de IA - Claude vs Gemini (dona).
* Tasa de éxito por proveedor de IA (barras horizontales).
* Estado de conexión de cuentas (chips de estado).
* Top 5 publicaciones por interacciones (tabla).
* Catálogo de "skills" activas.
* Panel de atención / cola de aprobaciones (placeholder hasta ai_agent_core).
* Panel de Métricas: elegí qué KPIs/gráficos ver y con qué tipo de gráfico,
  por pestaña, con preferencia guardada por navegador.
* Pestaña Tienda: ventas y finanzas (sale.order / account.move) — sin
  compras/stock/tienda online, que no están instalados en esta base.

Depende de social_agent_publisher para los datos de publicaciones y proveedores
de IA, y de sale/account para la pestaña Tienda. No requiere infraestructura
adicional: toda la agregación ocurre en el propio Odoo.
""",
    'author': 'Custom Development',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'social_agent_publisher', 'ai_agent_core', 'sale', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/hud_actions.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'web/static/lib/Chart/Chart.js',
            'ops_hud_dashboard/static/src/scss/hud_dashboard.scss',
            'ops_hud_dashboard/static/src/js/hud_metrics_registry.js',
            'ops_hud_dashboard/static/src/js/hud_dashboard.js',
            'ops_hud_dashboard/static/src/xml/hud_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
