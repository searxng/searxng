# SPDX-License-Identifier: AGPL-3.0-or-later
"""Baidu Maps"""

import json
import re
from urllib.parse import urlencode, quote_plus

from zhensa.result_types import EngineResults

about = {
    "website": 'https://map.baidu.com',
    "wikidata_id": 'Q483891',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['map']
paging = False


def request(query, params):
    """Baidu Maps search request"""

    # Baidu Maps search URL
    query_url = 'https://map.baidu.com/su?' + urlencode({
        'wd': query,
        'type': '0',
        'pc_ver': '2',
    })

    params['url'] = query_url
    params['headers']['Referer'] = 'https://map.baidu.com/'
    params['headers']['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

    return params


def response(resp):
    """Parse Baidu Maps search results"""
    results = []

    try:
        # Baidu Maps returns JSON data
        data = json.loads(resp.text)

        # Extract place suggestions from the response
        if 's' in data:
            for suggestion in data['s'][:10]:  # Limit to 10 results
                if isinstance(suggestion, str) and suggestion.strip():
                    # Create a map result for each suggestion
                    place_name = suggestion.strip()

                    results.append({
                        'template': 'map.html',
                        'title': place_name,
                        'url': f'https://map.baidu.com/search/{quote_plus(place_name)}',
                        'address': {
                            'name': place_name,
                        },
                    })

    except (json.JSONDecodeError, KeyError, TypeError):
        # If JSON parsing fails, try to extract from HTML
        pass

    # If no results from suggestions, provide a direct search link
    if not results:
        query = resp.search_params.get('query', '')
        results.append({
            'template': 'map.html',
            'title': f'Search for "{query}" on Baidu Maps',
            'url': f'https://map.baidu.com/search/{quote_plus(query)}',
            'address': {
                'name': f'Map search: {query}',
            },
        })

    return results