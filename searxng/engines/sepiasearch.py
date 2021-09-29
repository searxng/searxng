# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 SepiaSearch (Videos)
"""

from json import loads
from dateutil import parser, relativedelta
from urllib.parse import urlencode
from datetime import datetime

# about
about = {
    "website": 'https://sepiasearch.org',
    "wikidata_id": None,
    "official_api_documentation": "https://framagit.org/framasoft/peertube/search-index/-/tree/master/server/controllers/api",  # NOQA
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['videos']
paging = True
time_range_support = True
safesearch = True
supported_languages = [
    'en', 'fr', 'ja', 'eu', 'ca', 'cs', 'eo', 'el',
    'de', 'it', 'nl', 'es', 'oc', 'gd', 'zh', 'pt',
    'sv', 'pl', 'fi', 'ru'
]
base_url = 'https://sepiasearch.org/api/v1/search/videos'

safesearch_table = {
    0: 'both',
    1: 'false',
    2: 'false'
}

time_range_table = {
    'day': relativedelta.relativedelta(),
    'week': relativedelta.relativedelta(weeks=-1),
    'month': relativedelta.relativedelta(months=-1),
    'year': relativedelta.relativedelta(years=-1)
}


embedded_url = '<iframe width="540" height="304" src="{url}" frameborder="0" allowfullscreen></iframe>'


def minute_to_hm(minute):
    if isinstance(minute, int):
        return "%d:%02d" % (divmod(minute, 60))
    return None


def request(query, params):
    params['url'] = base_url + '?' + urlencode({
        'search': query,
        'start': (params['pageno'] - 1) * 10,
        'count': 10,
        'sort': '-match',
        'nsfw': safesearch_table[params['safesearch']]
    })

    language = params['language'].split('-')[0]
    if language in supported_languages:
        params['url'] += '&languageOneOf[]=' + language
    if params['time_range'] in time_range_table:
        time = datetime.now().date() + time_range_table[params['time_range']]
        params['url'] += '&startDate=' + time.isoformat()

    return params


def response(resp):
    results = []

    search_results = loads(resp.text)

    if 'data' not in search_results:
        return []

    for result in search_results['data']:
        title = result['name']
        content = result['description']
        thumbnail = result['thumbnailUrl']
        publishedDate = parser.parse(result['publishedAt'])
        embedded = embedded_url.format(url=result.get('embedUrl'))
        author = result.get('account', {}).get('displayName')
        length = minute_to_hm(result.get('duration'))
        url = result['url']

        results.append({'url': url,
                        'title': title,
                        'content': content,
                        'author': author,
                        'length': length,
                        'template': 'videos.html',
                        'publishedDate': publishedDate,
                        'embedded': embedded,
                        'thumbnail': thumbnail})

    return results
