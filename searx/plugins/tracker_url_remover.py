# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring, unused-argument

import logging
import typing as t

from flask_babel import gettext  # pyright: ignore[reportUnknownVariableType]

from searx.data import TRACKER_PATTERNS

from . import Plugin, PluginInfo

if t.TYPE_CHECKING:
    import flask
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request
    from searx.result_types import Result, LegacyResult  # pyright: ignore[reportPrivateLocalImportUsage]
    from searx.plugins import PluginCfg


log = logging.getLogger("searx.plugins.tracker_url_remover")


@t.final
class SXNGPlugin(Plugin):
    """Remove trackers arguments from the returned URL."""

    id = "tracker_url_remover"

    def __init__(self, plg_cfg: "PluginCfg") -> None:

        super().__init__(plg_cfg)
        self.info = PluginInfo(
            id=self.id,
            name=gettext("Tracker URL remover"),
            description=gettext("Remove trackers arguments from the returned URL"),
            preference_section="privacy",
        )

    def init(self, app: "flask.Flask") -> bool:
        TRACKER_PATTERNS.init()
        return True

    def on_result(self, request: "SXNG_Request", search: "SearchWithPlugins", result: "Result") -> bool:

        result.filter_urls(self.filter_url_field)
        return True

    @classmethod
    def filter_url_field(cls, result: "Result|LegacyResult", field_name: str, url_src: str) -> bool | str:
        """Returns bool ``True`` to use URL unchanged (``False`` to ignore URL).
        If URL should be modified, the returned string is the new URL to use."""

        if not url_src:
            log.debug("missing a URL in field %s", field_name)
            return True

        return TRACKER_PATTERNS.clean_url(url=url_src)
