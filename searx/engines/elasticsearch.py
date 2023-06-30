# SPDX-License-Identifier: AGPL-3.0-or-later
""".. sidebar:: info

   - :origin:`elasticsearch.py <searx/engines/elasticsearch.py>`
   - `Elasticsearch <https://www.elastic.co/elasticsearch/>`_
   - `Elasticsearch Guide
     <https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html>`_
   - `Install Elasticsearch
     <https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html>`_

Elasticsearch_ supports numerous ways to query the data it is storing.  At the
moment the engine supports the most popular search methods (``query_type``):

- ``match``,
- ``simple_query_string``,
- ``term`` and
- ``terms``.

If none of the methods fit your use case, you can select ``custom`` query type
and provide the JSON payload to submit to Elasticsearch in
``custom_query_json``.

Example
=======

The following is an example configuration for an Elasticsearch_ instance with
authentication configured to read from ``my-index`` index.

.. code:: yaml

  - name: elasticsearch
    shortcut: es
    engine: elasticsearch
    base_url: http://localhost:9200
    username: elastic
    password: changeme
    index: my-index
    query_type: match
    # custom_query_json: '{ ... }'
    enable_http: true

"""

from json import loads, dumps
from searx.exceptions import SearxEngineAPIException


base_url = 'http://localhost:9200'
username = ''
password = ''
index = ''
search_url = base_url + '/' + index + '/_search'
query_type = 'match'
custom_query_json = {}
show_metadata = False
categories = ['general']


def init(engine_settings):
    if 'query_type' in engine_settings and engine_settings['query_type'] not in _available_query_types:
        raise ValueError('unsupported query type', engine_settings['query_type'])

    if index == '':
        raise ValueError('index cannot be empty')


def request(query, params):
    if query_type not in _available_query_types:
        return params

    if username and password:
        params['auth'] = (username, password)

    params['url'] = search_url
    params['method'] = 'GET'
    params['data'] = dumps(_available_query_types[query_type](query))
    params['headers']['Content-Type'] = 'application/json'

    return params


def _match_query(query):
    """
    The standard for full text queries.
    searx format: "key:value" e.g. city:berlin
    REF: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-match-query.html
    """

    try:
        key, value = query.split(':')
    except Exception as e:
        raise ValueError('query format must be "key:value"') from e

    return {"query": {"match": {key: {'query': value}}}}


def _simple_query_string_query(query):
    """
    Accepts query strings, but it is less strict than query_string
    The field used can be specified in index.query.default_field in Elasticsearch.
    REF: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-simple-query-string-query.html
    """

    return {'query': {'simple_query_string': {'query': query}}}


def _term_query(query):
    """
    Accepts one term and the name of the field.
    searx format: "key:value" e.g. city:berlin
    REF: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-term-query.html
    """

    try:
        key, value = query.split(':')
    except Exception as e:
        raise ValueError('query format must be key:value') from e

    return {'query': {'term': {key: value}}}


def _terms_query(query):
    """
    Accepts multiple terms and the name of the field.
    searx format: "key:value1,value2" e.g. city:berlin,paris
    REF: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-terms-query.html
    """

    try:
        key, values = query.split(':')
    except Exception as e:
        raise ValueError('query format must be key:value1,value2') from e

    return {'query': {'terms': {key: values.split(',')}}}


def _custom_query(query):
    key, value = query.split(':')
    custom_query = custom_query_json
    for query_key, query_value in custom_query.items():
        if query_key == '{{KEY}}':
            custom_query[key] = custom_query.pop(query_key)
        if query_value == '{{VALUE}}':
            custom_query[query_key] = value
    return custom_query


def response(resp):
    results = []

    resp_json = loads(resp.text)
    if 'error' in resp_json:
        raise SearxEngineAPIException(resp_json['error'])

    for result in resp_json['hits']['hits']:
        r = {key: str(value) if not key.startswith('_') else value for key, value in result['_source'].items()}
        r['template'] = 'key-value.html'

        if show_metadata:
            r['metadata'] = {'index': result['_index'], 'id': result['_id'], 'score': result['_score']}

        results.append(r)

    return results


_available_query_types = {
    # Full text queries
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/full-text-queries.html
    'match': _match_query,
    'simple_query_string': _simple_query_string_query,
    # Term-level queries
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/term-level-queries.html
    'term': _term_query,
    'terms': _terms_query,
    # Query JSON defined by the instance administrator.
    'custom': _custom_query,
}
