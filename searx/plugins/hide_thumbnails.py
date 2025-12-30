# SPDX-License-Identifier: AGPL-3.0-or-later

"""
This plugin removes the 'thumbnail' property from search results if the 'hide_thumbnails' setting is enabled.
"""

import typing
from flask_babel import gettext

from searx.plugins import Plugin, PluginInfo
from searx.result_types import Result

if typing.TYPE_CHECKING:
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request
    from searx.result_types import Result
    from searx.plugins import PluginCfg


class SXNGPlugin(Plugin):
    id: str = "hide_thumbnails"

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)
        self.info = PluginInfo(
            id=self.id,
            name=gettext("Hide Thumbnails"),
            description=gettext("Removes thumbnails from search results")
        )

    def on_result(
        self,
        request: "SXNG_Request",
        search: "SearchWithPlugins",
        result: "Result"
    ) -> bool:  # pylint: disable=unused-argument
        if hasattr(result, "thumbnail"):
            result.thumbnail = None
        return True
