# SPDX-License-Identifier: AGPL-3.0-or-later
"""Simple implementation to store OSM keys and tags in a SQL database."""

__all__ = ["OSMKeysTagsDB"]

import typing as t
import json
import pathlib

from .core import get_cache, log

if t.TYPE_CHECKING:
    from searx.cache import CacheRowType


@t.final
class OSMKeysTagsDB:
    # pylint: disable=missing-class-docstring

    ctx_keys: str = "data_osm_keys"
    ctx_tags: str = "data_osm_tags"

    json_file: pathlib.Path = pathlib.Path(__file__).parent / "osm_keys_tags.json"

    def __init__(self):
        self.cache = get_cache()

    def init(self):
        if self.cache.properties("osm loaded") != "OK":
            # To avoid parallel initializations, the property is set first
            self.cache.properties.set("osm loaded", "OK")
            self.load()
        # F I X M E:
        #     do we need a maintenance .. rember: database is stored
        #     in /tmp and will be rebuild during the reboot anyway

    def load(self):
        log.debug("init searx.data.OSM_KEYS_TAGS")
        with open(self.json_file, encoding="utf-8") as f:
            data_dict: dict[str, dict[str, dict[str, t.Any]]] = json.load(f)

        rows: list["CacheRowType"] = [(k, v, None) for k, v in data_dict["keys"].items()]
        self.cache.setmany(rows, ctx=self.ctx_keys)

        rows = [(k, v, None) for k, v in data_dict["tags"].items()]
        self.cache.setmany(rows, ctx=self.ctx_tags)

    def get_key_label(self, key_name: str, lang: str) -> str | None:
        """Returns translated label of OSM key ``{category}={tag_name}``."""
        self.init()

        if key_name.startswith("currency:"):
            # currency:EUR --> get the name from the CURRENCIES variable
            # see https://wiki.openstreetmap.org/wiki/Key%3Acurrency
            # and for example https://taginfo.openstreetmap.org/keys/currency:EUR#values
            # but there is also currency=EUR (currently not handled)
            # https://taginfo.openstreetmap.org/keys/currency#values
            currency = key_name.split(':')
            if len(currency) > 1:
                # pylint: disable=import-outside-toplevel, cyclic-import
                from . import CURRENCIES

                if lang_iso4217 := CURRENCIES.iso4217_to_name(currency[1], lang):
                    return lang_iso4217
                return currency[1]

        labels: dict[str, str] = self.cache.get(  # type: ignore
            key=key_name,
            default={},
            ctx=self.ctx_keys,
        )
        return self.l10n(labels, lang)

    def get_tag_label(self, category: str, tag_name: str, lang: str) -> str | None:
        """Returns translated label of OSM tag ``{category}={tag_name}``."""
        self.init()

        labels: dict[str, str] = self.cache.get(  # type: ignore
            key=f"{category}={tag_name}",
            default={},
            ctx=self.ctx_tags,
        )
        return self.l10n(labels, lang)

    @staticmethod
    def l10n(labels: dict[str, str], lang: str) -> str | None:
        """Returns the string for the OSM label in the specified language."""

        # breakpoint()
        if label := labels.get(lang.lower()):
            return label
        # example: if 'zh-hk' is not found, check 'zh'
        if label := labels.get(lang.split("-")[0]):
            return label
        # example: if 'zh' is not found, check 'en'
        if label := labels.get("en"):
            return label
        # example: if still not found, use the first entry
        return (list(labels.values()) or [None])[0]
