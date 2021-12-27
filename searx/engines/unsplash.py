# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Unsplash

"""

from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl
from json import loads

# about
about = {
    "website": 'https://unsplash.com',
    "wikidata_id": 'Q28233552',
    "official_api_documentation": 'https://unsplash.com/developers',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

base_url = 'https://unsplash.com/'
search_url = base_url + 'napi/search/photos?'
categories = ['images']
page_size = 20
paging = True


def clean_url(url):
    parsed = urlparse(url)
    query = [(k, v) for (k, v) in parse_qsl(parsed.query) if k not in ['ixid', 's']]

    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(query), parsed.fragment))


def request(query, params):
    params['url'] = search_url + urlencode({'query': query, 'page': params['pageno'], 'per_page': page_size})
    logger.debug("query_url --> %s", params['url'])
    return params


def response(resp):
    results = []
    json_data = loads(resp.text)

    if 'results' in json_data:
        for result in json_data['results']:
            results.append(
                {
                    'template': 'images.html',
                    'url': clean_url(result['links']['html']),
                    'thumbnail_src': clean_url(result['urls']['thumb']),
                    'img_src': clean_url(result['urls']['raw']),
                    'title': result.get('alt_description') or 'unknown',
                    'content': result.get('description') or '',
                }
            )

    return results
