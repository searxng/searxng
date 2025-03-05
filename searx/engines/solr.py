# SPDX-License-Identifier: AGPL-3.0-or-later
""".. sidebar:: info

   - :origin:`solr.py <searx/engines/solr.py>`
   - `Solr <https://solr.apache.org>`_
   - `Solr Resources <https://solr.apache.org/resources.html>`_
   - `Install Solr <https://solr.apache.org/guide/installing-solr.html>`_

Solr_ is a popular search engine based on Lucene, just like Elasticsearch_.  But
instead of searching in indices, you can search in collections.

Example
=======

This is an example configuration for searching in the collection
``my-collection`` and get the results in ascending order.

.. code:: yaml

  - name: solr
    engine: solr
    shortcut: slr
    base_url: http://localhost:8983
    collection: my-collection
    sort: asc
    enable_http: true

"""

# pylint: disable=global-statement

from urllib.parse import urlencode
from searx.exceptions import SearxEngineAPIException
from searx.result_types import EngineResults
from searx.extended_types import SXNG_Response


base_url = 'http://localhost:8983'
collection = ''
rows = 10
sort = ''  # sorting: asc or desc
field_list = 'name'  # list of field names to display on the UI
default_fields = ''  # default field to query
query_fields = ''  # query fields
_search_url = ''
paging = True


def init(_):
    if collection == '':
        raise ValueError('collection cannot be empty')

    global _search_url
    _search_url = base_url + '/solr/' + collection + '/select?{params}'


def request(query, params):
    query_params = {'q': query, 'rows': rows}
    if field_list != '':
        query_params['fl'] = field_list
    if query_fields != '':
        query_params['qf'] = query_fields
    if default_fields != '':
        query_params['df'] = default_fields
    if sort != '':
        query_params['sort'] = sort

    if 'pageno' in params:
        query_params['start'] = rows * (params['pageno'] - 1)

    params['url'] = _search_url.format(params=urlencode(query_params))

    return params


def response(resp: SXNG_Response) -> EngineResults:
    try:
        resp_json = resp.json()
    except Exception as e:
        raise SearxEngineAPIException("failed to parse response") from e

    if "error" in resp_json:
        raise SearxEngineAPIException(resp_json["error"]["msg"])

    res = EngineResults()

    for result in resp_json["response"]["docs"]:
        kvmap = {key: str(value) for key, value in result.items()}
        if not kvmap:
            continue
        res.add(res.types.KeyValue(kvmap=kvmap))

    return res
