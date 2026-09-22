# -*- coding: utf-8 -*-
"""Lectura del listado de modelos de cada API a una forma común.

Cada entrada es ``{'model_id', 'display_name', 'kind', 'spec'}``, donde
``spec`` trae lo que la API informe de contexto, precio y capacidades
(vacío si no informa nada): Mistral, OpenRouter y Abacus sí lo publican;
Groq solo el contexto; DeepSeek y OpenAI, nada.
"""

# Modelos que no sirven para generar texto de chat. Genérico para los
# compatibles con OpenAI; OpenAI conserva su heurística propia.
NON_CHAT_SUBSTRINGS = (
    'embed', 'whisper', 'tts', 'moderation', 'transcribe', 'guard',
    'rerank', 'orpheus', 'playai', 'ocr', 'safeguard',
)
OPENAI_EXCLUDED_SUBSTRINGS = (
    'embedding', 'whisper', 'tts', 'moderation', 'audio', 'realtime',
    'transcribe', 'davinci-002', 'babbage-002', 'computer-use', 'search-preview',
)
OPENAI_IMAGE_PREFIXES = ('dall-e', 'gpt-image')
OPENAI_TEXT_PREFIXES = ('gpt-', 'o1', 'o3', 'o4', 'chatgpt')

# OpenRouter: límite de los modelos ":free" sin crédito comprado.
OPENROUTER_FREE_RPM = 20
OPENROUTER_FREE_RPD = 50


def _per_token_to_per_million(value):
    """Las APIs de OpenRouter y Abacus dan USD por token, como texto.
    Negativo significa "variable" (p. ej. openrouter/auto): desconocido."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if number < 0 else round(number * 1_000_000, 6)


def _entry(model_id, display_name=None, kind='text', **spec):
    return {
        'model_id': model_id,
        'display_name': display_name or model_id,
        'kind': kind,
        'spec': {key: value for key, value in spec.items() if value not in (None, '')},
    }


def parse_openai(data):
    entries = []
    for model in data.get('data') or []:
        model_id = model.get('id') or ''
        lowered = model_id.lower()
        if not model_id or any(s in lowered for s in OPENAI_EXCLUDED_SUBSTRINGS):
            continue
        if lowered.startswith(OPENAI_IMAGE_PREFIXES):
            entries.append(_entry(model_id, kind='image'))
        elif lowered.startswith(OPENAI_TEXT_PREFIXES):
            entries.append(_entry(model_id))
    return entries


def parse_openai_compatible(data):
    """Groq y DeepSeek: ids en ``data``; Groq añade ``context_window`` y
    ``active``."""
    entries = []
    for model in data.get('data') or []:
        model_id = model.get('id') or ''
        if not model_id or model.get('active') is False:
            continue
        if any(s in model_id.lower() for s in NON_CHAT_SUBSTRINGS):
            continue
        entries.append(_entry(
            model_id,
            context_window=model.get('context_window'),
            max_output_tokens=model.get('max_completion_tokens'),
        ))
    return entries


def parse_mistral(data):
    entries = []
    for model in data.get('data') or []:
        model_id = model.get('id') or ''
        capabilities = model.get('capabilities') or {}
        if not model_id or capabilities.get('completion_chat') is False:
            continue
        if any(s in model_id.lower() for s in NON_CHAT_SUBSTRINGS):
            continue
        entries.append(_entry(
            model_id, model.get('name'),
            context_window=model.get('max_context_length'),
            supports_tools=capabilities.get('function_calling'),
        ))
    return entries


def parse_openrouter(data):
    entries = []
    for model in data.get('data') or []:
        model_id = model.get('id') or ''
        architecture = model.get('architecture') or {}
        if not model_id or 'text' not in (architecture.get('output_modalities') or ['text']):
            continue
        pricing = model.get('pricing') or {}
        input_cost = _per_token_to_per_million(pricing.get('prompt'))
        output_cost = _per_token_to_per_million(pricing.get('completion'))
        is_free = model_id.endswith(':free')
        top = model.get('top_provider') or {}
        entries.append(_entry(
            model_id, model.get('name'),
            context_window=model.get('context_length'),
            max_output_tokens=top.get('max_completion_tokens'),
            input_cost_per_mtok=input_cost,
            output_cost_per_mtok=output_cost,
            pricing_known=input_cost is not None and output_cost is not None,
            supports_tools='tools' in (model.get('supported_parameters') or []),
            free_rpm=OPENROUTER_FREE_RPM if is_free else None,
            free_rpd=OPENROUTER_FREE_RPD if is_free else None,
        ))
    return entries


def parse_abacus(data):
    models = data.get('data') if isinstance(data, dict) else data
    entries = []
    for model in models or []:
        model_id = model.get('id') or ''
        if not model_id or model.get('model_type') not in (None, 'text_generation'):
            continue
        if 'text' not in (model.get('output_modalities') or ['text']):
            continue
        input_cost = _per_token_to_per_million(model.get('input_token_rate'))
        output_cost = _per_token_to_per_million(model.get('output_token_rate'))
        entries.append(_entry(
            model_id, model.get('display_name') or model.get('name'),
            context_window=model.get('context_length'),
            max_output_tokens=model.get('max_completion_tokens'),
            input_cost_per_mtok=input_cost,
            output_cost_per_mtok=output_cost,
            pricing_known=input_cost is not None and output_cost is not None,
            supports_tools=model.get('tools'),
        ))
    return entries


PARSERS = {
    'openai': parse_openai,
    'openai_compatible': parse_openai_compatible,
    'mistral': parse_mistral,
    'openrouter': parse_openrouter,
    'abacus': parse_abacus,
}
