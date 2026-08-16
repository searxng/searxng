# SPDX-License-Identifier: AGPL-3.0-or-later
"""Iconify aggregates icons from different open source icon sets."""

import typing as t
from urllib.parse import urlencode

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from extended_types import SXNG_Response
    from search.processors.online import OnlineParams


about = {
    "website": "https://iconify.design",
    "wikidata_id": None,
    "official_api_documentation": "https://iconify.design/docs/api/queries.html",
    "use_official_api": True,
    "results": "JSON",
}

categories = ["images", "icons"]
paging = True

base_url = "https://api.iconify.design"
page_size = 20


def request(query: str, params: "OnlineParams"):
    # actual number of results isn't exaxctly the same as the page size, only approximately
    args = {"query": query, "start": (params["pageno"] - 1) * page_size, "limit": page_size}
    params["url"] = f"{base_url}/search?{urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    for icon in resp.json()["icons"]:
        icon: str
        icon_source, icon_name = icon.split(":", 1)
        icon_url = f"{base_url}/{icon_source}/{icon_name}.svg"
        res.add(
            res.types.Image(
                url=icon_url,
                title=icon_name,
                img_src=icon_url,
            )
        )

    return res
