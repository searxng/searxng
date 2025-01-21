# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tavily AI Engine
"""

from json import dumps
from datetime import datetime
from searx.exceptions import SearxEngineAPIException

# about
about = {
    "website": 'https://tavily.com/',
    "wikidata_id": None,
    "official_api_documentation": 'https://docs.tavily.com/docs/rest-api/api-reference',
    "use_official_api": True,
    "require_api_key": True,
    "results": 'JSON',
}

search_url = 'https://api.tavily.com/search'
paging = False
time_range_support = True

search_type = 'search'  # possible values: search, news
api_key = 'unset'
max_results = 20
search_depth = 'basic'  # The depth of the search. It can be "basic" or "advanced".
include_images = False  # Include query-related images. Turns answer into infobox with first image.
include_domains = []  # A list of domains to specifically include in the search results.
exclude_domains = []  # A list of domains to specifically exclude from the search results.


def request(query, params):
    if api_key == 'unset':
        raise SearxEngineAPIException('missing Tavily API key')

    data = {
        'query': query,
        'api_key': api_key,
        'search_depth': 'basic',
        'time_range': params["time_range"],
        'max_results': max_results,
        'include_images': include_images,
        'include_domains': include_domains,
        'exclude_domains': exclude_domains,
    }
    if search_type == 'search':
        data['include_answer'] = True
    elif search_type == 'news':
        data['topic'] = 'news'
    else:
        raise ValueError(f"Invalid search type {search_type}")

    params['url'] = search_url
    params['method'] = 'POST'
    params['headers']['content-type'] = 'application/json'
    params['data'] = dumps(data)
    return params


def response(resp):
    results = []
    json_resp = resp.json()

    for result in json_resp.get('results', []):
        results.append(
            {
                'title': result['title'],
                'url': result['url'],
                'content': result['content'],
                'publishedDate': _parse_date(result.get('published_date')),
            }
        )

    if json_resp['images']:
        results.append({'infobox': 'Tavily', 'img_src': json_resp['images'][0], 'content': json_resp['answer']})
    elif json_resp['answer']:
        results.append({'answer': json_resp['answer']})

    return results


def _parse_date(pubDate):
    if pubDate is not None:
        try:
            return datetime.strptime(pubDate, '%a, %d %b %Y %H:%M:%S %Z')
        except (ValueError, TypeError) as e:
            logger.debug("ignore exception (publishedDate): %s", e)
    return None
