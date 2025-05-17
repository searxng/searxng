# SPDX-License-Identifier: AGPL-3.0-or-later
"""Valkey is an open source (BSD licensed), in-memory data structure (key value
based) store.  Before configuring the ``valkey_server`` engine, you must install
the dependency valkey_.

Configuration
=============

Select a database to search in and set its index in the option ``db``.  You can
either look for exact matches or use partial keywords to find what you are
looking for by configuring ``exact_match_only``.

Example
=======

Below is an example configuration:

.. code:: yaml

  # Required dependency: valkey

  - name: myvalkey
    shortcut : rds
    engine: valkey_server
    exact_match_only: false
    host: '127.0.0.1'
    port: 6379
    enable_http: true
    password: ''
    db: 0

Implementations
===============

"""

import valkey  # pylint: disable=import-error

from searx.result_types import EngineResults

engine_type = 'offline'

# valkey connection variables
host = '127.0.0.1'
port = 6379
password = ''
db = 0

# engine specific variables
paging = False
exact_match_only = True

_valkey_client = None


def init(_engine_settings):
    global _valkey_client  # pylint: disable=global-statement
    _valkey_client = valkey.StrictValkey(
        host=host,
        port=port,
        db=db,
        password=password or None,
        decode_responses=True,
    )


def search(query, _params) -> EngineResults:
    res = EngineResults()

    if not exact_match_only:
        for kvmap in search_keys(query):
            res.add(res.types.KeyValue(kvmap=kvmap))
        return res

    kvmap: dict[str, str] = _valkey_client.hgetall(query)
    if kvmap:
        res.add(res.types.KeyValue(kvmap=kvmap))
    elif " " in query:
        qset, rest = query.split(" ", 1)
        for row in _valkey_client.hscan_iter(qset, match='*{}*'.format(rest)):
            res.add(res.types.KeyValue(kvmap={row[0]: row[1]}))
    return res


def search_keys(query) -> list[dict]:
    ret = []
    for key in _valkey_client.scan_iter(match='*{}*'.format(query)):
        key_type = _valkey_client.type(key)
        res = None

        if key_type == 'hash':
            res = _valkey_client.hgetall(key)
        elif key_type == 'list':
            res = dict(enumerate(_valkey_client.lrange(key, 0, -1)))

        if res:
            res['valkey_key'] = key
            ret.append(res)
    return ret
