# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Deepl translation engine"""

from json import loads

about = {
    "website": 'https://deepl.com',
    "wikidata_id": 'Q43968444',
    "official_api_documentation": 'https://www.deepl.com/docs-api',
    "use_official_api": True,
    "require_api_key": True,
    "results": 'JSON',
}

engine_type = 'online_dictionary'
categories = ['general']

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


def response(resp):
    results = []
    result = loads(resp.text)
    translations = result['translations']

    infobox = "<dl>"

    for translation in translations:
        infobox += f"<dd>{translation['text']}</dd>"

    infobox += "</dl>"

    results.append(
        {
            'infobox': 'Deepl',
            'content': infobox,
        }
    )

    return results
