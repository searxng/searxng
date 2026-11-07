# SPDX-License-Identifier: AGPL-3.0-or-later
"""Simple implementation to store OSM keys and tags in a SQL database."""

__all__ = ["OSMKeysTagsDB"]

import typing as t
import json
import pathlib

from .core import get_cache, log

if t.TYPE_CHECKING:
    from searx.cache import CacheRowType


def _flatten_dict_keys(tag_name: list[str], tags: dict[str, t.Any]) -> dict[str, t.Any]:
    """E.g. flattens ``{"sports": {"soccer": {"*": {"en": "soccer", "de": "fußball"}}}}``
    into ``{"sports:soccer": {"en": "soccer", "de": "fußball"}}``.

    That makes it easier to store and lookup in a database, because it only requires a single key
    lookup to get the translations object and doesn't require loading the whole `sports` object.
    """
    flattened: dict[str, t.Any] = {}
    for key, value in tags.items():
        if key == "*":
            flattened[":".join(tag_name)] = value
        else:
            flattened |= _flatten_dict_keys(tag_name + [key], value)
    return flattened


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

        rows = [(k, v, None) for k, v in _flatten_dict_keys([], data_dict["keys"]).items()]
        log.debug(rows)
        self.cache.setmany(rows, ctx=self.ctx_keys)

        rows: "list[CacheRowType]" = []
        for category, entry in data_dict["tags"].items():
            for name, value in entry.items():
                rows.append((f"{category}:{name}", value, None))
        self.cache.setmany(rows, ctx=self.ctx_tags)

    def get_key_label(self, key: str) -> dict[str, str] | None:
        self.init()

        return self.cache.get(key=key, default=None, ctx=self.ctx_keys)

    def get_tag_label(self, category: str, label: str) -> dict[str, str] | None:
        self.init()

        return self.cache.get(key=f"{category}:{label}", default=None, ctx=self.ctx_keys)
