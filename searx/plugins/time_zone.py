# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring, missing-class-docstring
import zoneinfo
import datetime

from flask_babel import gettext
from searx.result_types import EngineResults
from searx.data import TIMEZONES

from . import Plugin, PluginInfo


datetime_format = "%H:%M - %A, %d/%m/%y"


class SXNGPlugin(Plugin):

    id = "time_zone"
    keywords = ["time", "timezone", "now", "clock", "timezones"]

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
        results = EngineResults()

        # remove keywords from the query
        query = search.search_query.query
        query_parts = filter(lambda part: part.lower() not in self.keywords, query.split(" "))
        location = "_".join(query_parts)

        if not location:
            results.add(results.types.Answer(answer=f"{datetime.datetime.now().strftime(datetime_format)}"))
            return results

        # location is too short for proper matching
        if len(location) <= 3:
            return results

        zones = TIMEZONES["cities"].copy()
        zones.update(TIMEZONES["countries"])
        for key, tz_name in zones.items():
            if location in key.lower():
                zone = zoneinfo.ZoneInfo(tz_name)
                now = datetime.datetime.now(tz=zone)

                results.add(
                    results.types.Answer(
                        answer=f"{now.strftime(datetime_format)} at {tz_name.replace('_', ' ')} ({now.strftime('%Z')})"
                    )
                )

        return results
