# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stract is an independent open source search engine.  At this state, it's
still in beta and hence this implementation will need to be updated once beta
ends.

"""

from json import dumps
from searx.utils import searx_useragent

about = {
    "website": "https://stract.com/",
    "use_official_api": True,
    "official_api_documentation": "https://stract.com/beta/api/docs/#/search/api",
    "require_api_key": False,
    "results": "JSON",
}
categories = ['general']
paging = True

search_url = "https://stract.com/beta/api/search"


def request(query, params):
    params['url'] = search_url
    params['method'] = "POST"
    params['headers'] = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': searx_useragent(),
    }
    params['data'] = dumps({'query': query, 'page': params['pageno'] - 1})

    return params


def response(resp):
    results = []

    for result in resp.json()["webpages"]:
        results.append(
            {
                'url': result['url'],
                'title': result['title'],
                'content': ''.join(fragment['text'] for fragment in result['snippet']['text']['fragments']),
            }
        )

    return results
