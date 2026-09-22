# -*- coding: utf-8 -*-
import json
from unittest.mock import MagicMock

REQUESTS = 'odoo.addons.ai_agent_core.models.ai_provider_config.requests'


def fake_response(status, payload=None, headers=None, text=None):
    response = MagicMock()
    response.status_code = status
    if isinstance(payload, (dict, list)):
        response.json.return_value = payload
        response.text = text if text is not None else json.dumps(payload)
    else:
        response.json.side_effect = ValueError('not json')
        response.text = text if text is not None else (payload or '')
    response.headers = headers or {}
    return response


def chat_ok(text='ok', prompt_tokens=10, completion_tokens=5, **usage):
    return fake_response(200, {
        'choices': [{'message': {'content': text}, 'finish_reason': 'stop'}],
        'usage': dict(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, **usage),
    })


def ollama_ok(text='respuesta local'):
    return fake_response(200, {'message': {'content': text}, 'prompt_eval_count': 7, 'eval_count': 3})
