# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tusksearch_ is an American search engine that claims to fight censorship.
Its search results are (at least partially) from Brave.

.. _Tusksearch: https://tusksearch.com/about
"""

from json import loads
import random
import typing as t
from urllib.parse import urlencode
from dateutil import parser

from searx.exceptions import SearxEngineAPIException
from searx.network import get
from searx.utils import gen_useragent, html_to_text
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://tusksearch.com",
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

paging = True

categories = ["general"]
tusk_categ = "web"
"""Category to search in. Can be either "web", "images", "videos" or "news"."""


api_url = "https://api.tusksearch.com"


def init(_):
    if tusk_categ not in ("web", "images", "videos", "news"):
        raise ValueError("invalid search type: %s" % tusk_categ)


def _obtain_x_sid() -> tuple[str, str]:
    """
    The session ID ("sid") is encoded as a byte array in ``embed.js``.
    It is only valid for exactly one request, so we can't cache it.

    The header key is usually called `x-sid-{UUIDv4}`, and the value is
    usually a plain UUIDv4 (but a different one than in the header key).
    """
    resp = get(f"{api_url}/revcontent/embed.js", headers={"User-Agent": gen_useragent()})
    if not resp.ok:
        raise SearxEngineAPIException("failed to obtain request x-sid token")

    # data is prefixed by 'var x='
    data_array = loads(resp.text[6:])

    def _byte_array_to_ascii(text: list[int]) -> str:
        """
        Converts a byte array (e.g. [81, 101, 97, 114, 88, 78, 71]) to the ASCII
        string representation (e.g. "SearXNG").
        """
        return "".join([chr(x) for x in text])

    x_sid_header = _byte_array_to_ascii(data_array[3])
    x_sid_value = _byte_array_to_ascii(data_array[4])
    return x_sid_header, x_sid_value


def request(query: str, params: "OnlineParams") -> None:
    # images don't support pagination, news and videos only support two pages
    if tusk_categ == "images" and params["pageno"] > 1 or tusk_categ in ("news", "videos") and params["pageno"] > 2:
        params["url"] = None
        return

    args = {
        "q": query,
        "p": params["pageno"],
        "l": "center",  # political direction: "left", "center" or "right"
    }
    if tusk_categ == "images":
        params["url"] = f"{api_url}/Search/Image?{urlencode(args)}"
    else:
        # web response also contains news and videos
        params["url"] = f"{api_url}/Search/Web?{urlencode(args)}"

    x_sid_header, x_sid_value = _obtain_x_sid()
    params["headers"].update(
        {
            x_sid_header: x_sid_value,
            # required - we send a random longitude and latitude instead of the actual user location
            "x-lon": str(round(random.random() * 90, 4)),
            "x-lat": str(round(random.random() * 90, 4)),
        }
    )


def response(resp: "SXNG_Response"):
    res = EngineResults()

    json_resp = resp.json()["results"]

    if tusk_categ == "web":
        for result in (json_resp.get("web") or {}).get("results", []):
            res.add(
                res.types.MainResult(
                    url=result["url"],
                    title=html_to_text(result["title"]),
                    content=html_to_text(result["description"]),
                    thumbnail=(result["thumbnail"] or {}).get("src") or "",
                )
            )
    elif tusk_categ == "news":
        for result in (json_resp.get("news") or {}).get("results", []):
            publishedDate = None
            try:
                publishedDate = parser.parse(result["age"])
            except parser.ParserError:
                pass

            res.add(
                res.types.MainResult(
                    url=result["url"],
                    title=html_to_text(result["title"]),
                    content=html_to_text(result["description"]),
                    thumbnail=result["thumbnail"]["src"],
                    publishedDate=publishedDate,
                )
            )
    elif tusk_categ == "videos":
        for result in (json_resp.get("videos") or {}).get("results", []):
            publishedDate = None
            try:
                publishedDate = parser.parse(result["age"])
            except parser.ParserError:
                pass

            res.add(
                res.types.LegacyResult(
                    template="videos.html",
                    url=result["url"],
                    title=html_to_text(result["title"]),
                    content=html_to_text(result["description"]),
                    thumbnail=result["thumbnail"]["src"],
                    publishedDate=publishedDate,
                    length=result["video"].get("duration"),
                )
            )
    elif tusk_categ == "images":
        for result in json_resp:
            res.add(
                res.types.Image(
                    url=result["url"],
                    title=html_to_text(result["title"]),
                    img_src=result["properties"]["url"],
                    thumbnail_src=result["thumbnail"]["src"],
                )
            )

    return res
