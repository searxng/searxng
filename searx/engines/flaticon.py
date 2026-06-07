# SPDX-License-Identifier: AGPL-3.0-or-later
"""Flaticon_ is a database for icons.

.. _Flaticon: https://www.flaticon.com
"""

from urllib.parse import urlencode

import typing as t

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://www.flaticon.com",
    "wikidata_id": "Q105283791",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

base_url = "https://www.flaticon.com"

categories = ["images", "icons"]
paging = True


def request(query: str, params: "OnlineParams") -> None:
    args = {
        "word": query,
    }
    params["headers"].update(
        {
            # important: query term is not URL encoded in the referer string
            "Referer": f"{base_url}/search?word={query}",
            "X-Requested-With": "XMLHttpRequest",
        }
    )
    params["url"] = f"{base_url}/ajax/search/{params['pageno']}?{urlencode(args)}"


def _fix_url(url: str) -> str:
    return url.replace(r"\/", "/")


def response(resp: "SXNG_Response"):
    res = EngineResults()

    result: dict[str, str]  # TBH: dict[str, t.Any]
    for result in resp.json()["items"]:
        tags = [
            tag_info["tag"] for tag_info in result["tags"] if tag_info["tag"]  # pyright: ignore[reportArgumentType]
        ]
        res.add(
            res.types.Image(
                title=result["name"],
                content=", ".join(tags),
                url=_fix_url(result["slug"]),
                thumbnail_src=_fix_url(result["png"]),
                img_src=_fix_url(result["png512"]),
                author=result["team_name"],
            )
        )

    return res
