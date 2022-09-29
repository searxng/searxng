# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
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
_my_offline_engine = None


def init(engine_settings=None):
    """Initialization of the (offline) engine.  The origin of this demo engine is a
    simple json string which is loaded in this example while the engine is
    initialized.

    """
    global _my_offline_engine  # pylint: disable=global-statement

    _my_offline_engine = (
        '[ {"value": "%s"}'
        ', {"value":"first item"}'
        ', {"value":"second item"}'
        ', {"value":"third item"}'
        ']' % engine_settings.get('name')
    )


def search(query, request_params):
    """Query (offline) engine and return results.  Assemble the list of results from
    your local engine.  In this demo engine we ignore the 'query' term, usual
    you would pass the 'query' term to your local engine to filter out the
    results.

    """
    ret_val = []

    result_list = json.loads(_my_offline_engine)

    for row in result_list:
        entry = {
            'query': query,
            'language': request_params['searxng_locale'],
            'value': row.get("value"),
            # choose a result template or comment out to use the *default*
            'template': 'key-value.html',
        }
        ret_val.append(entry)

    return ret_val
