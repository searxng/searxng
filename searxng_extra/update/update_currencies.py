#!/usr/bin/env python
# lint: pylint
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Fetch currencies from :origin:`searx/engines/wikidata.py` engine.

Output file: :origin:`searx/data/currencies.json` (:origin:`CI Update data ...
<.github/workflows/data-update.yml>`).

"""

# pylint: disable=invalid-name

import re
import unicodedata
import json

# set path
from os.path import join

from searx import searx_dir
from searx.locales import LOCALE_NAMES
from searx.engines import wikidata, set_loggers

set_loggers(wikidata, 'wikidata')

# ORDER BY (with all the query fields) is important to keep a deterministic result order
# so multiple invokation of this script doesn't change currencies.json
SARQL_REQUEST = """
SELECT DISTINCT ?iso4217 ?unit ?unicode ?label ?alias WHERE {
  ?item wdt:P498 ?iso4217; rdfs:label ?label.
  OPTIONAL { ?item skos:altLabel ?alias FILTER (LANG (?alias) = LANG(?label)). }
  OPTIONAL { ?item wdt:P5061 ?unit. }
  OPTIONAL { ?item wdt:P489 ?symbol.
             ?symbol wdt:P487 ?unicode. }
  MINUS { ?item wdt:P582 ?end_data . }                  # Ignore monney with an end date
  MINUS { ?item wdt:P31/wdt:P279* wd:Q15893266 . }      # Ignore "former entity" (obsolete currency)
  FILTER(LANG(?label) IN (%LANGUAGES_SPARQL%)).
}
ORDER BY ?iso4217 ?unit ?unicode ?label ?alias
"""

# ORDER BY (with all the query fields) is important to keep a deterministic result order
# so multiple invokation of this script doesn't change currencies.json
SPARQL_WIKIPEDIA_NAMES_REQUEST = """
SELECT DISTINCT ?iso4217 ?article_name WHERE {
  ?item wdt:P498 ?iso4217 .
  ?article schema:about ?item ;
           schema:name ?article_name ;
           schema:isPartOf [ wikibase:wikiGroup "wikipedia" ]
  MINUS { ?item wdt:P582 ?end_data . }                  # Ignore monney with an end date
  MINUS { ?item wdt:P31/wdt:P279* wd:Q15893266 . }      # Ignore "former entity" (obsolete currency)
  FILTER(LANG(?article_name) IN (%LANGUAGES_SPARQL%)).
}
ORDER BY ?iso4217 ?article_name
"""


LANGUAGES = LOCALE_NAMES.keys()
LANGUAGES_SPARQL = ', '.join(set(map(lambda l: repr(l.split('_')[0]), LANGUAGES)))


def remove_accents(name):
    return unicodedata.normalize('NFKD', name).lower()


def remove_extra(name):
    for c in ('(', ':'):
        if c in name:
            name = name.split(c)[0].strip()
    return name


def _normalize_name(name):
    name = re.sub(' +', ' ', remove_accents(name.lower()).replace('-', ' '))
    name = remove_extra(name)
    return name


def add_currency_name(db, name, iso4217, normalize_name=True):
    db_names = db['names']

    if normalize_name:
        name = _normalize_name(name)

    iso4217_set = db_names.setdefault(name, [])
    if iso4217 not in iso4217_set:
        iso4217_set.insert(0, iso4217)


def add_currency_label(db, label, iso4217, language):
    labels = db['iso4217'].setdefault(iso4217, {})
    labels[language] = label


def wikidata_request_result_iterator(request):
    result = wikidata.send_wikidata_query(request.replace('%LANGUAGES_SPARQL%', LANGUAGES_SPARQL))
    if result is not None:
        for r in result['results']['bindings']:
            yield r


def fetch_db():
    db = {
        'names': {},
        'iso4217': {},
    }

    for r in wikidata_request_result_iterator(SPARQL_WIKIPEDIA_NAMES_REQUEST):
        iso4217 = r['iso4217']['value']
        article_name = r['article_name']['value']
        article_lang = r['article_name']['xml:lang']
        add_currency_name(db, article_name, iso4217)
        add_currency_label(db, article_name, iso4217, article_lang)

    for r in wikidata_request_result_iterator(SARQL_REQUEST):
        iso4217 = r['iso4217']['value']
        if 'label' in r:
            label = r['label']['value']
            label_lang = r['label']['xml:lang']
            add_currency_name(db, label, iso4217)
            add_currency_label(db, label, iso4217, label_lang)

        if 'alias' in r:
            add_currency_name(db, r['alias']['value'], iso4217)

        if 'unicode' in r:
            add_currency_name(db, r['unicode']['value'], iso4217, normalize_name=False)

        if 'unit' in r:
            add_currency_name(db, r['unit']['value'], iso4217, normalize_name=False)

    # reduce memory usage:
    # replace lists with one item by the item.
    # see searx.search.processors.online_currency.name_to_iso4217
    for name in db['names']:
        if len(db['names'][name]) == 1:
            db['names'][name] = db['names'][name][0]

    return db


def get_filename():
    return join(join(searx_dir, "data"), "currencies.json")


def main():
    #
    db = fetch_db()
    # static
    add_currency_name(db, "euro", 'EUR')
    add_currency_name(db, "euros", 'EUR')
    add_currency_name(db, "dollar", 'USD')
    add_currency_name(db, "dollars", 'USD')
    add_currency_name(db, "peso", 'MXN')
    add_currency_name(db, "pesos", 'MXN')

    with open(get_filename(), 'w', encoding='utf8') as f:
        json.dump(db, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
