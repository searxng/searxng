# SPDX-License-Identifier: AGPL-3.0-or-later
"""This module holds the *data* created by::

  make data.all

"""
from __future__ import annotations

__all__ = ["ahmia_blacklist_loader"]

import json
import typing

from .core import log, data_dir
from .currencies import CurrenciesDB
from .tracker_patterns import TrackerPatternsDB

CURRENCIES: CurrenciesDB
USER_AGENTS: dict[str, typing.Any]
EXTERNAL_URLS: dict[str, typing.Any]
WIKIDATA_UNITS: dict[str, typing.Any]
EXTERNAL_BANGS: dict[str, typing.Any]
OSM_KEYS_TAGS: dict[str, typing.Any]
ENGINE_DESCRIPTIONS: dict[str, typing.Any]
ENGINE_TRAITS: dict[str, typing.Any]
LOCALES: dict[str, typing.Any]
TRACKER_PATTERNS: TrackerPatternsDB

lazy_globals = {
    "CURRENCIES": CurrenciesDB(),
    "USER_AGENTS": None,
    "EXTERNAL_URLS": None,
    "WIKIDATA_UNITS": None,
    "EXTERNAL_BANGS": None,
    "OSM_KEYS_TAGS": None,
    "ENGINE_DESCRIPTIONS": None,
    "ENGINE_TRAITS": None,
    "LOCALES": None,
    "TRACKER_PATTERNS": TrackerPatternsDB(),
}

data_json_files = {
    "USER_AGENTS": "useragents.json",
    "EXTERNAL_URLS": "external_urls.json",
    "WIKIDATA_UNITS": "wikidata_units.json",
    "EXTERNAL_BANGS": "external_bangs.json",
    "OSM_KEYS_TAGS": "osm_keys_tags.json",
    "ENGINE_DESCRIPTIONS": "engine_descriptions.json",
    "ENGINE_TRAITS": "engine_traits.json",
    "LOCALES": "locales.json",
}


def __getattr__(name):
    # lazy init of the global objects
    if name not in lazy_globals:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    data = lazy_globals[name]
    if data is not None:
        return data

    log.debug("init searx.data.%s", name)

    with open(data_dir / data_json_files[name], encoding='utf-8') as f:
        lazy_globals[name] = json.load(f)

    return lazy_globals[name]


def ahmia_blacklist_loader():
    """Load data from `ahmia_blacklist.txt` and return a list of MD5 values of onion
    names.  The MD5 values are fetched by::

      searxng_extra/update/update_ahmia_blacklist.py

    This function is used by :py:mod:`searx.plugins.ahmia_filter`.

    """
    with open(data_dir / 'ahmia_blacklist.txt', encoding='utf-8') as f:
        return f.read().split()
