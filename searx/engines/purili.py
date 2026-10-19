# SPDX-License-Identifier: AGPL-3.0-or-later
"""Purili"""

from datetime import datetime
import typing as t
from urllib.parse import urlencode, unquote_plus

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://puri.li",
    "wikidata_id": None,
    "official_api_documentation": "https://puri.li/developer/documentation",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["general"]
# paging not supported by news
paging = True

PuriliCategory = t.Literal["search", "images", "news"]
purili_categ: PuriliCategory = "search"

base_url = "https://puri.li"


def setup(_: dict[str, t.Any]):
    if purili_categ not in t.get_args(PuriliCategory):
        raise ValueError(f"invalid purili category: {purili_categ!r}")


def request(query: str, params: "OnlineParams"):
    if purili_categ == "news" and params["pageno"] > 1:
        params["url"] = None
        return

    args = {"q": query, "page": params["pageno"]}
    params["url"] = f"{base_url}/api/{purili_categ}?{urlencode(args)}"


def _extract_image_url(proxied_url: str | None) -> str:
    if not proxied_url:
        return ""

    url_encoded = proxied_url.split("?url=")[-1]
    return unquote_plus(url_encoded)


def response(resp: "SXNG_Response"):
    res = EngineResults()

    json_resp: dict[str, t.Any] = resp.json()

    result: dict[str, str]
    match purili_categ:
        case "search":
            for result in json_resp["results"]:
                res.add(
                    res.types.MainResult(
                        url=result["url"],
                        title=result["title"],
                        content=result["description"],
                    )
                )
        case "news":
            for result in json_resp["items"]:
                publishedDate = None
                if date := result.get("publishedAt"):
                    publishedDate = datetime.fromisoformat(date)
                res.add(
                    res.types.MainResult(
                        url=result["url"],
                        title=result["title"],
                        content=result["description"],
                        thumbnail=_extract_image_url(result.get("imageUrl")),
                        publishedDate=publishedDate,
                    )
                )
        case "images":
            for result in json_resp["images"]:
                res.add(
                    res.types.Image(
                        url=_extract_image_url(result["url"]),
                        title=result["title"],
                        img_src=_extract_image_url(result.get("url")),
                        thumbnail_src=_extract_image_url(result.get("thumbUrl")),
                        resolution=f"{result['width']}x{result['height']}",
                    )
                )

    return res
