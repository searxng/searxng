# SPDX-License-Identifier: AGPL-3.0-or-later
"""Giphy (images)"""

import random
from urllib.parse import urlencode
import re

import typing as t

from lxml import html

from searx.enginelib import EngineCache
from searx.exceptions import SearxEngineAPIException
from searx.network import get
from searx.result_types import EngineResults
from searx.result_types.image import ImageRef
from searx.utils import eval_xpath_list, humanize_bytes

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://giphy.com",
    "wikidata_id": "Q17054335",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

base_url = "https://giphy.com"
api_url = "https://api.giphy.com"

categories = ["images"]
paging = True
page_size = 15

GiphyCategs = t.Literal["gifs", "stickers", "clips"]
giphy_categ: GiphyCategs = "gifs"
"""Giphy category to search in."""

CACHE: EngineCache
"""Cache for storing the extracted api key."""


_GIPHY_API_KEY_RE = re.compile(r"[Aa]piKey\s*:\s*\"(\w+)\"")


def setup(engine_settings: dict[str, str]) -> bool:
    if giphy_categ not in t.get_args(GiphyCategs):
        raise ValueError("invalid category: %s" % giphy_categ)

    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache(engine_settings["name"])

    return True


def _get_api_key() -> str:
    """
    Extract the Giphy API key from the JavaScript code. There are different API keys
    (e.g. for mobile, desktop, ...), so we just pick a random one of these.
    """
    cached = CACHE.get("api_key")
    if cached:
        return cached

    homepage_resp = get(base_url)
    homepage_doc = html.fromstring(homepage_resp.text)

    for script_src in eval_xpath_list(homepage_doc, "//script[contains(@src, 'layout')]/@src"):
        script_resp = get(base_url + script_src)
        api_keys = _GIPHY_API_KEY_RE.findall(script_resp.text)
        if api_keys:
            api_key = random.choice(api_keys)
            CACHE.set("api_key", api_key, expire=60 * 60 * 6)  # 6 hours
            return api_key

    raise SearxEngineAPIException("failed to extract api keys")


def request(query: str, params: "OnlineParams") -> None:
    args = {
        "q": query,
        "api_key": _get_api_key(),
        "limit": page_size,
        "offset": (params["pageno"] - 1) * page_size,
        "type": giphy_categ,
    }
    params["url"] = f"{api_url}/v1/{giphy_categ}/search?{urlencode(args)}"


def response(resp: "SXNG_Response"):
    res = EngineResults()

    result: dict[str, t.Any]
    for result in resp.json()["data"]:
        img = result['images']['original']
        formats = [
            ImageRef(url=img["mp4"], subtype="mp4"),  # type: ignore
            ImageRef(url=img["webp"], subtype="webp"),  # type: ignore
        ]
        thumb = (
            result["images"].get("downsized")
            or result["images"].get("downsized_medium")
            or result["images"].get("downsized_small")
            or result["images"].get("downsized_large")
        )
        res.add(
            res.types.Image(
                title=result["title"],
                content=", ".join(result.get("tags", [])),
                url=result["url"],
                thumbnail_src=thumb.get("url") or img["url"],
                img_src=img["url"],
                resolution=f"{img['width']}x{img['height']}",
                img_format="GIF",
                formats=formats,
                author=result["username"],
                filesize=humanize_bytes(int(img["size"])),
                source=result.get("source_tld") or "",
            )
        )

    return res
