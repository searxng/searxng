"""Searchcode (IT)"""

from __future__ import annotations

import typing as t

from urllib.parse import urlencode

from searx.result_types import EngineResults
from searx.extended_types import SXNG_Response

# about
about = {
    "website": "https://searchcode.com/",
    "wikidata_id": None,
    "official_api_documentation": "https://searchcode.com/api/",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

# engine dependent config
categories = ["it"]
search_api = "https://searchcode.com/api/codesearch_I/?"

# paging is broken in searchcode.com's API .. not sure it will ever been fixed
# paging = True


def request(query: str, params: dict[str, t.Any]) -> None:
    args = {
        "q": query,
        # paging is broken in searchcode.com's API
        # "p": params["pageno"] - 1,
        # "per_page": 10,
    }

    params["url"] = search_api + urlencode(args)
    logger.debug("query_url --> %s", params["url"])


def response(resp: SXNG_Response) -> EngineResults:
    res = EngineResults()

    # parse results
    for result in resp.json().get("results", []):
        lines = {}
        for line, code in result["lines"].items():
            lines[int(line)] = code

        res.add(
            res.types.Code(
                url=result["url"],
                title=f'{result["name"]} - {result["filename"]}',
                repository=result["repo"],
                filename=result["filename"],
                codelines=sorted(lines.items()),
                strip_whitespace=True,
            )
        )

    return res
