# SPDX-License-Identifier: AGPL-3.0-or-later
"""MongoDB_ is a document based database program that handles JSON like data.
Before configuring the ``mongodb`` engine, you must install the dependency
pymongo_.

Configuration
=============

In order to query MongoDB_, you have to select a ``database`` and a
``collection``.  Furthermore, you have to select a ``key`` that is going to be
searched.  MongoDB_ also supports the option ``exact_match_only``, so configure
it as you wish.

Example
=======

Below is an example configuration for using a MongoDB collection:

.. code:: yaml

  # MongoDB engine
  # Required dependency: pymongo

  - name: mymongo
    engine: mongodb
    shortcut: md
    exact_match_only: false
    host: '127.0.0.1'
    port: 27017
    enable_http: true
    results_per_page: 20
    database: 'business'
    collection: 'reviews'  # name of the db collection
    key: 'name'            # key in the collection to search for

Implementations
===============

"""

import re

try:
    from pymongo import MongoClient  # type: ignore
except ImportError:
    # import error is ignored because the admin has to install pymongo manually
    # to use the engine
    pass

from zhensa.result_types import EngineResults


engine_type = 'offline'

# mongodb connection variables
host = '127.0.0.1'
port = 27017
username = ''
password = ''
database = None
collection = None
key = None

# engine specific variables
paging = True
results_per_page = 20
exact_match_only = False

_client = None


def init(_):
    connect()


def connect():
    global _client  # pylint: disable=global-statement
    kwargs: dict[str, str | int] = {'port': port}
    if username:
        kwargs['username'] = username
    if password:
        kwargs['password'] = password
    _client = MongoClient(host, **kwargs)[database][collection]


def search(query, params) -> EngineResults:
    res = EngineResults()
    if exact_match_only:
        q = {'$eq': query}
    else:
        _re = re.compile('.*{0}.*'.format(re.escape(query)), re.I | re.M)
        q = {'$regex': _re}

    query = _client.find({key: q}).skip((params['pageno'] - 1) * results_per_page).limit(results_per_page)

    res.add(res.types.LegacyResult(number_of_results=query.count()))
    for row in query:
        del row['_id']
        kvmap = {str(k): str(v) for k, v in row.items()}
        res.add(res.types.KeyValue(kvmap=kvmap))

    return res
