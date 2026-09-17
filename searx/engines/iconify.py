# SPDX-License-Identifier: AGPL-3.0-or-later
"""Iconify aggregates icons from different open source icon sets."""

import codecs
import typing as t
from urllib.parse import urlencode

from searx.network import get
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from extended_types import SXNG_Response
    from search.processors.online import OnlineParams


about = {
    "website": "https://iconify.design",
    "wikidata_id": None,
    "official_api_documentation": None,
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

    # we request all icons from the same icon set with one request
    icon_sources: dict[str, list[str]] = {}
    for icon in resp.json()["icons"]:
        icon: str
        icon_source, icon_name = icon.split(":", 1)
        icon_sources[icon_source] = icon_sources.get(icon_source, []) + [icon_name]

    for source, names in icon_sources.items():
        icon_resp = get(f"{base_url}/{source}.json?icons={','.join(names)}").json()

        icon_name: str
        icon_info: dict[str, str]
        for icon_name, icon_info in icon_resp["icons"].items():
            w = icon_resp.get("width", 24)
            h = icon_resp.get("height", 24)
            icon_svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">{icon_info["body"]}</svg>'
            b64_icon = codecs.encode(icon_svg.encode(), encoding="base64").decode("utf-8")
            res.add(
                res.types.Image(
                    url=f"{base_url}/{source}.json?icons={icon_name}",
                    title=icon_name,
                    img_src=f"data:image/svg+xml;base64,{b64_icon}",
                )
            )

    return res
