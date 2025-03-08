# SPDX-License-Identifier: AGPL-3.0-or-later
"""A plugin for converting measured values from one unit to another unit (a
unit converter).

The plugin looks up the symbols (given in the query term) in a list of
converters, each converter is one item in the list (compare
:py:obj:`ADDITIONAL_UNITS`).  If the symbols are ambiguous, the matching units
of measurement are evaluated.  The weighting in the evaluation results from the
sorting of the :py:obj:`list of unit converters<symbol_to_si>`.

Enable in ``settings.yml``:

.. code:: yaml

  enabled_plugins:
    ..
    - 'Unit converter plugin'

"""

from __future__ import annotations
import re
import babel.numbers

from flask_babel import gettext, get_locale

from searx import data
from searx.result_types import EngineResults


name = "Unit converter plugin"
description = gettext("Convert between units")
default_on = True

plugin_id = "unit_converter"
preference_section = "general"

CONVERT_KEYWORDS = ["in", "to", "as"]

# inspired from https://stackoverflow.com/a/42475086
RE_MEASURE = r'''
(?P<sign>[-+]?)         # +/- or nothing for positive
(\s*)                   # separator: white space or nothing
(?P<number>[\d\.,]*)    # number: 1,000.00 (en) or 1.000,00 (de)
(?P<E>[eE][-+]?\d+)?    # scientific notation: e(+/-)2 (*10^2)
(\s*)                   # separator: white space or nothing
(?P<unit>\S+)           # unit of measure
'''


ADDITIONAL_UNITS = [
    {
        "si_name": "Q11579",
        "symbol": "°C",
        "to_si": lambda val: val + 273.15,
        "from_si": lambda val: val - 273.15,
    },
    {
        "si_name": "Q11579",
        "symbol": "°F",
        "to_si": lambda val: (val + 459.67) * 5 / 9,
        "from_si": lambda val: (val * 9 / 5) - 459.67,
    },
]
"""Additional items to convert from a measure unit to a SI unit (vice versa).

.. code:: python

    {
        "si_name": "Q11579",                 # Wikidata item ID of the SI unit (Kelvin)
        "symbol": "°C",                      # symbol of the measure unit
        "to_si": lambda val: val + 273.15,   # convert measure value (val) to SI unit
        "from_si": lambda val: val - 273.15, # convert SI value (val) measure unit
    },
    {
        "si_name": "Q11573",
        "symbol": "mi",
        "to_si": 1609.344,                   # convert measure value (val) to SI unit
        "from_si": 1 / 1609.344              # convert SI value (val) measure unit
    },

The values of ``to_si`` and ``from_si`` can be of :py:obj:`float` (a multiplier)
or a callable_ (val in / converted value returned).

.. _callable: https://docs.python.org/3/glossary.html#term-callable
"""


ALIAS_SYMBOLS = {
    '°C': ('C',),
    '°F': ('F',),
    'mi': ('L',),
}
"""Alias symbols for known unit of measure symbols / by example::

    '°C': ('C', ...),  # list of alias symbols for °C (Q69362731)
    '°F': ('F', ...),  # list of alias symbols for °F (Q99490479)
    'mi': ('L',),      # list of alias symbols for mi (Q253276)
"""


SYMBOL_TO_SI = []


def symbol_to_si():
    """Generates a list of tuples, each tuple is a measure unit and the fields
    in the tuple are:

    0. Symbol of the measure unit (e.g. 'mi' for measure unit 'miles' Q253276)

    1. SI name of the measure unit (e.g. Q11573 for SI unit 'metre')

    2. Factor to get SI value from measure unit (e.g. 1mi is equal to SI 1m
       multiplied by 1609.344)

    3. Factor to get measure value from from SI value (e.g. SI 100m is equal to
       100mi divided by 1609.344)

    The returned list is sorted, the first items are created from
    ``WIKIDATA_UNITS``, the second group of items is build from
    :py:obj:`ADDITIONAL_UNITS` and items created from :py:obj:`ALIAS_SYMBOLS`.

    If you search this list for a symbol, then a match with a symbol from
    Wikidata has the highest weighting (first hit in the list), followed by the
    symbols from the :py:obj:`ADDITIONAL_UNITS` and the lowest weighting is
    given to the symbols resulting from the aliases :py:obj:`ALIAS_SYMBOLS`.

    """

    global SYMBOL_TO_SI  # pylint: disable=global-statement
    if SYMBOL_TO_SI:
        return SYMBOL_TO_SI

    # filter out units which can't be normalized to a SI unit and filter out
    # units without a symbol / arcsecond does not have a symbol
    # https://www.wikidata.org/wiki/Q829073

    for item in data.WIKIDATA_UNITS.values():
        if item['to_si_factor'] and item['symbol']:
            SYMBOL_TO_SI.append(
                (
                    item['symbol'],
                    item['si_name'],
                    1 / item['to_si_factor'],  # from_si
                    item['to_si_factor'],  # to_si
                    item['symbol'],
                )
            )

    for item in ADDITIONAL_UNITS:
        SYMBOL_TO_SI.append(
            (
                item['symbol'],
                item['si_name'],
                item['from_si'],
                item['to_si'],
                item['symbol'],
            )
        )

    alias_items = []
    for item in SYMBOL_TO_SI:
        for alias in ALIAS_SYMBOLS.get(item[0], ()):
            alias_items.append(
                (
                    alias,
                    item[1],
                    item[2],  # from_si
                    item[3],  # to_si
                    item[0],  # origin unit
                )
            )
    SYMBOL_TO_SI = SYMBOL_TO_SI + alias_items
    return SYMBOL_TO_SI


def _parse_text_and_convert(from_query, to_query) -> str | None:

    # pylint: disable=too-many-branches, too-many-locals

    if not (from_query and to_query):
        return None

    measured = re.match(RE_MEASURE, from_query, re.VERBOSE)
    if not (measured and measured.group('number'), measured.group('unit')):
        return None

    # Symbols are not unique, if there are several hits for the from-unit, then
    # the correct one must be determined by comparing it with the to-unit
    # https://github.com/searxng/searxng/pull/3378#issuecomment-2080974863

    # first: collecting possible units

    source_list, target_list = [], []

    for symbol, si_name, from_si, to_si, orig_symbol in symbol_to_si():

        if symbol == measured.group('unit'):
            source_list.append((si_name, to_si))
        if symbol == to_query:
            target_list.append((si_name, from_si, orig_symbol))

    if not (source_list and target_list):
        return None

    source_to_si = target_from_si = target_symbol = None

    # second: find the right unit by comparing list of from-units with list of to-units

    for source in source_list:
        for target in target_list:
            if source[0] == target[0]:  # compare si_name
                source_to_si = source[1]
                target_from_si = target[1]
                target_symbol = target[2]

    if not (source_to_si and target_from_si):
        return None

    _locale = get_locale() or 'en_US'

    value = measured.group('sign') + measured.group('number') + (measured.group('E') or '')
    value = babel.numbers.parse_decimal(value, locale=_locale)

    # convert value to SI unit

    if isinstance(source_to_si, (float, int)):
        value = float(value) * source_to_si
    else:
        value = source_to_si(float(value))

    # convert value from SI unit to target unit

    if isinstance(target_from_si, (float, int)):
        value = float(value) * target_from_si
    else:
        value = target_from_si(float(value))

    if measured.group('E'):
        # when incoming notation is scientific, outgoing notation is scientific
        result = babel.numbers.format_scientific(value, locale=_locale)
    else:
        result = babel.numbers.format_decimal(value, locale=_locale, format='#,##0.##########;-#')

    return f'{result} {target_symbol}'


def post_search(_request, search) -> EngineResults:
    results = EngineResults()

    # only convert between units on the first page
    if search.search_query.pageno > 1:
        return results

    query = search.search_query.query
    query_parts = query.split(" ")

    if len(query_parts) < 3:
        return results

    for query_part in query_parts:
        for keyword in CONVERT_KEYWORDS:
            if query_part == keyword:
                from_query, to_query = query.split(keyword, 1)
                target_val = _parse_text_and_convert(from_query.strip(), to_query.strip())
                if target_val:
                    results.add(results.types.Answer(answer=target_val))

    return results
