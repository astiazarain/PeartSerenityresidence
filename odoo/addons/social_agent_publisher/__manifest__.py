# -*- coding: utf-8 -*-
{
    'name': 'Social Agent Publisher',
    'version': '19.0.1.0.0',
    'category': 'Marketing',
    'summary': 'Agente para generar y publicar contenido en redes sociales usando Claude o Gemini',
    'description': """
Social Agent Publisher
=======================
Módulo genérico para Odoo 19 Community que permite:

* Configurar cuentas de redes sociales (Facebook, Instagram, LinkedIn, X/Twitter,
  TikTok o un webhook genérico para cualquier otro sistema).
* Conectar Facebook/Instagram, LinkedIn, X (Twitter) y TikTok con un clic
  mediante OAuth2 (sin copiar tokens a mano), con renovación automática de
  tokens de corta duración (X/TikTok) mediante un cron.
* Configurar uno o varios proveedores de IA (Claude - Anthropic, o Gemini - Google)
  para generar el contenido de las publicaciones.
* Crear publicaciones, generarlas con IA, revisarlas/editarlas, programarlas y
  publicarlas automáticamente mediante un cron.
* Analítica de publicaciones: pivote y gráfico por red social/estado, con
  métricas reales de me gusta, comentarios, compartidos e impresiones
  (Facebook, Instagram, LinkedIn, X) actualizadas automáticamente por cron.

No depende de ningún módulo de Odoo Enterprise.
""",
    'author': 'Custom Development',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/social_agent_security.xml',
        'security/ir.model.access.csv',
        'data/ai_provider_data.xml',
        'data/ir_cron_data.xml',
        'views/ai_provider_config_views.xml',
        'views/social_oauth_app_views.xml',
        'views/social_media_account_views.xml',
        'views/social_media_post_views.xml',
        'views/social_media_analytics_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
