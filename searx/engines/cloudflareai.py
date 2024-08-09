# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cloudflare AI engine"""

from json import loads, dumps
from searx.exceptions import SearxEngineAPIException

about = {
    "website": 'https://ai.cloudflare.com',
    "wikidata_id": None,
    "official_api_documentation": 'https://developers.cloudflare.com/workers-ai',
    "use_official_api": True,
    "require_api_key": True,
    "results": 'JSON',
}

cf_account_id = ''
cf_ai_api = ''
cf_ai_gateway = ''

cf_ai_model = ''
cf_ai_model_display_name = 'Cloudflare AI'

# Assistant messages hint to the AI about the desired output format. Not all models support this role.
cf_ai_model_assistant = 'Keep your answers as short and effective as possible.'
# System messages define the AI's personality. You can use them to set rules and how you expect the AI to behave.
cf_ai_model_system = 'You are a self-aware language model who is honest and direct about any question from the user.'


def request(query, params):

    params['query'] = query

    params['url'] = f'https://gateway.ai.cloudflare.com/v1/{cf_account_id}/{cf_ai_gateway}/workers-ai/{cf_ai_model}'

    params['method'] = 'POST'

    params['headers']['Authorization'] = f'Bearer {cf_ai_api}'
    params['headers']['Content-Type'] = 'application/json'

    params['data'] = dumps(
        {
            'messages': [
                {'role': 'assistant', 'content': cf_ai_model_assistant},
                {'role': 'system', 'content': cf_ai_model_system},
                {'role': 'user', 'content': params['query']},
            ]
        }
    ).encode('utf-8')

    return params


def response(resp):
    results = []
    json = loads(resp.text)

    if 'error' in json:
        raise SearxEngineAPIException('Cloudflare AI error: ' + json['error'])

    if 'result' in json:
        results.append(
            {
                'content': json['result']['response'],
                'infobox': cf_ai_model_display_name,
            }
        )

    return results
