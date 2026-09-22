# -*- coding: utf-8 -*-
"""Resultado normalizado de una llamada de texto y lectura del uso de tokens,
que cada API informa con otros nombres."""
from collections import namedtuple

LlmResult = namedtuple('LlmResult', 'text input_tokens output_tokens reported_cost')


def _as_int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def parse_usage(protocol, data):
    """(tokens_entrada, tokens_salida, costo_informado_en_USD_o_None)."""
    data = data if isinstance(data, dict) else {}
    if protocol == 'openai':
        usage = data.get('usage') or {}
        cost = usage.get('cost')  # OpenRouter devuelve el costo real
        try:
            cost = float(cost) if cost is not None else None
        except (TypeError, ValueError):
            cost = None
        return _as_int(usage.get('prompt_tokens')), _as_int(usage.get('completion_tokens')), cost
    if protocol == 'anthropic':
        usage = data.get('usage') or {}
        return _as_int(usage.get('input_tokens')), _as_int(usage.get('output_tokens')), None
    if protocol == 'gemini':
        usage = data.get('usageMetadata') or {}
        # Los tokens de razonamiento se facturan como salida.
        output = _as_int(usage.get('candidatesTokenCount')) + _as_int(usage.get('thoughtsTokenCount'))
        return _as_int(usage.get('promptTokenCount')), output, None
    if protocol == 'ollama':
        return _as_int(data.get('prompt_eval_count')), _as_int(data.get('eval_count')), None
    return 0, 0, None
