# SPDX-License-Identifier: AGPL-3.0-or-later
"""media.ccc.de"""

import typing as t
import datetime
from urllib.parse import urlencode

import dateutil.parser

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://media.ccc.de",
    "official_api_documentation": "https://github.com/voc/voctoweb",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}
categories = ["videos"]
paging = True

api_url = "https://api.media.ccc.de"


def request(query: str, params: "OnlineParams"):
    args = {"q": query, "page": params["pageno"]}
    params["url"] = f"{api_url}/public/events/search?{urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    for item in resp.json()["events"]:
        publishedDate = None
        if item.get("date"):
            publishedDate = dateutil.parser.parse(item["date"])

        iframe_src = None
        for rec in item["recordings"]:
            if rec["mime_type"].startswith("video"):
                if not iframe_src:
                    iframe_src = rec["recording_url"]
                elif rec["mime_type"] == "video/mp4":
                    # prefer mp4 (minimal data rates)
                    iframe_src = rec["recording_url"]

        res.add(
            res.types.Video(
                url=item["frontend_link"],
                title=item["title"],
                content=item["description"] or "",
                thumbnail=item["thumb_url"],
                publishedDate=publishedDate,
                length=datetime.timedelta(seconds=item["length"]),
                iframe_src=iframe_src or "",
            )
        )

    return res
