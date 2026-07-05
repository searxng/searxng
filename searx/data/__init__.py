# SPDX-License-Identifier: AGPL-3.0-or-later
"""This module holds the *data* created by::

make data.all

"""
# pylint: disable=invalid-name

__all__ = ["ahmia_blacklist_loader", "data_dir", "get_cache"]

import json
import typing as t

from .core import log, data_dir, get_cache
from .currencies import CurrenciesDB
from .tracker_patterns import TrackerPatternsDB


class UserAgentType(t.TypedDict):
    """Data structure of ``useragents.json``"""

    os: list[str]
    ua: str
    versions: list[str]


class WikiDataUnitType(t.TypedDict):
    """Data structure of an item in ``wikidata_units.json``"""

    si_name: str
    symbol: str
    to_si_factor: float


class LocalesType(t.TypedDict):
    """Data structure of an item in ``locales.json``"""

    LOCALE_NAMES: dict[str, str]
    RTL_LOCALES: list[str]


USER_AGENTS: UserAgentType
WIKIDATA_UNITS: dict[str, WikiDataUnitType]
TRACKER_PATTERNS: TrackerPatternsDB
LOCALES: LocalesType
CURRENCIES: CurrenciesDB

EXTERNAL_URLS: dict[str, dict[str, dict[str, str | dict[str, str]]]]
EXTERNAL_BANGS: dict[str, dict[str, t.Any]]
OSM_KEYS_TAGS: dict[str, dict[str, t.Any]]
ENGINE_DESCRIPTIONS: dict[str, dict[str, t.Any]]
ENGINE_TRAITS: dict[str, dict[str, t.Any]]


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


def __getattr__(name: str) -> t.Any:
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


def ahmia_blacklist_loader() -> list[str]:
    """Load data from `ahmia_blacklist.txt` and return a list of MD5 values of onion
    names.  The MD5 values are fetched by::

      searxng_extra/update/update_ahmia_blacklist.py

    This function is used by :py:mod:`searx.plugins.ahmia_filter`.

    """
    with open(data_dir / 'ahmia_blacklist.txt', encoding='utf-8') as f:
        return f.read().split()
