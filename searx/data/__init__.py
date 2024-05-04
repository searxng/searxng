# SPDX-License-Identifier: AGPL-3.0-or-later
"""This module holds the *data* created by::

  make data.all

"""

__all__ = [
    'ENGINE_TRAITS',
    'USER_AGENTS',
    'EXTERNAL_URLS',
    'WIKIDATA_UNITS',
    'EXTERNAL_BANGS',
    'LOCALES',
    'ahmia_blacklist_loader',
    'fetch_engine_descriptions',
    'fetch_iso4217_from_user',
    'fetch_name_from_iso4217',
    'fetch_osm_key_label',
]

import re
import unicodedata
import json
import sqlite3
from contextlib import contextmanager
from typing import Dict, Generator, List, Optional
from functools import lru_cache
from pathlib import Path


data_dir = Path(__file__).parent
data_connection_local = {}


def _load(filename):
    with open(data_dir / filename, encoding='utf-8') as f:
        return json.load(f)


@contextmanager
def sql_connection(filename: str) -> Generator[sqlite3.Connection, None, None]:
    """Return a read only SQLite connection to filename.
    The filename is relative to searx/data

    Multiple calls to this function in the same thread,
    already return the same connection.
    """
    dict_id = filename
    connection = data_connection_local.get(dict_id)
    if connection is None:
        data_filename = str(data_dir / filename)
        # open database in read only mode and allow to share between threads
        # https://www.sqlite.org/faq.html#q6
        # see https://ricardoanderegg.com/posts/python-sqlite-thread-safety/
        # and https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety
        #     sqlite3.threadsafety is hard coded to 1
        # the only reliable way to check if multithreading is supported is to run this query
        # SELECT * FROM pragma_compile_options WHERE compile_options LIKE 'THREADSAFE=%'
        # but THREADSAFE=1 on Linux anyway
        data_connection = sqlite3.connect(f'file:{data_filename}?mode=ro', uri=True, check_same_thread=False)
        # 512KB of cache instead of 2MB (512KB / 4KB = 128, 4KB is the default page size)
        # https://www.sqlite.org/pragma.html#pragma_cache_size
        data_connection.execute("PRAGMA cache_size = 128;")
        data_connection_local[dict_id] = data_connection
    yield data_connection


def fetch_engine_descriptions(language) -> Dict[str, List[str]]:
    """Return engine description and source for each engine name."""
    with sql_connection("engine_descriptions.db") as conn:
        res = conn.execute("SELECT engine, description, source FROM engine_descriptions WHERE language=?", (language,))
        return {result[0]: [result[1], result[2]] for result in res.fetchall()}


def _normalize_name(name):
    name = name.lower().replace('-', ' ').rstrip('s')
    name = re.sub(' +', ' ', name)
    return unicodedata.normalize('NFKD', name).lower()


@lru_cache(10)
def fetch_iso4217_from_user(name: str) -> Optional[str]:
    with sql_connection("currencies.db") as connection:
        # try the iso4217
        res = connection.execute("SELECT iso4217 FROM currencies WHERE lower(iso4217)=? LIMIT 1", (name.lower(),))
        result = res.fetchone()
        if result:
            return result[0]

        # try the currency names
        name = _normalize_name(name)
        res = connection.execute("SELECT iso4217 FROM currencies WHERE name=?", (name,))
        result = list(set(result[0] for result in res.fetchall()))
        if len(result) == 1:
            return result[0]

        # ambiguity --> return nothing
        return None


@lru_cache(10)
def fetch_name_from_iso4217(iso4217: str, language: str) -> Optional[str]:
    with sql_connection("currencies.db") as connection:
        res = connection.execute("SELECT name FROM currencies WHERE iso4217=? AND language=?", (iso4217, language))
        result = [result[0] for result in res.fetchall()]
        if len(result) == 1:
            return result[0]
        return None


@lru_cache(100)
def fetch_osm_key_label(key_name: str, language: str) -> Optional[str]:
    if key_name.startswith('currency:'):
        # currency:EUR --> get the name from the CURRENCIES variable
        # see https://wiki.openstreetmap.org/wiki/Key%3Acurrency
        # and for example https://taginfo.openstreetmap.org/keys/currency:EUR#values
        # but there is also currency=EUR (currently not handled)
        # https://taginfo.openstreetmap.org/keys/currency#values
        currency = key_name.split(':')
        if len(currency) > 1:
            label = fetch_name_from_iso4217(currency[1], language)
            if label:
                return label
            return currency[1]

    language = language.lower()
    language_short = language.split('-')[0]
    with sql_connection("osm_keys_tags.db") as conn:
        res = conn.execute(
            "SELECT language, label FROM osm_keys WHERE name=? AND language in (?, ?, 'en')",
            (key_name, language, language_short),
        )
        result = {result[0]: result[1] for result in res.fetchall()}
        return result.get(language) or result.get(language_short) or result.get('en')


@lru_cache(100)
def fetch_osm_tag_label(tag_key: str, tag_value: str, language: str) -> Optional[str]:
    language = language.lower()
    language_short = language.split('-')[0]
    with sql_connection("osm_keys_tags.db") as conn:
        res = conn.execute(
            "SELECT language, label FROM osm_tags WHERE tag_key=? AND tag_value=? AND language in (?, ?, 'en')",
            (tag_key, tag_value, language, language_short),
        )
        result = {result[0]: result[1] for result in res.fetchall()}
        return result.get(language) or result.get(language_short) or result.get('en')


def ahmia_blacklist_loader():
    """Load data from `ahmia_blacklist.txt` and return a list of MD5 values of onion
    names.  The MD5 values are fetched by::

      searxng_extra/update/update_ahmia_blacklist.py

    This function is used by :py:mod:`searx.plugins.ahmia_filter`.

    """
    with open(data_dir / 'ahmia_blacklist.txt', encoding='utf-8') as f:
        return f.read().split()


USER_AGENTS = _load('useragents.json')
EXTERNAL_URLS = _load('external_urls.json')
WIKIDATA_UNITS = _load('wikidata_units.json')
EXTERNAL_BANGS = _load('external_bangs.json')
ENGINE_TRAITS = _load('engine_traits.json')
LOCALES = _load('locales.json')
