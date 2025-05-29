# SPDX-License-Identifier: AGPL-3.0-or-later
"""A plugin for converting measured values from one unit to another unit (a
unit converter).

The plugin looks up the symbols (given in the query term) in a list of
converters, each converter is one item in the list (compare
:py:obj:`ADDITIONAL_UNITS`).  If the symbols are ambiguous, the matching units
of measurement are evaluated.  The weighting in the evaluation results from the
sorting of the :py:obj:`list of unit converters<symbol_to_si>`.
"""
from __future__ import annotations
import typing
import re
import babel.numbers

from flask_babel import gettext, get_locale

from searx.wikidata_units import symbol_to_si
from searx.plugins import Plugin, PluginInfo
from searx.result_types import EngineResults

if typing.TYPE_CHECKING:
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request
    from searx.plugins import PluginCfg


name = ""
description = gettext("")

plugin_id = ""
preference_section = ""

CONVERT_KEYWORDS = ["in", "to", "as"]


class SXNGPlugin(Plugin):
    """Convert between units.  The result is displayed in area for the
    "answers".
    """

    id = "unit_converter"

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)

        self.info = PluginInfo(
            id=self.id,
            name=gettext("Unit converter plugin"),
            description=gettext("Convert between units"),
            preference_section="general",
        )

    def post_search(self, request: "SXNG_Request", search: "SearchWithPlugins") -> EngineResults:
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


# inspired from https://stackoverflow.com/a/42475086
RE_MEASURE = r'''
(?P<sign>[-+]?)         # +/- or nothing for positive
(\s*)                   # separator: white space or nothing
(?P<number>[\d\.,]*)    # number: 1,000.00 (en) or 1.000,00 (de)
(?P<E>[eE][-+]?\d+)?    # scientific notation: e(+/-)2 (*10^2)
(\s*)                   # separator: white space or nothing
(?P<unit>\S+)           # unit of measure
'''


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
