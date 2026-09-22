# -*- coding: utf-8 -*-
{
    'name': 'Ops HUD - Residencia',
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Pestaña "Residencia" del Centro de Control: seguridad clínica, cumplimiento, ocupación y familias',
    'description': """
Ops HUD - Residencia
====================
Agrega la pestaña RESIDENCIA al Centro de Control (ops_hud_dashboard) con los
indicadores del expediente clínico (peart_clinical_record):

* Dosis atrasadas o no administradas, registros de turno cerrados, valores
  fuera de rango, incidentes abiertos, caídas, cumplimiento vencido, ocupación,
  portal familiar y ARIA para familias.
* Semáforo con umbrales configurables (Residents > Configuration > HUD thresholds).
* Cola de atención: pendientes accionables, cada uno abre el registro.
* Tendencias de 30 días calculadas sobre los propios datos.

Cada rol ve solo sus bloques, y lo decide el servidor:
CEO todo; Médico seguridad, cumplimiento y familias; Enfermera lo del turno;
Administrador solo lo operativo (sin datos clínicos).
""",
    'author': 'Peart Serenity Residence',
    'license': 'LGPL-3',
    'depends': ['ops_hud_dashboard', 'peart_clinical_record'],
    'data': [
        'security/ir.model.access.csv',
        'data/threshold_data.xml',
        'views/threshold_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ops_hud_clinical/static/src/js/hud_clinical_registry.js',
        ],
    },
    'installable': True,
    'auto_install': False,
}
