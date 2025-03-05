# SPDX-License-Identifier: AGPL-3.0-or-later
""".. sidebar:: info

   - :origin:`meilisearch.py <searx/engines/meilisearch.py>`
   - `MeiliSearch <https://www.meilisearch.com>`_
   - `MeiliSearch Documentation <https://docs.meilisearch.com/>`_
   - `Install MeiliSearch
     <https://docs.meilisearch.com/learn/getting_started/installation.html>`_

MeiliSearch_ is aimed at individuals and small companies.  It is designed for
small-scale (less than 10 million documents) data collections.  E.g. it is great
for storing web pages you have visited and searching in the contents later.

The engine supports faceted search, so you can search in a subset of documents
of the collection.  Furthermore, you can search in MeiliSearch_ instances that
require authentication by setting ``auth_token``.

Example
=======

Here is a simple example to query a Meilisearch instance:

.. code:: yaml

  - name: meilisearch
    engine: meilisearch
    shortcut: mes
    base_url: http://localhost:7700
    index: my-index
    enable_http: true

"""

# pylint: disable=global-statement

from json import dumps
from searx.result_types import EngineResults
from searx.extended_types import SXNG_Response

base_url = 'http://localhost:7700'
index = ''
auth_key = ''
facet_filters = []
_search_url = ''
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


def response(resp: SXNG_Response) -> EngineResults:
    res = EngineResults()

    resp_json = resp.json()
    for row in resp_json['hits']:
        kvmap = {key: str(value) for key, value in row.items()}
        res.add(res.types.KeyValue(kvmap=kvmap))

    return res
