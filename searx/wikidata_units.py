# SPDX-License-Identifier: AGPL-3.0-or-later
"""Unit conversion on the basis of `SPARQL/WIKIDATA Precision, Units and
Coordinates`_

.. _SPARQL/WIKIDATA Precision, Units and Coordinates:
   https://en.wikibooks.org/wiki/SPARQL/WIKIDATA_Precision,_Units_and_Coordinates#Quantities
"""

__all__ = ["convert_from_si", "convert_to_si", "symbol_to_si"]

import collections

from searx import data
from searx.engines import wikidata


class Beaufort:
    """The mapping of the Beaufort_ contains values from 0 to 16 (55.6 m/s),
    wind speeds greater than 200km/h (55.6 m/s) are given as 17 Bft. Thats why
    a value of 17 Bft cannot be converted to SI.

    .. hint::

       Negative values or values greater 16 Bft (55.6 m/s) will throw a
       :py:obj:`ValueError`.

    _Beaufort: https://en.wikipedia.org/wiki/Beaufort_scale
    """

    # fmt: off
    scale: list[float] = [
         0.2,  1.5,  3.3,  5.4,  7.9,
        10.7, 13.8, 17.1, 20.7, 24.4,
        28.4, 32.6, 32.7, 41.1, 45.8,
        50.8, 55.6
    ]
    # fmt: on

    @classmethod
    def from_si(cls, value) -> float:
        if value < 0 or value > 55.6:
            raise ValueError(f"invalid value {value} / the Beaufort scales from 0 to 16 (55.6 m/s)")
        bft = 0
        for bft, mps in enumerate(cls.scale):
            if mps >= value:
                break
        return bft

    @classmethod
    def to_si(cls, value) -> float:
        idx = round(value)
        if idx < 0 or idx > 16:
            raise ValueError(f"invalid value {value} / the Beaufort scales from 0 to 16 (55.6 m/s)")
        return cls.scale[idx]


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
    {
        "si_name": "Q182429",
        "symbol": "Bft",
        "to_si": Beaufort.to_si,
        "from_si": Beaufort.from_si,
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
    'Bft': ('bft',),
}
"""Alias symbols for known unit of measure symbols / by example::

    '°C': ('C', ...),  # list of alias symbols for °C (Q69362731)
    '°F': ('F', ...),  # list of alias symbols for °F (Q99490479)
    'mi': ('L',),      # list of alias symbols for mi (Q253276)
"""


SYMBOL_TO_SI = []
UNITS_BY_SI_NAME: dict = {}


def convert_from_si(si_name: str, symbol: str, value: float | int) -> float:
    from_si = units_by_si_name(si_name)[symbol][pos_from_si]
    if isinstance(from_si, (float, int)):
        value = float(value) * from_si
    else:
        value = from_si(float(value))
    return value


def convert_to_si(si_name: str, symbol: str, value: float | int) -> float:
    to_si = units_by_si_name(si_name)[symbol][pos_to_si]
    if isinstance(to_si, (float, int)):
        value = float(value) * to_si
    else:
        value = to_si(float(value))
    return value


def units_by_si_name(si_name):

    global UNITS_BY_SI_NAME  # pylint: disable=global-statement,global-variable-not-assigned
    if UNITS_BY_SI_NAME:
        return UNITS_BY_SI_NAME[si_name]

    # build the catalog ..
    for item in symbol_to_si():

        item_si_name = item[pos_si_name]
        item_symbol = item[pos_symbol]

        by_symbol = UNITS_BY_SI_NAME.get(item_si_name)
        if by_symbol is None:
            by_symbol = {}
            UNITS_BY_SI_NAME[item_si_name] = by_symbol
        by_symbol[item_symbol] = item

    return UNITS_BY_SI_NAME[si_name]


pos_symbol = 0  # (alias) symbol
pos_si_name = 1  # si_name
pos_from_si = 2  # from_si
pos_to_si = 3  # to_si
pos_symbol = 4  # standardized symbol


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


# the response contains duplicate ?item with the different ?symbol
# "ORDER BY ?item DESC(?rank) ?symbol" provides a deterministic result
# even if a ?item has different ?symbol of the same rank.
# A deterministic result
# see:
# * https://www.wikidata.org/wiki/Help:Ranking
# * https://www.mediawiki.org/wiki/Wikibase/Indexing/RDF_Dump_Format ("Statement representation" section)
# * https://w.wiki/32BT
# * https://en.wikibooks.org/wiki/SPARQL/WIKIDATA_Precision,_Units_and_Coordinates#Quantities
#   see the result for https://www.wikidata.org/wiki/Q11582
#   there are multiple symbols the same rank

SARQL_REQUEST = """
SELECT DISTINCT ?item ?symbol ?tosi ?tosiUnit
WHERE
{
  ?item wdt:P31/wdt:P279 wd:Q47574 .
  ?item p:P5061 ?symbolP .
  ?symbolP ps:P5061 ?symbol ;
           wikibase:rank ?rank .
  OPTIONAL {
    ?item p:P2370 ?tosistmt .
    ?tosistmt psv:P2370 ?tosinode .
    ?tosinode wikibase:quantityAmount ?tosi .
    ?tosinode wikibase:quantityUnit ?tosiUnit .
  }
  FILTER(LANG(?symbol) = "en").
}
ORDER BY ?item DESC(?rank) ?symbol
"""


def fetch_units():
    """Fetch units from Wikidata.  Function is used to update persistence of
    :py:obj:`searx.data.WIKIDATA_UNITS`."""

    results = collections.OrderedDict()
    response = wikidata.send_wikidata_query(SARQL_REQUEST)
    for unit in response['results']['bindings']:

        symbol = unit['symbol']['value']
        name = unit['item']['value'].rsplit('/', 1)[1]
        si_name = unit.get('tosiUnit', {}).get('value', '')
        if si_name:
            si_name = si_name.rsplit('/', 1)[1]

        to_si_factor = unit.get('tosi', {}).get('value', '')
        if name not in results:
            # ignore duplicate: always use the first one
            results[name] = {
                'symbol': symbol,
                'si_name': si_name if si_name else None,
                'to_si_factor': float(to_si_factor) if to_si_factor else None,
            }
    return results
