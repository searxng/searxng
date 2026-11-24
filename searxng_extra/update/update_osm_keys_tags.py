#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fetch OSM keys and tags.

To get the i18n names, the scripts uses `Wikidata Query Service`_ instead of for
example `OSM tags API`_ (side note: the actual change log from
map.atownsend.org.uk_ might be useful to normalize OSM tags).

Output file: :origin:`searx/data/osm_keys_tags` (:origin:`CI Update data ...
<.github/workflows/data-update.yml>`).

.. _Wikidata Query Service: https://query.wikidata.org/
.. _OSM tags API: https://taginfo.openstreetmap.org/taginfo/apidoc
.. _map.atownsend.org.uk: https://map.atownsend.org.uk/maps/map/changelog.html

:py:obj:`SPARQL_TAGS_REQUEST` :
    Wikidata SPARQL query that returns *type-categories* and *types*.  The
    returned tag is ``Tag:{category}={type}`` (see :py:func:`get_tags`).
    Example:

    - https://taginfo.openstreetmap.org/tags/building=house#overview
    - https://wiki.openstreetmap.org/wiki/Tag:building%3Dhouse
      at the bottom of the infobox (right side), there is a link to wikidata:
      https://www.wikidata.org/wiki/Q3947
      see property "OpenStreetMap tag or key" (P1282)
    - https://wiki.openstreetmap.org/wiki/Tag%3Abuilding%3Dbungalow
      https://www.wikidata.org/wiki/Q850107

:py:obj:`SPARQL_KEYS_REQUEST` :
    Wikidata SPARQL query that returns *keys*.  Example with "payment":

    - https://wiki.openstreetmap.org/wiki/Key%3Apayment
      at the bottom of infobox (right side), there is a link to wikidata:
      https://www.wikidata.org/wiki/Q1148747
      link made using the "OpenStreetMap tag or key" property (P1282)
      to be confirm: there is a one wiki page per key ?
    - https://taginfo.openstreetmap.org/keys/payment#values
    - https://taginfo.openstreetmap.org/keys/payment:cash#values

    ``rdfs:label`` get all the labels without language selection
    (as opposed to SERVICE ``wikibase:label``).

"""

import time
from itertools import groupby
import json
import collections

from searx.network import set_timeout_for_thread
from searx.engines import wikidata, set_loggers
from searx.sxng_locales import sxng_locales
from searx.data import data_dir
from searx.wikidata import send_wikidata_query

DATA_FILE = data_dir / 'osm_keys_tags.json'

set_loggers(wikidata, 'wikidata')


SPARQL_TAGS_REQUEST = """
SELECT DISTINCT ?tag ?item ?itemLabel ?language
WHERE {
  ?item wdt:P1282 ?tag .
  ?item rdfs:label ?itemLabel .

  BIND(LANG(?itemLabel) AS ?language)
}
ORDER BY ?tag ?language
"""

SPARQL_KEYS_REQUEST = """
SELECT DISTINCT ?key ?item ?itemLabel ?language
WHERE {
  ?item wdt:P13786 ?key .
  ?item rdfs:label ?itemLabel .

  BIND(LANG(?itemLabel) AS ?language)
}
ORDER BY ?key LANG(?itemLabel)
"""

LANGUAGES = [l[0].lower() for l in sxng_locales]
"""Language codes supported by SearXNG."""

PRESET_KEYS = {
    "wikidata": {"en": "Wikidata"},
    "wikipedia": {"en": "Wikipedia"},
    "email": {"en": "Email"},
    "facebook": {"en": "Facebook"},
    "fax": {"en": "Fax"},
    "ssid": {"en": "Wi-Fi"},
    "internet_access": {"en": "Wi-Fi"},
}
"""Additional keys that are missing in Wikidata."""


def get_keys():
    start = time.perf_counter()
    print("sending Wikidata query: SPARQL_KEYS_REQUEST .. can take up to 5min!")
    response = send_wikidata_query(SPARQL_KEYS_REQUEST, timeout=300)
    print(f"  duration: {time.perf_counter() - start:.2f} sec")

    results = collections.OrderedDict(PRESET_KEYS)
    for key, entries in groupby(response["results"]["bindings"], key=lambda b: b["key"]["value"]):
        results[key] = {
            e["language"]["value"]: e["itemLabel"]["value"] for e in entries if e["language"]["value"] in LANGUAGES
        }
    return results


def get_tags() -> dict[str, str]:
    start = time.perf_counter()
    print("sending Wikidata query: SPARQL_TAGS_REQUEST .. can take up to 5min!")
    response = send_wikidata_query(SPARQL_TAGS_REQUEST, timeout=300)
    print(f"  duration: {time.perf_counter() - start:.2f} sec")
    results = collections.OrderedDict()
    for key, entries in groupby(response["results"]["bindings"], key=lambda b: b["tag"]["value"]):
        results[key] = {
            e["language"]["value"]: e["itemLabel"]["value"] for e in entries if e["language"]["value"] in LANGUAGES
        }
    return results


if __name__ == '__main__':
    set_timeout_for_thread(60)
    result = {
        'keys': get_keys(),
        'tags': get_tags(),
    }
    with DATA_FILE.open('w', encoding="utf8") as f:
        json.dump(result, f, indent=4, sort_keys=True, ensure_ascii=False)
