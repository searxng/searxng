# SPDX-License-Identifier: AGPL-3.0-or-later
"""Simple implementation to store currencies data in a SQL database."""

__all__ = ["CurrenciesDB"]

import typing as t
import json
import pathlib

from .core import get_cache, log

if t.TYPE_CHECKING:
    from searx.cache import CacheRowType


@t.final
class CurrenciesDB:
    # pylint: disable=missing-class-docstring

    ctx_names: str = "data_currencies_names"
    ctx_iso4217: str = "data_currencies_iso4217"

    # Any ISO 4217 code present in currencies.json can be used as a sentinel to
    # detect a cache that is marked as loaded but contains no data.
    sentinel_iso4217: str = "USD"

    json_file: pathlib.Path = pathlib.Path(__file__).parent / "currencies.json"

    def __init__(self):
        self.cache = get_cache()

    def init(self):
        if self.cache.properties("currencies loaded") == "OK" and self._is_loaded():
            return
        # Load first: if loading fails, the property is not set and the next
        # call retries instead of leaving an empty cache marked as loaded.
        self.load()
        self.cache.properties.set("currencies loaded", "OK")
        # F I X M E:
        #     do we need a maintenance .. rember: database is stored
        #     in /tmp and will be rebuild during the reboot anyway

    def _is_loaded(self) -> bool:
        return bool(self.cache.get(key=self.sentinel_iso4217, default=None, ctx=self.ctx_iso4217))

    def load(self):
        log.debug("init searx.data.CURRENCIES")
        with open(self.json_file, encoding="utf-8") as f:
            data_dict: dict[str, dict[str, str]] = json.load(f)

        rows: "list[CacheRowType]" = [(k, v, None) for k, v in data_dict["names"].items()]
        self.cache.setmany(rows, ctx=self.ctx_names)
        rows = [(k, v, None) for k, v in data_dict["iso4217"].items()]
        self.cache.setmany(rows, ctx=self.ctx_iso4217)

    def name_to_iso4217(self, name: str) -> str | None:
        self.init()

        ret_val: str | list[str] | None = self.cache.get(key=name, default=None, ctx=self.ctx_names)
        if isinstance(ret_val, list):
            # if more alternatives, use the last in the list
            ret_val = ret_val[-1]
        return ret_val

    def iso4217_to_name(self, iso4217: str, language: str) -> str | None:
        self.init()

        iso4217_languages: dict[str, str] = self.cache.get(key=iso4217, default={}, ctx=self.ctx_iso4217)
        return iso4217_languages.get(language)

    def is_iso4217(self, iso4217: str) -> bool:
        self.init()

        item = self.cache.get(key=iso4217, default={}, ctx=self.ctx_iso4217)
        return bool(item)
