# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

import typing as t
from hashlib import md5

from flask_babel import gettext  # pyright: ignore[reportUnknownVariableType]

from zhensa.data import ahmia_blacklist_loader
from zhensa import get_setting
from zhensa.plugins import Plugin, PluginInfo

if t.TYPE_CHECKING:
    import flask
    from zhensa.search import SearchWithPlugins
    from zhensa.extended_types import SXNG_Request
    from zhensa.result_types import Result
    from zhensa.plugins import PluginCfg

ahmia_blacklist: list[str] = []


@t.final
class SXNGPlugin(Plugin):
    """Filter out onion results that appear in Ahmia's blacklist (See https://ahmia.fi/blacklist)."""

    id = "ahmia_filter"

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)
        self.info = PluginInfo(
            id=self.id,
            name=gettext("Ahmia blacklist"),
            description=gettext("Filter out onion results that appear in Ahmia's blacklist."),
            preference_section="general",
        )

    def on_result(
        self, request: "SXNG_Request", search: "SearchWithPlugins", result: "Result"
    ) -> bool:  # pylint: disable=unused-argument
        if not getattr(result, "is_onion", False) or not getattr(result, "parsed_url", False):
            return True
        result_hash = md5(result["parsed_url"].hostname.encode()).hexdigest()
        return result_hash not in ahmia_blacklist

    def init(self, app: "flask.Flask") -> bool:  # pylint: disable=unused-argument
        global ahmia_blacklist  # pylint: disable=global-statement
        if not get_setting("outgoing.using_tor_proxy"):
            # disable the plugin
            return False
        ahmia_blacklist = ahmia_blacklist_loader()
        return True
