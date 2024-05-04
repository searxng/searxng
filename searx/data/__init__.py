# SPDX-License-Identifier: AGPL-3.0-or-later
"""This module holds the *data* created by::

  make data.all

"""

__all__ = [
    'ENGINE_TRAITS',
    'CURRENCIES',
    'USER_AGENTS',
    'EXTERNAL_URLS',
    'WIKIDATA_UNITS',
    'EXTERNAL_BANGS',
    'OSM_KEYS_TAGS',
    'LOCALES',
    'ahmia_blacklist_loader',
    'fetch_engine_descriptions',
]

import json
import sqlite3
from contextlib import contextmanager
from typing import Dict, Generator, List
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


def ahmia_blacklist_loader():
    """Load data from `ahmia_blacklist.txt` and return a list of MD5 values of onion
    names.  The MD5 values are fetched by::

      searxng_extra/update/update_ahmia_blacklist.py

    This function is used by :py:mod:`searx.plugins.ahmia_filter`.

    """
    with open(data_dir / 'ahmia_blacklist.txt', encoding='utf-8') as f:
        return f.read().split()


CURRENCIES = _load('currencies.json')
USER_AGENTS = _load('useragents.json')
EXTERNAL_URLS = _load('external_urls.json')
WIKIDATA_UNITS = _load('wikidata_units.json')
EXTERNAL_BANGS = _load('external_bangs.json')
OSM_KEYS_TAGS = _load('osm_keys_tags.json')
ENGINE_TRAITS = _load('engine_traits.json')
LOCALES = _load('locales.json')
