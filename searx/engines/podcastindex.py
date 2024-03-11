# SPDX-License-Identifier: AGPL-3.0-or-later
"""Podcast Index
"""

from urllib.parse import quote_plus
from datetime import datetime

about = {
    'website': 'https://podcastindex.org',
    'official_api_documentation': None,  # requires an account
    'use_official_api': False,
    'require_api_key': False,
    'results': 'JSON',
}
categories = []

base_url = "https://podcastindex.org"


def request(query, params):
    params['url'] = f"{base_url}/api/search/byterm?q={quote_plus(query)}"
    return params


def response(resp):
    results = []

    json = resp.json()

    for result in json['feeds']:
        results.append(
            {
                'url': result['link'],
                'title': result['title'],
                'content': result['description'],
                'thumbnail': result['image'],
                'publishedDate': datetime.utcfromtimestamp(result['newestItemPubdate']),
                'metadata': f"{result['author']}, {result['episodeCount']} episodes",
            }
        )

    return results
