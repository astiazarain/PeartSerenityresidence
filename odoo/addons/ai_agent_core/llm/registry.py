# -*- coding: utf-8 -*-
"""Registro de proveedores: cómo se habla con cada uno.

Aquí va solo lo técnico del endpoint (protocolo, URL base, rutas, cómo se
autentica el health check). Lo que cambia cada pocos meses —precios,
ventana de contexto, límites del tier gratuito— NO va aquí: vive en el
modelo ``ai.model.spec``, editable desde la interfaz.

Groq, DeepSeek, Mistral, OpenRouter y Abacus (RouteLLM) exponen la API de
OpenAI (``POST {base_url}/chat/completions``): comparten el adaptador
``openai`` y solo difieren en estos datos. Añadir otro proveedor
compatible es añadir una entrada aquí y su valor en la selección.
"""

OPENAI = 'openai'
ANTHROPIC = 'anthropic'
GEMINI = 'gemini'
OLLAMA = 'ollama'

PROVIDER_REGISTRY = {
    'anthropic': {
        'label': 'Claude (Anthropic)',
        'protocol': ANTHROPIC,
        'default_model': 'claude-sonnet-5',
        'catalog': 'anthropic',
        'key_url': 'https://console.anthropic.com/settings/keys',
    },
    'google': {
        'label': 'Gemini (Google)',
        'protocol': GEMINI,
        'default_model': 'gemini-2.5-flash',
        'catalog': 'gemini',
        'key_url': 'https://aistudio.google.com/apikey',
    },
    'openai': {
        'label': 'ChatGPT (OpenAI)',
        'protocol': OPENAI,
        'base_url': 'https://api.openai.com/v1',
        'default_model': 'gpt-4o-mini',
        'catalog': 'openai',
        'health': ('/models', 'bearer'),
        'key_url': 'https://platform.openai.com/api-keys',
    },
    'groq': {
        'label': 'Groq',
        'protocol': OPENAI,
        'base_url': 'https://api.groq.com/openai/v1',
        'default_model': 'openai/gpt-oss-120b',
        'catalog': 'openai_compatible',
        'health': ('/models', 'bearer'),
        'key_url': 'https://console.groq.com/keys',
        'free_tier_note': 'Tier gratuito con límites por modelo (RPM/RPD/TPM/TPD): '
                          'ver la ficha de cada modelo en "Especificaciones de modelos".',
    },
    'deepseek': {
        'label': 'DeepSeek',
        'protocol': OPENAI,
        'base_url': 'https://api.deepseek.com',
        'default_model': 'deepseek-flash',
        'catalog': 'openai_compatible',
        # /user/balance valida la clave y no genera: /models también la
        # pide, pero el saldo dice además si la cuenta puede operar.
        'health': ('/user/balance', 'bearer'),
        'key_url': 'https://platform.deepseek.com/api_keys',
        'free_tier_note': 'Sin tier gratuito ni límites RPM/TPM publicados: limita '
                          'por conexiones simultáneas y cobra por uso (402 sin saldo).',
    },
    'mistral': {
        'label': 'Mistral',
        'protocol': OPENAI,
        'base_url': 'https://api.mistral.ai/v1',
        'default_model': 'mistral-small-latest',
        'catalog': 'mistral',
        'health': ('/models', 'bearer'),
        'key_url': 'https://console.mistral.ai/api-keys',
        'free_tier_note': 'El plan gratuito incluye crédito mensual de API; Mistral no '
                          'publica sus límites RPM/TPM (dependen del plan de la cuenta).',
    },
    'openrouter': {
        'label': 'OpenRouter',
        'protocol': OPENAI,
        'base_url': 'https://openrouter.ai/api/v1',
        'default_model': 'openrouter/auto',
        'catalog': 'openrouter',
        # /models es público en OpenRouter: no probaría la clave. /key sí.
        'health': ('/key', 'bearer'),
        'key_url': 'https://openrouter.ai/settings/keys',
        'free_tier_note': 'Modelos ":free": 20 peticiones/min y 50/día (1000/día con '
                          '10 USD o más de crédito comprado).',
    },
    'abacus': {
        'label': 'Abacus.AI (RouteLLM)',
        'protocol': OPENAI,
        'base_url': 'https://routellm.abacus.ai/v1',
        'default_model': 'route-llm',
        'catalog': 'abacus',
        # /v1/models de RouteLLM es público: no probaría la clave. La API
        # v0 de Abacus sí la exige (responde 403 "Invalid API Key") y no
        # genera nada.
        'health': ('https://routellm.abacus.ai/api/v0/describeUser', 'apikey'),
        'key_url': 'https://abacus.ai/app/route-llm-apis',
        'free_tier_note': 'Sin tier gratuito publicado: se cobra por token según el '
                          'modelo al que enrute RouteLLM.',
    },
    'ollama': {
        'label': 'Ollama (servidor local)',
        'protocol': OLLAMA,
        'base_url': 'http://localhost:11434',
        'default_model': 'llama3.2',
        'catalog': 'ollama',
    },
}

PROVIDER_SELECTION = [(code, spec['label']) for code, spec in PROVIDER_REGISTRY.items()]

# Proveedores sin API de imágenes en este módulo: el modelo de texto dibuja
# la imagen en SVG (ver ai.provider.config._generate_svg_image).
SVG_IMAGE_PROVIDERS = tuple(
    code for code, spec in PROVIDER_REGISTRY.items() if code not in ('google', 'openai')
)

# Antes de 19.0.2.0.0, base_url tenía este default para TODOS los
# proveedores (era un campo pensado solo para Ollama). La migración lo
# limpia en los que no son Ollama.
LEGACY_BASE_URL_DEFAULT = 'http://localhost:11434'


def provider_spec(code):
    return PROVIDER_REGISTRY.get(code) or {}


def protocol_of(code):
    return provider_spec(code).get('protocol')
