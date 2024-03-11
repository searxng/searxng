# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fyyd (podcasts)
"""

from datetime import datetime
from urllib.parse import urlencode

about = {
    'website': 'https://fyyd.de',
    'official_api_documentation': 'https://github.com/eazyliving/fyyd-api',
    'use_official_api': True,
    'require_api_key': False,
    'results': 'JSON',
}
categories = []
paging = True

base_url = "https://api.fyyd.de"
page_size = 10


def request(query, params):
    args = {
        'term': query,
        'count': page_size,
        'page': params['pageno'] - 1,
    }
    params['url'] = f"{base_url}/0.2/search/podcast?{urlencode(args)}"
    return params


def response(resp):
    results = []

    json_results = resp.json()['data']

    for result in json_results:
        results.append(
            {
                'url': result['htmlURL'],
                'title': result['title'],
                'content': result['description'],
                'thumbnail': result['smallImageURL'],
                'publishedDate': datetime.strptime(result['status_since'], '%Y-%m-%d %H:%M:%S'),
                'metadata': f"Rank: {result['rank']} || {result['episode_count']} episodes",
            }
        )

    return results
