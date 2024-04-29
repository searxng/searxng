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
    'ENGINE_DESCRIPTIONS',
    'LOCALES',
    'ahmia_blacklist_loader',
]

import json
from pathlib import Path
from searx import logger

data_dir = Path(__file__).parent
logger = logger.getChild('data')

CURRENCIES: dict
USER_AGENTS: dict
EXTERNAL_URLS: dict
WIKIDATA_UNITS: dict
EXTERNAL_BANGS: dict
OSM_KEYS_TAGS: dict
ENGINE_DESCRIPTIONS: dict
ENGINE_TRAITS: dict
LOCALES: dict


def ahmia_blacklist_loader():
    """Load data from `ahmia_blacklist.txt` and return a list of MD5 values of onion
    names.  The MD5 values are fetched by::

      searxng_extra/update/update_ahmia_blacklist.py

    This function is used by :py:mod:`searx.plugins.ahmia_filter`.

    """
    with open(data_dir / 'ahmia_blacklist.txt', encoding='utf-8') as f:
        return f.read().split()


NAME_TO_JSON_FILE = {
    'CURRENCIES': 'currencies.json',
    'USER_AGENTS': 'useragents.json',
    'EXTERNAL_URLS': 'external_urls.json',
    'WIKIDATA_UNITS': 'wikidata_units.json',
    'EXTERNAL_BANGS': 'external_bangs.json',
    'OSM_KEYS_TAGS': 'osm_keys_tags.json',
    'ENGINE_DESCRIPTIONS': 'engine_descriptions.json',
    'ENGINE_TRAITS': 'engine_traits.json',
    'LOCALES': 'locales.json',
}


def __getattr__(name: str):
    # lazy load of JSON files ..
    filename = NAME_TO_JSON_FILE.get(name)
    if filename:
        filename = data_dir / filename
        logger.debug("init global %s from JSON file %s", name, filename)
        with open(filename, encoding='utf-8') as f:
            globals()[name] = json.load(f)
            return globals()[name]
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
