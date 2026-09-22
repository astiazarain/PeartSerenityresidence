# -*- coding: utf-8 -*-
{
    'name': 'AI Agent Core',
    'version': '19.0.2.0.0',
    'category': 'Productivity',
    'summary': 'Núcleo de la capa agéntica ARIA: agentes, herramientas, aprobaciones y auditoría',
    'description': """
AI Agent Core (ARIA)
======================
Núcleo genérico, sin dependencias de dominio, para la capa de agentes de IA
descrita en ARIA_Especificacion_Tecnica.md.

Provee:

* ai.provider.config - abstracción sobre proveedores de IA: Claude, Gemini,
  Ollama y, sobre un único adaptador compatible con OpenAI, OpenAI, Groq,
  DeepSeek, Mistral, OpenRouter y Abacus (RouteLLM). Credenciales cifradas
  (ORBYLS_AI_VAULT_KEY), reintento con backoff ante 429, cadena de fallback
  con Ollama local como último recurso y health check sin consumo de tokens.
* ai.model.spec - contexto, precio y límites de cada modelo, para calcular
  el gasto de cada llamada.
* ai.agent - catálogo de agentes (Coordinador, Redes Sociales, Atención al Cliente...).
* ai.agent.tool - registro de herramientas por agente, con nivel de riesgo y
  contrato de ejecución.
* ai.approval.request - motor de aprobación para operaciones de riesgo 2 y 3.
* ai.audit.log - auditoría de toda operación ejecutada por un agente.
* ai.conversation / ai.conversation.message - memoria de conversación.
* Coordinador: enrutador simple de intención hacia el agente/herramienta
  correspondiente.

Los módulos de dominio (social_agent_publisher, ai_customer_agent) registran
sus herramientas aquí mediante datos XML/CSV o código de instalación; no hay
dependencia inversa de este módulo hacia ellos.
""",
    'author': 'Custom Development',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'external_dependencies': {'python': ['cryptography']},
    'data': [
        'security/ai_agent_security.xml',
        'security/ir.model.access.csv',
        'data/ai_agent_data.xml',
        'data/ir_cron_data.xml',
        'data/ai_model_spec_data.xml',
        'views/ai_agent_tool_views.xml',
        'views/ai_agent_views.xml',
        'views/ai_approval_request_views.xml',
        'views/ai_audit_log_views.xml',
        'views/ai_conversation_views.xml',
        'views/ai_provider_config_views.xml',
        'views/ai_model_spec_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
