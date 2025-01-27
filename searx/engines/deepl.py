# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deepl translation engine"""

from searx.result_types import EngineResults

about = {
    "website": 'https://deepl.com',
    "wikidata_id": 'Q43968444',
    "official_api_documentation": 'https://www.deepl.com/docs-api',
    "use_official_api": True,
    "require_api_key": True,
    "results": 'JSON',
}

engine_type = 'online_dictionary'
categories = ['general', 'translate']

url = 'https://api-free.deepl.com/v2/translate'
api_key = None


def request(_query, params):
    '''pre-request callback

    params<dict>:

    - ``method`` : POST/GET
    - ``headers``: {}
    - ``data``: {}  # if method == POST
    - ``url``: ''
    - ``category``: 'search category'
    - ``pageno``: 1  # number of the requested page
    '''

    params['url'] = url
    params['method'] = 'POST'
    params['data'] = {'auth_key': api_key, 'text': params['query'], 'target_lang': params['to_lang'][1]}

    return params


def response(resp) -> EngineResults:

    res = EngineResults()
    data = resp.json()
    if not data.get('translations'):
        return res

    translations = [res.types.Translations.Item(text=t['text']) for t in data['translations']]
    res.add(res.types.Translations(translations=translations))

    return res
