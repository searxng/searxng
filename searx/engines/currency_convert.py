# SPDX-License-Identifier: AGPL-3.0-or-later
"""Currency convert (DuckDuckGo)
"""

import json

# about
about = {
    "website": 'https://duckduckgo.com/',
    "wikidata_id": 'Q12805',
    "official_api_documentation": 'https://duckduckgo.com/api',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSONP',
    "description": "Service from DuckDuckGo.",
}

engine_type = 'online_currency'
categories = []
base_url = 'https://duckduckgo.com/js/spice/currency/1/{0}/{1}'
weight = 100

https_support = True


def request(_query, params):
    params['url'] = base_url.format(params['from'], params['to'])
    return params


def response(resp):
    # remove first and last lines to get only json
    json_resp = resp.text[resp.text.find('\n') + 1 : resp.text.rfind('\n') - 2]
    try:
        conversion_rate = float(json.loads(json_resp)["to"][0]["mid"])
    except IndexError:
        return []
    answer = '{0} {1} = {2} {3}, 1 {1} ({5}) = {4} {3} ({6})'.format(
        resp.search_params['amount'],
        resp.search_params['from'],
        resp.search_params['amount'] * conversion_rate,
        resp.search_params['to'],
        conversion_rate,
        resp.search_params['from_name'],
        resp.search_params['to_name'],
    )

    url = f"https://duckduckgo.com/?q={resp.search_params['from']}+to+{resp.search_params['to']}"

    return [{"answer": answer, "url": url}]
