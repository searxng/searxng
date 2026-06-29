# SPDX-License-Identifier: AGPL-3.0-or-later
"""Heexy_ is a minimalist search engine that focuses on privacy.

Although it also supports news and videos, these are not implemented here
because they usually return no result to very few irrelevant ones.

It seems to use Bing internally, as the image thumbnails are loaded from Bing.

.. _Heexy: https://docs.heexy.org/introduction

"""

from urllib.parse import urlencode

import typing as t
from lxml import html

from searx.enginelib import EngineCache
from searx.network import get
from searx.exceptions import SearxEngineAPIException, SearxEngineAccessDeniedException
from searx.result_types import EngineResults
from searx.utils import eval_xpath, extract_text, gen_useragent

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://heexy.org",
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

paging = True
safesearch = True

categories = ["general"]
heexy_categ = "web"
"""Category to search in. Can be either "web" or "image"."""


base_url = "https://heexy.org"
api_url = "https://seapi.heexy.org"
safe_search_map = {0: "off", 1: "on", 2: "on"}

CACHE: EngineCache
"""Cache for storing the ``X-Data-Cacheft`` token (acts like an API key)."""


def setup(engine_settings: dict[str, t.Any]) -> bool:
    global CACHE  # pylint: disable=global-statement

    if heexy_categ not in ("web", "image"):
        raise ValueError("invalid search category: %s" % heexy_categ)

    CACHE = EngineCache(engine_settings["name"])
    return True


def _get_api_token(query: str) -> str:
    """The API token is independent of the search query. We just need any query
    to obtain it initially, and don't hardcode it here to decrease chances of
    getting blocked. The token must be passed as ``X-Data-Cacheft`` header."""

    cached_token: str = CACHE.get("token")
    if cached_token:
        return cached_token

    resp = get(f"{base_url}/search?q={query}", headers={"User-Agent": gen_useragent()})
    if not resp.ok:
        raise SearxEngineAPIException("failed to obtain request token: invalid response code")

    doc = html.fromstring(resp.text)
    token = extract_text(eval_xpath(doc, "//html/@data-cacheft"))
    if not token:
        raise SearxEngineAPIException("failed to obtain request token: no token found")

    CACHE.set("token", token)
    return token


def request(query: str, params: "OnlineParams") -> None:
    args = {
        "q": query,
        "page": params["pageno"],
        "safe": safe_search_map[params["safesearch"]],
    }
    if params["searxng_locale"] != "all":
        args["lang"] = params["searxng_locale"].split("-")[0]

    params["url"] = f"{api_url}/search/{heexy_categ}?{urlencode(args)}"
    params["headers"]["X-Data-Cacheft"] = _get_api_token(query)
    params["headers"]["Origin"] = api_url


def response(resp: "SXNG_Response"):
    res = EngineResults()

    json_resp = resp.json()
    if not json_resp["success"]:
        raise SearxEngineAccessDeniedException()

    result: dict[str, str]
    for result in json_resp["results"]:
        if heexy_categ == "web":
            res.add(
                res.types.MainResult(
                    url=result["url"],
                    title=result["title"],
                    content=result["description"],
                )
            )
        elif heexy_categ == "image":
            res.add(
                res.types.Image(
                    title=result["description"],
                    url=result["url"],
                    thumbnail_src=result["image"],
                    img_src=result["rawImage"],
                )
            )

    return res
