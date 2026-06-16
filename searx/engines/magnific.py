# SPDX-License-Identifier: AGPL-3.0-or-later
"""Magnific_ is a database for images.

.. _Magnific: https://www.magnific.com
"""

from urllib.parse import urlencode

import typing as t

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://www.magnific.com",
    "wikidata_id": "Q104211654",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

base_url = "https://www.magnific.com"

categories = ["images"]
paging = True

free_images_only = True
"""
Whether to only load images that may be used for free, without a Magnific account.
"""


def request(query: str, params: "OnlineParams") -> None:
    args = {"term": query, "filters[ai-generated][excluded]": 1, "page": params["pageno"], "locale": "en"}
    if free_images_only:
        args["filters[license]"] = "free"

    params["headers"]["Referer"] = f"{base_url}/search"
    params["url"] = f"{base_url}/api/regular/search?{urlencode(args)}"


def response(resp: "SXNG_Response"):
    res = EngineResults()

    result: dict[str, t.Any]  # TBH: dict[str, t.Any]
    for result in resp.json()["items"]:
        res.add(
            res.types.Image(
                title=result["name"],
                url=result["url"],
                thumbnail_src=result["preview"]["url"],
                img_src=result["preview"]["url"],
                resolution=f"{result['preview']['width']}x{result['preview']['height']}",
            )
        )

    return res
