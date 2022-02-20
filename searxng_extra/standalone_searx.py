#!/usr/bin/env python
# lint: pylint

# SPDX-License-Identifier: AGPL-3.0-or-later
# (C) Copyright Contributors to the SearXNG project.
# (C) Copyright Contributors to the searx project (2014 - 2021)

"""Script to run SearXNG from terminal.

Getting categories without initiate the engine will only return `['general']`

>>> import searx.engines
... list(searx.engines.categories.keys())
['general']
>>> import searx.search
... searx.search.initialize()
... list(searx.engines.categories.keys())
['general', 'it', 'science', 'images', 'news', 'videos', 'music', 'files', 'social media', 'map']

Example to use this script:

.. code::  bash

    $ python3 searxng_extra/standalone_searx.py rain

.. danger::

   Be warned, using the ``standalone_searx.py`` won't give you privacy!

   On the contrary, this script behaves like a SearXNG server: your IP is
   exposed and tracked by all active engines (google, bing, qwant, ... ), with
   every query!

Example to run it from python:

>>> import importlib
... import json
... import sys
... import searx.engines
... import searx.search
... search_query = 'rain'
... # initialize engines
... searx.search.initialize()
... # load engines categories once instead of each time the function called
... engine_cs = list(searx.engines.categories.keys())
... # load module
... spec = importlib.util.spec_from_file_location(
...     'utils.standalone_searx', 'searxng_extra/standalone_searx.py')
... sas = importlib.util.module_from_spec(spec)
... spec.loader.exec_module(sas)
... # use function from module
... prog_args = sas.parse_argument([search_query], category_choices=engine_cs)
... search_q = sas.get_search_query(prog_args, engine_categories=engine_cs)
... res_dict = sas.to_dict(search_q)
... sys.stdout.write(json.dumps(
...     res_dict, sort_keys=True, indent=4, ensure_ascii=False,
...     default=sas.json_serial))
{
    "answers": [],
    "infoboxes": [ {...} ],
    "paging": true,
    "results": [... ],
    "results_number": 820000000.0,
    "search": {
        "lang": "all",
        "pageno": 1,
        "q": "rain",
        "safesearch": 0,
        "timerange": null
    },
    "suggestions": [...]
}

"""  # pylint: disable=line-too-long

import argparse
import sys
from datetime import datetime
from json import dumps
from typing import Any, Dict, List, Optional

import searx
import searx.preferences
import searx.query
import searx.search
import searx.webadapter

EngineCategoriesVar = Optional[List[str]]


def get_search_query(
    args: argparse.Namespace, engine_categories: EngineCategoriesVar = None
) -> searx.search.SearchQuery:
    """Get  search results for the query"""
    if engine_categories is None:
        engine_categories = list(searx.engines.categories.keys())
    try:
        category = args.category.decode('utf-8')
    except AttributeError:
        category = args.category
    form = {
        "q": args.query,
        "categories": category,
        "pageno": str(args.pageno),
        "language": args.lang,
        "time_range": args.timerange,
    }
    preferences = searx.preferences.Preferences(['simple'], engine_categories, searx.engines.engines, [])
    preferences.key_value_settings['safesearch'].parse(args.safesearch)

    search_query = searx.webadapter.get_search_query_from_webapp(preferences, form)[0]
    return search_query


def no_parsed_url(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove parsed url from dict."""
    for result in results:
        del result['parsed_url']
    return results


def json_serial(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default json code.

    :raise TypeError: raised when **obj** is not serializable
    """
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    if isinstance(obj, bytes):
        return obj.decode('utf8')
    if isinstance(obj, set):
        return list(obj)
    raise TypeError("Type ({}) not serializable".format(type(obj)))


def to_dict(search_query: searx.search.SearchQuery) -> Dict[str, Any]:
    """Get result from parsed arguments."""
    result_container = searx.search.Search(search_query).search()
    result_container_json = {
        "search": {
            "q": search_query.query,
            "pageno": search_query.pageno,
            "lang": search_query.lang,
            "safesearch": search_query.safesearch,
            "timerange": search_query.time_range,
        },
        "results": no_parsed_url(result_container.get_ordered_results()),
        "infoboxes": result_container.infoboxes,
        "suggestions": list(result_container.suggestions),
        "answers": list(result_container.answers),
        "paging": result_container.paging,
        "results_number": result_container.results_number(),
    }
    return result_container_json


def parse_argument(
    args: Optional[List[str]] = None, category_choices: EngineCategoriesVar = None
) -> argparse.Namespace:
    """Parse command line.

    :raise SystemExit: Query argument required on `args`

    Examples:

    >>> import importlib
    ... # load module
    ... spec = importlib.util.spec_from_file_location(
    ...     'utils.standalone_searx', 'utils/standalone_searx.py')
    ... sas = importlib.util.module_from_spec(spec)
    ... spec.loader.exec_module(sas)
    ... sas.parse_argument()
    usage: ptipython [-h] [--category [{general}]] [--lang [LANG]] [--pageno [PAGENO]] [--safesearch [{0,1,2}]] [--timerange [{day,week,month,year}]]
                     query
    SystemExit: 2
    >>> sas.parse_argument(['rain'])
    Namespace(category='general', lang='all', pageno=1, query='rain', safesearch='0', timerange=None)
    """  # noqa: E501
    if not category_choices:
        category_choices = list(searx.engines.categories.keys())
    parser = argparse.ArgumentParser(description='Standalone searx.')
    parser.add_argument('query', type=str, help='Text query')
    parser.add_argument(
        '--category', type=str, nargs='?', choices=category_choices, default='general', help='Search category'
    )
    parser.add_argument('--lang', type=str, nargs='?', default='all', help='Search language')
    parser.add_argument('--pageno', type=int, nargs='?', default=1, help='Page number starting from 1')
    parser.add_argument(
        '--safesearch',
        type=str,
        nargs='?',
        choices=['0', '1', '2'],
        default='0',
        help='Safe content filter from none to strict',
    )
    parser.add_argument(
        '--timerange', type=str, nargs='?', choices=['day', 'week', 'month', 'year'], help='Filter by time range'
    )
    return parser.parse_args(args)


if __name__ == '__main__':
    settings_engines = searx.settings['engines']
    searx.search.load_engines(settings_engines)
    engine_cs = list(searx.engines.categories.keys())
    prog_args = parse_argument(category_choices=engine_cs)
    searx.search.initialize_network(settings_engines, searx.settings['outgoing'])
    searx.search.check_network_configuration()
    searx.search.initialize_metrics([engine['name'] for engine in settings_engines])
    searx.search.initialize_processors(settings_engines)
    search_q = get_search_query(prog_args, engine_categories=engine_cs)
    res_dict = to_dict(search_q)
    sys.stdout.write(dumps(res_dict, sort_keys=True, indent=4, ensure_ascii=False, default=json_serial))
