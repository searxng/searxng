# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from __future__ import annotations
import typing

import re
from urllib.parse import urlunparse, parse_qsl, urlencode, ParseResult

from flask_babel import gettext

from searx.plugins import Plugin, PluginInfo
from searx.data import TRACKER_PATTERNS

if typing.TYPE_CHECKING:
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request
    from searx.result_types import Result
    from searx.plugins import PluginCfg


class SXNGPlugin(Plugin):
    """Remove trackers arguments from the returned URL"""

    id = "tracker_url_remover"

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)
        self.info = PluginInfo(
            id=self.id,
            name=gettext("Tracker URL remover"),
            description=gettext("Remove trackers arguments from the returned URL"),
            preference_section="privacy",
        )

    def _remove_queries(self, url: ParseResult, query_regexes: list[str]):
        parsed_query: list[tuple[str, str]] = list(parse_qsl(url.query))

        for param_name, param_value in parsed_query.copy():
            for reg in query_regexes:
                if re.match(reg, param_name):
                    parsed_query.remove((param_name, param_value))

        return url._replace(query=urlencode(parsed_query))

    def on_result(
        self, request: "SXNG_Request", search: "SearchWithPlugins", result: Result
    ) -> bool:  # pylint: disable=unused-argument
        if not result.parsed_url:
            return True

        for rule in TRACKER_PATTERNS:
            if not re.match(rule["urlPattern"], result.url):
                continue

            for exception in rule["exceptions"]:
                if re.match(exception, result.url):
                    break
            else:
                result.parsed_url = self._remove_queries(result.parsed_url, rule["trackerParams"])
                result.url = urlunparse(result.parsed_url)

        return True
