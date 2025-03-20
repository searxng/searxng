# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from __future__ import annotations
import typing

import re
from urllib.parse import urlunparse, parse_qsl, urlencode

from flask_babel import gettext

from searx.plugins import Plugin, PluginInfo

if typing.TYPE_CHECKING:
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request
    from searx.result_types import Result
    from searx.plugins import PluginCfg

regexes = {
    re.compile(r'utm_[^&]+'),
    re.compile(r'(wkey|wemail)[^&]*'),
    re.compile(r'(_hsenc|_hsmi|hsCtaTracking|__hssc|__hstc|__hsfp)[^&]*'),
    re.compile(r'&$'),
}


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

    def on_result(
        self, request: "SXNG_Request", search: "SearchWithPlugins", result: Result
    ) -> bool:  # pylint: disable=unused-argument
        if not result.parsed_url:
            return True

        parsed_query: list[tuple[str, str]] = parse_qsl(result.parsed_url.query)
        for name_value in list(parsed_query):
            param_name = name_value[0]
            for reg in regexes:
                if reg.match(param_name):
                    parsed_query.remove(name_value)
                    result.parsed_url = result.parsed_url._replace(query=urlencode(parsed_query))
                    result.url = urlunparse(result.parsed_url)
                    break

        return True
