# SPDX-License-Identifier: AGPL-3.0-or-later
"""Marginalia Search"""

from urllib.parse import urlencode, quote_plus
from searx.utils import searxng_useragent

about = {
    "website": 'https://marginalia.nu',
    "wikidata_id": None,
    "official_api_documentation": 'https://about.marginalia-search.com/article/api/',
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

base_url = "https://api.marginalia.nu"
safesearch = True
categories = ['general']
paging = False
results_per_page = 20
api_key = ""


def request(query, params):

    query_params = {
        "count": results_per_page,
        "nsfw": min(params['safesearch'], 1),
    }

    params["url"] = f"{base_url}/{api_key}/search/{quote_plus(query)}?{urlencode(query_params)}"

    params['headers'] = {
        'User-Agent': searxng_useragent(),
    }

    return params


def response(resp):
    search_res = resp.json()

    results = []

    for item in search_res.get('results', []):
        results.append(
            {
                "url": item['url'],
                "title": item['title'],
                "content": item['description'],
            }
        )

    return results
