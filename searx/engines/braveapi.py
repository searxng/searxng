# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Brave Search API Engine
======================

This engine uses the official Brave Search API for search queries.

Configuration
------------

.. code:: yaml

  - name: braveapi
    engine: braveapi
    api_key: 'YOUR-API-KEY'  # Required
    safesearch: true  # Optional
    
Supported categories:
- web (default)
- news 
- videos
- images

The API supports paging and time filters.
"""

from urllib.parse import urlencode
import json
from datetime import datetime
from dateutil import parser


from searx.network import get as http_get
from searx.exceptions import SearxEngineAPIException

about = {
    "website": "https://api.search.brave.com/",
    "wikidata_id": "Q22906900",
    "official_api_documentation": "https://api-dashboard.search.brave.com/documentation",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

api_key = ''
categories = ['general', 'news', 'videos', 'images']
paging = True
safe_search = True
time_range_support = True

base_url = 'https://api.search.brave.com/res/v1/web/search'

time_range_map = {
    'day': 'past_day',
    'week': 'past_week',
    'month': 'past_month',
    'year': 'past_year'
}

def request(query, params):
    """Creates the API request"""
    
    if api_key == "":
        raise SearxEngineAPIException('No API key provided')
    
    search_args = {
        'q': query,
        'count': 20,
    }
    
    # Seitennavigation
    if params.get('pageno'):
        search_args['offset'] = (params['pageno'] - 1) * 20
        
    # Zeitfilter
    if params.get('time_range'):
        search_args['time_range'] = time_range_map.get(params['time_range'])
        
    # SafeSearch
    if params['safesearch']:
        search_args['safesearch'] = 'strict'
        
    params['url'] = f'{base_url}?{urlencode(search_args)}'
    params['headers']['X-Subscription-Token'] = api_key
    
    return params


def _extract_published_date(published_date_raw: str | None):
    if published_date_raw is None:
        return None
    try:
        return parser.parse(published_date_raw)
    except parser.ParserError:
        return None

def response(resp):
    """Processes the API response"""
    results = []
    
    if not resp.ok:
        raise SearxEngineAPIException(f'HTTP error {resp.status_code}')
        
    data = json.loads(resp.text)
    
    for result in data.get('web', {}).get('results', []):
        results.append({
            'url': result['url'],
            'title': result['title'],
            'content': result.get('description', ''),
            'publishedDate': _extract_published_date(result.get('age')),
            'thumbnail': result.get('thumbnail', {}).get('src'),
            'template': 'default.html'
        })
        
    return results
