# SPDX-License-Identifier: AGPL-3.0-or-later
"""Within this module we implement a *demo offline engine*.  Do not look to
close to the implementation, its just a simple example.  To get in use of this
*demo* engine add the following entry to your engines list in ``settings.yml``:

.. code:: yaml

  - name: my offline engine
    engine: demo_offline
    shortcut: demo
    disabled: false

"""

import json

from searx.result_types import EngineResults
from searx.enginelib import EngineCache

engine_type = 'offline'
categories = ['general']
disabled = True
timeout = 2.0

about = {
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

# if there is a need for globals, use a leading underline
_my_offline_engine: str = ""

CACHE: EngineCache
"""Persistent (SQLite) key/value cache that deletes its values after ``expire``
seconds."""


def init(engine_settings):
    """Initialization of the (offline) engine.  The origin of this demo engine is a
    simple json string which is loaded in this example while the engine is
    initialized."""
    global _my_offline_engine, CACHE  # pylint: disable=global-statement

    CACHE = EngineCache(engine_settings["name"])  # type:ignore

    _my_offline_engine = (
        '[ {"value": "%s"}'
        ', {"value":"first item"}'
        ', {"value":"second item"}'
        ', {"value":"third item"}'
        ']' % engine_settings.get('name')
    )


def search(query, request_params) -> EngineResults:
    """Query (offline) engine and return results.  Assemble the list of results
    from your local engine.  In this demo engine we ignore the 'query' term,
    usual you would pass the 'query' term to your local engine to filter out the
    results.
    """
    res = EngineResults()
    count = CACHE.get("count", 0)

    for row in json.loads(_my_offline_engine):
        count += 1
        kvmap = {
            'query': query,
            'language': request_params['searxng_locale'],
            'value': row.get("value"),
        }
        res.add(
            res.types.KeyValue(
                caption=f"Demo Offline Engine Result #{count}",
                key_title="Name",
                value_title="Value",
                kvmap=kvmap,
            )
        )
    res.add(res.types.LegacyResult(number_of_results=count))

    # cache counter value for 20sec
    CACHE.set("count", count, expire=20)
    return res
