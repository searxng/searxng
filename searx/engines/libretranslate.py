# SPDX-License-Identifier: AGPL-3.0-or-later
"""LibreTranslate (Free and Open Source Machine Translation API)"""

import random
import json
from searx.result_types import EngineResults

about = {
    "website": 'https://libretranslate.com',
    "wikidata_id": None,
    "official_api_documentation": 'https://libretranslate.com/docs/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

engine_type = 'online_dictionary'
categories = ['general', 'translate']

base_url = "https://libretranslate.com/translate"
api_key = ""


def request(_query, params):
    request_url = random.choice(base_url) if isinstance(base_url, list) else base_url

    if request_url.startswith("https://libretranslate.com") and not api_key:
        return None
    params['url'] = f"{request_url}/translate"

    args = {
        'q': params['query'],
        'source': params['from_lang'][1],
        'target': params['to_lang'][1],
        'alternatives': 3,
    }
    if api_key:
        args['api_key'] = api_key

    params['data'] = json.dumps(args)
    params['method'] = 'POST'
    params['headers'] = {'Content-Type': 'application/json'}
    params['req_url'] = request_url

    return params


def response(resp) -> EngineResults:
    results = EngineResults()

    json_resp = resp.json()
    text = json_resp.get('translatedText')
    if not text:
        return results

    item = results.types.Translations.Item(text=text, examples=json_resp.get('alternatives', []))
    results.add(results.types.Translations(translations=[item]))

    return results
