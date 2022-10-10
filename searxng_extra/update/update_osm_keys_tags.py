#!/usr/bin/env python
# lint: pylint
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fetch OSM keys and tags.

To get the i18n names, the scripts uses `Wikidata Query Service`_ instead of for
example `OSM tags API`_ (sidenote: the actual change log from
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

import json
import collections
from pathlib import Path

from searx import searx_dir
from searx.network import set_timeout_for_thread
from searx.engines import wikidata, set_loggers
from searx.sxng_locales import sxng_locales
from searx.engines.openstreetmap import get_key_rank, VALUE_TO_LINK

set_loggers(wikidata, 'wikidata')


SPARQL_TAGS_REQUEST = """
SELECT ?tag ?item ?itemLabel WHERE {
  ?item wdt:P1282 ?tag .
  ?item rdfs:label ?itemLabel .
  FILTER(STRSTARTS(?tag, 'Tag'))
}
GROUP BY ?tag ?item ?itemLabel
ORDER BY ?tag ?item ?itemLabel
"""

SPARQL_KEYS_REQUEST = """
SELECT ?key ?item ?itemLabel WHERE {
  ?item wdt:P1282 ?key .
  ?item rdfs:label ?itemLabel .
  FILTER(STRSTARTS(?key, 'Key'))
}
GROUP BY ?key ?item ?itemLabel
ORDER BY ?key ?item ?itemLabel
"""

LANGUAGES = [l[0].lower() for l in sxng_locales]

PRESET_KEYS = {
    ('wikidata',): {'en': 'Wikidata'},
    ('wikipedia',): {'en': 'Wikipedia'},
    ('email',): {'en': 'Email'},
    ('facebook',): {'en': 'Facebook'},
    ('fax',): {'en': 'Fax'},
    ('internet_access', 'ssid'): {'en': 'Wi-Fi'},
}

INCLUDED_KEYS = {('addr',)}


def get_preset_keys():
    results = collections.OrderedDict()
    for keys, value in PRESET_KEYS.items():
        r = results
        for k in keys:
            r = r.setdefault(k, {})
        r.setdefault('*', value)
    return results


def get_keys():
    results = get_preset_keys()
    response = wikidata.send_wikidata_query(SPARQL_KEYS_REQUEST)

    for key in response['results']['bindings']:
        keys = key['key']['value'].split(':')[1:]
        if keys[0] == 'currency' and len(keys) > 1:
            # special case in openstreetmap.py
            continue
        if keys[0] == 'contact' and len(keys) > 1:
            # label for the key "contact.email" is "Email"
            # whatever the language
            r = results.setdefault('contact', {})
            r[keys[1]] = {'*': {'en': keys[1]}}
            continue
        if tuple(keys) in PRESET_KEYS:
            # skip presets (already set above)
            continue
        if (
            get_key_rank(':'.join(keys)) is None
            and ':'.join(keys) not in VALUE_TO_LINK
            and tuple(keys) not in INCLUDED_KEYS
        ):
            # keep only keys that will be displayed by openstreetmap.py
            continue
        label = key['itemLabel']['value'].lower()
        lang = key['itemLabel']['xml:lang']
        r = results
        for k in keys:
            r = r.setdefault(k, {})
        r = r.setdefault('*', {})
        if lang in LANGUAGES:
            r.setdefault(lang, label)

    # special cases
    results['delivery']['covid19']['*'].clear()
    for k, v in results['delivery']['*'].items():
        results['delivery']['covid19']['*'][k] = v + ' (COVID19)'

    results['opening_hours']['covid19']['*'].clear()
    for k, v in results['opening_hours']['*'].items():
        results['opening_hours']['covid19']['*'][k] = v + ' (COVID19)'

    return results


def get_tags():
    results = collections.OrderedDict()
    response = wikidata.send_wikidata_query(SPARQL_TAGS_REQUEST)
    for tag in response['results']['bindings']:
        tag_names = tag['tag']['value'].split(':')[1].split('=')
        if len(tag_names) == 2:
            tag_category, tag_type = tag_names
        else:
            tag_category, tag_type = tag_names[0], ''
        label = tag['itemLabel']['value'].lower()
        lang = tag['itemLabel']['xml:lang']
        if lang in LANGUAGES:
            results.setdefault(tag_category, {}).setdefault(tag_type, {}).setdefault(lang, label)
    return results


def optimize_data_lang(translations):
    language_to_delete = []
    # remove "zh-hk" entry if the value is the same as "zh"
    # same for "en-ca" / "en" etc...
    for language in translations:
        if '-' in language:
            base_language = language.split('-')[0]
            if translations.get(base_language) == translations.get(language):
                language_to_delete.append(language)

    for language in language_to_delete:
        del translations[language]
    language_to_delete = []

    # remove entries that have the same value than the "en" entry
    value_en = translations.get('en')
    if value_en:
        for language, value in translations.items():
            if language != 'en' and value == value_en:
                language_to_delete.append(language)

    for language in language_to_delete:
        del translations[language]


def optimize_tags(data):
    for v in data.values():
        for translations in v.values():
            optimize_data_lang(translations)
    return data


def optimize_keys(data):
    for k, v in data.items():
        if k == '*':
            optimize_data_lang(v)
        elif isinstance(v, dict):
            optimize_keys(v)
    return data


def get_osm_tags_filename():
    return Path(searx_dir) / "data" / "osm_keys_tags.json"


if __name__ == '__main__':

    set_timeout_for_thread(60)
    result = {
        'keys': optimize_keys(get_keys()),
        'tags': optimize_tags(get_tags()),
    }
    with open(get_osm_tags_filename(), 'w', encoding="utf8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False, sort_keys=True)
