# SPDX-License-Identifier: AGPL-3.0-or-later
"""Calculate mathematical expressions using ack#eval
"""

from flask_babel import gettext

from searx.data import WIKIDATA_UNITS

name = "Unit converter plugin"
description = gettext("Convert between units")
default_on = True

CONVERT_KEYWORDS = ["in", "to", "as"]


def _convert(from_value, source_si_factor, target_si_factor):
    return from_value * source_si_factor / target_si_factor


def _parse_text_and_convert(search, splitted_query):
    if len(splitted_query) != 2 or splitted_query[0].strip() == "" or splitted_query[1].strip() == "":
        return

    from_value = ""
    from_unit_key = ""

    # only parse digits as value that belong together
    read_alpha = False
    for c in splitted_query[0]:
        if not read_alpha and (c in ("-", ".") or str.isdigit(c)):
            from_value += c
            read_alpha = True
        elif c != " ":
            from_unit_key += c

    to_unit_key = splitted_query[1].strip()

    from_unit = None
    to_unit = None

    for unit in WIKIDATA_UNITS.values():
        if unit['symbol'] == from_unit_key:
            from_unit = unit

        if unit['symbol'] == to_unit_key:
            to_unit = unit

        if from_unit and to_unit:
            break

    if from_unit is None or to_unit is None or to_unit.get('si_name') != from_unit.get('si_name'):
        return

    result = _convert(float(from_value), from_unit['to_si_factor'], to_unit['to_si_factor'])
    search.result_container.answers['conversion'] = {'answer': f"{result:g} {to_unit['symbol']}"}


def post_search(_request, search):
    # only convert between units on the first page
    if search.search_query.pageno > 1:
        return True

    query = search.search_query.query
    query_parts = query.split(" ")

    if len(query_parts) < 3:
        return True

    for query_part in query_parts:
        for keyword in CONVERT_KEYWORDS:
            if query_part == keyword:
                keyword_split = query.split(keyword, 1)
                _parse_text_and_convert(search, keyword_split)
                return True

    return True
