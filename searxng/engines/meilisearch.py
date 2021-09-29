# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
 Meilisearch
"""

# pylint: disable=global-statement

from json import loads, dumps


base_url = 'http://localhost:7700'
index = ''
auth_key = ''
facet_filters = []
_search_url = ''
result_template = 'key-value.html'
categories = ['general']
paging = True


def init(_):
    if index == '':
        raise ValueError('index cannot be empty')

    global _search_url
    _search_url = base_url + '/indexes/' + index + '/search'


def request(query, params):
    if auth_key != '':
        params['headers']['X-Meili-API-Key'] = auth_key

    params['headers']['Content-Type'] = 'application/json'
    params['url'] = _search_url
    params['method'] = 'POST'

    data = {
        'q': query,
        'offset': 10 * (params['pageno'] - 1),
        'limit': 10,
    }
    if len(facet_filters) > 0:
        data['facetFilters'] = facet_filters

    params['data'] = dumps(data)

    return params


def response(resp):
    results = []

    resp_json = loads(resp.text)
    for result in resp_json['hits']:
        r = {key: str(value) for key, value in result.items()}
        r['template'] = result_template
        results.append(r)

    return results
