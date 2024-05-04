#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fetch currencies from :origin:`searx/engines/wikidata.py` engine.

Output file: :origin:`searx/data/currencies.json` (:origin:`CI Update data ...
<.github/workflows/data-update.yml>`).

"""

# pylint: disable=invalid-name

import csv
import re
import unicodedata
import sqlite3
from pathlib import Path

from searx.network import set_timeout_for_thread
from searx.locales import LOCALE_NAMES, locales_initialize
from searx.engines import wikidata, set_loggers
from searx.data import data_dir

DATABASE_FILE = data_dir / 'currencies.db'
CSV_FILE = data_dir / 'dumps' / 'currencies.csv'


set_loggers(wikidata, 'wikidata')
locales_initialize()

# ORDER BY (with all the query fields) is important to keep a deterministic result order
# so multiple invocation of this script doesn't change currencies.json
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
# so multiple invocation of this script doesn't change currencies.json
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


def add_entry(db, language, iso4217, name, normalize_name=True):
    if normalize_name:
        name = _normalize_name(name)

    entry = (language, iso4217, name)
    db.add(entry)


def wikidata_request_result_iterator(request):
    set_timeout_for_thread(60)
    result = wikidata.send_wikidata_query(request.replace('%LANGUAGES_SPARQL%', LANGUAGES_SPARQL))
    if result is not None:
        yield from result['results']['bindings']


def fetch_db():
    db = set()

    for r in wikidata_request_result_iterator(SPARQL_WIKIPEDIA_NAMES_REQUEST):
        iso4217 = r['iso4217']['value']
        article_name = r['article_name']['value']
        article_lang = r['article_name']['xml:lang']
        add_entry(db, article_lang, iso4217, article_name)

    for r in wikidata_request_result_iterator(SARQL_REQUEST):
        iso4217 = r['iso4217']['value']
        if 'label' in r:
            label = r['label']['value']
            label_lang = r['label']['xml:lang']
            add_entry(db, label_lang, iso4217, label)

        if 'alias' in r:
            add_entry(db, "", iso4217, r['alias']['value'])

        if 'unicode' in r:
            add_entry(db, "", iso4217, r['unicode']['value'], normalize_name=False)

        if 'unit' in r:
            add_entry(db, "", iso4217, r['unit']['value'], normalize_name=False)

    return db


def main():

    db = fetch_db()

    # static
    add_entry(db, "", 'EUR', "euro")
    add_entry(db, "", 'EUR', "euros")
    add_entry(db, "", 'USD', "dollar")
    add_entry(db, "", 'USD', "dollars")
    add_entry(
        db,
        "",
        'MXN',
        "peso",
    )
    add_entry(db, "", 'MXN', "pesos")

    db = list(db)
    db.sort(key=lambda entry: (entry[0], entry[1], entry[2]))
    Path(DATABASE_FILE).unlink(missing_ok=True)
    with sqlite3.connect(DATABASE_FILE) as con:
        cur = con.cursor()
        cur.execute("CREATE TABLE currencies(language, iso4217, name)")
        cur.executemany("INSERT INTO currencies VALUES(?, ?, ?)", db)
        cur.execute("CREATE INDEX index_currencies_iso4217 ON currencies('iso4217')")
        cur.execute("CREATE INDEX index_currencies_name ON currencies('name')")
        con.commit()
    with CSV_FILE.open('w', encoding='utf8') as f:
        w = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        w.writerow(["language", "iso4217", "name"])
        for row in db:
            w.writerow(row)


if __name__ == '__main__':
    main()
