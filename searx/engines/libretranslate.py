# SPDX-License-Identifier: AGPL-3.0-or-later
"""LibreTranslate (Free and Open Source Machine Translation API)"""

import random
from json import dumps

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

base_url = "https://translate.terraprint.co"
api_key = ''


def request(_query, params):
    request_url = random.choice(base_url) if isinstance(base_url, list) else base_url
    params['url'] = f"{request_url}/translate"

    args = {'source': params['from_lang'][1], 'target': params['to_lang'][1], 'q': params['query'], 'alternatives': 3}
    if api_key:
        args['api_key'] = api_key
    params['data'] = dumps(args)

    params['method'] = 'POST'
    params['headers'] = {'Content-Type': 'application/json'}
    params['req_url'] = request_url

    return params


def response(resp):
    results = []

    json_resp = resp.json()
    text = json_resp.get('translatedText')

    if not text:
        return results

    translations = [{'text': text}] + [{'text': alternative} for alternative in json_resp.get('alternatives', [])]

    results.append({'answer': text, 'answer_type': 'translations', 'translations': translations})

    return results
