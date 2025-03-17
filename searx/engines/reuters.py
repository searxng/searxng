# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reuters (news)"""

from json import dumps
from urllib.parse import quote_plus
from datetime import datetime, timedelta

from searx.utils import gen_useragent

about = {
    'website': "https://www.reuters.com",
    'wikidata_id': "Q130879",
    'official_api_documentation': None,
    'use_official_api': False,
    'require_api_key': False,
    'results': 'JSON',
}

categories = ['news']
time_range_support = True
paging = True

base_url = "https://www.reuters.com"

results_per_page = 20
sort_order = 'relevance'  # other options: display_date:desc, display_data:asc

time_range_duration_map = {
    'day': 1,
    'week': 7,
    'month': 30,
    'year': 365,
}


def request(query, params):
    args = {
        'keyword': query,
        'offset': (params['pageno'] - 1) * results_per_page,
        'orderby': sort_order,
        'size': results_per_page,
        'website': 'reuters',
    }
    if params['time_range']:
        time_diff_days = time_range_duration_map[params['time_range']]
        start_date = datetime.now() - timedelta(days=time_diff_days)
        args['start_date'] = start_date.isoformat()

    params['url'] = f'{base_url}/pf/api/v3/content/fetch/articles-by-search-v2?query={quote_plus(dumps(args))}'
    params['headers']['User-Agent'] = gen_useragent()
    return params


def response(resp):
    results = []

    for result in resp.json().get('result', {}).get('articles', []):
        results.append(
            {
                'url': base_url + result['canonical_url'],
                'title': result['web'],
                'content': result['description'],
                'publishedDate': datetime.strptime(result['display_time'], '%Y-%m-%dT%H:%M:%SZ'),
                'thumbnail': result.get('thumbnail', {}).get('url', ''),
                'metadata': result.get('kicker', {}).get('name'),
            }
        )

    return results
