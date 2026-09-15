# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tusksearch_ is an American search engine that claims to fight censorship.
Its search results are (at least partially) from Brave.

.. _Tusksearch: https://tusksearch.com/about
"""

from json import loads
import random
import typing as t
from urllib.parse import urlencode

from searx.engines.brave import parse_images_json, parse_news_json, parse_videos_json, parse_web_json
from searx.exceptions import SearxEngineAPIException
from searx.network import get

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
TuskCategType = t.Literal["web", "images", "videos", "news"]
tusk_categ: TuskCategType = "web"
"""Category to search in. Can be either "web", "images", "videos" or "news"."""


api_url = "https://api.tusksearch.com"


def setup(_: dict[str, t.Any]) -> bool | None:
    if tusk_categ not in t.get_args(TuskCategType):
        raise ValueError("invalid search type: %s" % tusk_categ)


def _obtain_x_sid() -> tuple[str, str]:
    """
    The session ID ("sid") is encoded as a byte array in ``embed.js``.
    It is only valid for exactly one request, so we can't cache it.

    The header key is usually called `x-sid-{UUIDv4}`, and the value is
    usually a plain UUIDv4 (but a different one than in the header key).
    """
    resp = get(f"{api_url}/revcontent/embed.js", headers={"Referer": "https://tusksearch.com/"})
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
            "Referer": "https://tusksearch.com/",
        }
    )


def response(resp: "SXNG_Response"):
    json_resp = resp.json()["results"]

    match tusk_categ:
        case "web":
            results = (json_resp.get("web") or {}).get("results", [])
            return parse_web_json(results)
        case "news":
            results = (json_resp.get("news") or {}).get("results", [])
            return parse_news_json(results)
        case "videos":
            results = (json_resp.get("videos") or {}).get("results", [])
            return parse_videos_json(results)
        case "images":
            return parse_images_json(json_resp)
