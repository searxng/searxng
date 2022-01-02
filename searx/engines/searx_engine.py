# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Searx (all)
"""

from json import loads
from searx.engines import categories as searx_categories

# about
about = {
    "website": 'https://github.com/searxng/searxng',
    "wikidata_id": 'Q17639196',
    "official_api_documentation": 'https://docs.searxng.org/dev/search_api.html',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

categories = searx_categories.keys()

# search-url
instance_urls = []
instance_index = 0


# do search-request
def request(query, params):
    global instance_index
    params['url'] = instance_urls[instance_index % len(instance_urls)]
    params['method'] = 'POST'

    instance_index += 1

    params['data'] = {
        'q': query,
        'pageno': params['pageno'],
        'language': params['language'],
        'time_range': params['time_range'],
        'category': params['category'],
        'format': 'json',
    }

    return params


# get response from search-request
def response(resp):

    response_json = loads(resp.text)
    results = response_json['results']

    for i in ('answers', 'infoboxes'):
        results.extend(response_json[i])

    results.extend({'suggestion': s} for s in response_json['suggestions'])

    results.append({'number_of_results': response_json['number_of_results']})

    return results
