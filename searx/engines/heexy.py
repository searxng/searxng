# SPDX-License-Identifier: AGPL-3.0-or-later
"""Heexy_ is a minimalist search engine that focuses on privacy.

Although it also supports news and videos, these are not implemented here
because they usually return no result to very few irrelevant ones.

It seems to use Bing internally, as the image thumbnails are loaded from Bing.

.. _Heexy: https://docs.heexy.org/introduction

"""

from urllib.parse import urlencode

import typing as t

from searx.exceptions import SearxEngineAccessDeniedException
from searx.result_types import EngineResults

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


base_url = "https://seapi.heexy.org"
safe_search_map = {0: "off", 1: "on", 2: "on"}


def init(_):
    if heexy_categ not in ("web", "image"):
        raise ValueError("invalid search category: %s" % heexy_categ)


def request(query: str, params: "OnlineParams") -> None:
    args = {
        "q": query,
        "page": params["pageno"],
        "safe": safe_search_map[params["safesearch"]],
    }
    if params["searxng_locale"] != "all":
        args["lang"] = params["searxng_locale"].split("-")[0]

    params["url"] = f"{base_url}/search/{heexy_categ}?{urlencode(args)}"
    params["headers"]["Origin"] = base_url


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
