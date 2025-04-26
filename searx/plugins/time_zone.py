# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from __future__ import annotations
import typing as t

import datetime

from flask_babel import gettext  # type: ignore
from searx.result_types import EngineResults
from searx.weather import DateTime, GeoLocation

from . import Plugin, PluginInfo

if t.TYPE_CHECKING:
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request
    from searx.plugins import PluginCfg


@t.final
class SXNGPlugin(Plugin):
    """Plugin to display the current time at different timezones (usually the
    query city)."""

    id: str = "time_zone"
    keywords: list[str] = ["time", "timezone", "now", "clock", "timezones"]

    def __init__(self, plg_cfg: "PluginCfg"):
        super().__init__(plg_cfg)

        self.info = PluginInfo(
            id=self.id,
            name=gettext("Timezones plugin"),
            description=gettext("Display the current time on different time zones."),
            preference_section="query",
            examples=["time Berlin", "clock Los Angeles"],
        )

    def post_search(self, request: "SXNG_Request", search: "SearchWithPlugins") -> EngineResults:
        """The plugin uses the :py:obj:`searx.weather.GeoLocation` class, which
        is already implemented in the context of weather forecasts, to determine
        the time zone. The :py:obj:`searx.weather.DateTime` class is used for
        the localized display of date and time."""

        results = EngineResults()
        if search.search_query.pageno > 1:
            return results

        # remove keywords from the query
        query = search.search_query.query
        query_parts = filter(lambda part: part.lower() not in self.keywords, query.split(" "))
        search_term = " ".join(query_parts).strip()

        if not search_term:
            date_time = DateTime(time=datetime.datetime.now())
            results.add(results.types.Answer(answer=date_time.l10n()))
            return results

        geo = GeoLocation.by_query(search_term=search_term)
        if geo:
            date_time = DateTime(time=datetime.datetime.now(tz=geo.zoneinfo))
            tz_name = geo.timezone.replace('_', ' ')
            results.add(
                results.types.Answer(
                    answer=(f"{tz_name}:" f" {date_time.l10n()} ({date_time.datetime.strftime('%Z')})")
                )
            )

        return results
