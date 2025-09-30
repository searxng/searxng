#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Script to run Zhensa from terminal.

  DON'T USE THIS SCRIPT!!

.. danger::

   Be warned, using the ``standalone_zhensa.py`` won't give you privacy!

   On the contrary, this script behaves like a Zhensa server: your IP is
   exposed and tracked by all active engines (google, bing, qwant, ... ), with
   every query!

.. note::

   This is an old and grumpy hack / Zhensa is a Flask application with
   client/server structure, which can't be turned into a command line tool the
   way it was done here.

Getting categories without initiate the engine will only return `['general']`

>>> import zhensa.engines
... list(zhensa.engines.categories.keys())
['general']
>>> import zhensa.search
... zhensa.search.initialize()
... list(zhensa.engines.categories.keys())
['general', 'it', 'science', 'images', 'news', 'videos', 'music', 'files', 'social media', 'map']

Example to use this script:

.. code::  bash

    $ python3 zhensa_extra/standalone_zhensa.py rain

"""  # pylint: disable=line-too-long

import argparse
import sys
from datetime import datetime
from json import dumps
from typing import Any, Dict, List, Optional

import zhensa
import zhensa.preferences
import zhensa.query
import zhensa.search
import zhensa.search.models
import zhensa.webadapter
from zhensa.search.processors import PROCESSORS

EngineCategoriesVar = Optional[List[str]]


def get_search_query(
    args: argparse.Namespace, engine_categories: EngineCategoriesVar = None
) -> zhensa.search.models.SearchQuery:
    """Get  search results for the query"""
    if engine_categories is None:
        engine_categories = list(zhensa.engines.categories.keys())
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
    preferences = zhensa.preferences.Preferences(['simple'], engine_categories, zhensa.engines.engines, [])
    preferences.key_value_settings['safesearch'].parse(args.safesearch)

    search_query = zhensa.webadapter.get_search_query_from_webapp(preferences, form)[0]
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


def to_dict(search_query: zhensa.search.models.SearchQuery) -> Dict[str, Any]:
    """Get result from parsed arguments."""
    result_container = zhensa.search.Search(search_query).search()
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
        "number_of_results": result_container.number_of_results,
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
    ...     'utils.standalone_zhensa', 'utils/standalone_zhensa.py')
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
        category_choices = list(zhensa.engines.categories.keys())
    parser = argparse.ArgumentParser(description='Standalone zhensa.')
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
    settings_engines = zhensa.settings['engines']
    zhensa.search.load_engines(settings_engines)
    engine_cs = list(zhensa.engines.categories.keys())
    prog_args = parse_argument(category_choices=engine_cs)
    zhensa.search.initialize_network(settings_engines, zhensa.settings['outgoing'])
    zhensa.search.check_network_configuration()
    zhensa.search.initialize_metrics([engine['name'] for engine in settings_engines])
    PROCESSORS.init(settings_engines)
    search_q = get_search_query(prog_args, engine_categories=engine_cs)
    res_dict = to_dict(search_q)
    sys.stdout.write(dumps(res_dict, sort_keys=True, indent=4, ensure_ascii=False, default=json_serial))
