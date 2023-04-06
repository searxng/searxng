# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
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
    'ahmia_blacklist_loader',
]

import json
from pathlib import Path

data_dir = Path(__file__).parent


def _load(filename):
    with open(data_dir / filename, encoding='utf-8') as f:
        return json.load(f)


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
ENGINE_DESCRIPTIONS = _load('engine_descriptions.json')
ENGINE_TRAITS = _load('engine_traits.json')
