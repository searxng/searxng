# SPDX-License-Identifier: AGPL-3.0-or-later
"""Grokipedia (general)"""

from urllib.parse import urlencode
from searx.utils import html_to_text

about = {
    "website": 'https://grokipedia.com',
    "wikidata_id": "Q136410803",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

base_url = "https://grokipedia.com/api/full-text-search"
categories = ['general']
paging = True
results_per_page = 10


def request(query, params):

    start_index = (params["pageno"] - 1) * results_per_page

    query_params = {
        "query": query,
        "limit": results_per_page,
        "offset": start_index,
    }

    params["url"] = f"{base_url}?{urlencode(query_params)}"

    return params


def response(resp):
    search_res = resp.json()
    results = []

    for item in search_res.get("results", []):

        results.append(
            {
                'url': 'https://grokipedia.com/page/' + item["slug"],
                'title': item["title"],
                'content': html_to_text(item["snippet"]),
            }
        )

    return results
