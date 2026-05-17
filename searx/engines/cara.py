# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=invalid-name
"""Cara_ is a social media and portfolio-sharing platform for artists and art
enthusiasts.

With the widespread use of generative AI, Cara_ decided to build a place that
filters out gen AI images so that people searching for authentic creatives and
images can do so easily.

.. _Cara: https://cara.app/about
"""

from urllib.parse import urlencode

import typing as t

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://cara.app",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

base_url = "https://cara.app"
images_url = "https://images.cara.app"

categories = ["images"]
paging = True
results_per_page = 24

# if using HTTP2, we get blocked immediately
enable_http2 = False


def request(query: str, params: "OnlineParams") -> None:
    args = {
        "q": query,
        "sortBy": "Top",
        "take": results_per_page,
        "skip": (params["pageno"] - 1) * results_per_page,
    }
    params["url"] = f"{base_url}/api/search/portfolio-posts?{urlencode(args)}"


def response(resp: "SXNG_Response"):
    res = EngineResults()
    json_data: list[dict[str, t.Any]] = resp.json()

    for result in json_data:
        thumbnail, img = None, None

        i: dict[str, str]
        for i in result["images"]:
            if thumbnail is None or i["isCoverImg"]:
                thumbnail = i

            if img is None or not i["isCoverImg"]:
                img = i

        if not thumbnail or not img:
            continue

        res.add(
            res.types.LegacyResult(
                {
                    "template": "images.html",
                    "url": f"{base_url}/post/{result['id']}",
                    "thumbnail_src": f"{images_url}/{thumbnail['src']}?height=256",
                    "img_src": f"{images_url}/{img['src']}",
                    "title": result["title"],
                    "content": result["content"],
                    "author": result["name"],
                }
            )
        )

    return res
