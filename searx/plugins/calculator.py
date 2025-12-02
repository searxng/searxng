# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

import typing as t

from flask_babel import gettext  # pyright: ignore[reportUnknownVariableType]

from searx.plugins import Plugin, PluginInfo

if t.TYPE_CHECKING:
    from searx.plugins import PluginCfg


@t.final
class SXNGPlugin(Plugin):
    """Parses and solves mathematical expressions."""

    id = "calculator"

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)

        self.info = PluginInfo(
            id=self.id,
            name=gettext("Calculator"),
            description=gettext("Parses and solves mathematical expressions."),
            preference_section="query",
        )
