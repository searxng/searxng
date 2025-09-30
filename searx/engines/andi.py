# SPDX-License-Identifier: AGPL-3.0-or-later
"""Andi Search engine"""

from urllib.parse import urlencode

about = {
    "website": 'https://andisearch.com',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['general']
paging = False

base_url = 'https://andisearch.com'


def request(query, params):
    query_params = {'q': query}
    params['url'] = f'{base_url}/search?{urlencode(query_params)}'
    return params


def response(resp):
    """Return a link to Andi Search"""
    results = []

    query = resp.search_params.get('query', '')
    url = f'{base_url}/search?q={query}'
    results.append({
        'title': f'Search Andi for: {query}',
        'url': url,
        'content': 'AI-powered search engine with direct answers and sources.',
    })

    return results