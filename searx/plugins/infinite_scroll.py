# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

import typing as t

from flask_babel import gettext  # pyright: ignore[reportUnknownVariableType]

from searx.plugins import Plugin, PluginInfo

if t.TYPE_CHECKING:
    from searx.plugins import PluginCfg


@t.final
class SXNGPlugin(Plugin):
    """Automatically loads the next page when scrolling to bottom of the current page."""

    id = "infiniteScroll"

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)

        self.info = PluginInfo(
            id=self.id,
            name=gettext("Infinite scroll"),
            description=gettext("Automatically loads the next page when scrolling to bottom of the current page"),
            preference_section="ui",
        )
