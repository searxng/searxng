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

    json_file: pathlib.Path = pathlib.Path(__file__).parent / "currencies.json"

    def __init__(self):
        self.cache = get_cache()

    def init(self):
        if self.cache.properties("currencies loaded") != "OK":
            # To avoid parallel initializations, the property is set first
            self.cache.properties.set("currencies loaded", "OK")
            self.load()
        # F I X M E:
        #     do we need a maintenance .. rember: database is stored
        #     in /tmp and will be rebuild during the reboot anyway

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
        item = self.cache.get(key=iso4217, default={}, ctx=self.ctx_iso4217)
        return bool(item)
