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

    args = {'source': params['from_lang'][1], 'target': params['to_lang'][1], 'q': params['query']}
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

    from_lang = resp.search_params["from_lang"][1]
    to_lang = resp.search_params["to_lang"][1]
    query = resp.search_params["query"]
    req_url = resp.search_params["req_url"]

    if text:
        results.append({"answer": text, "url": f"{req_url}/?source={from_lang}&target={to_lang}&q={query}"})

    return results
