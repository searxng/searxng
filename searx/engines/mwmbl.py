# SPDX-License-Identifier: AGPL-3.0-or-later
"""Mwmbl_ is a non-profit, ad-free, free-libre and free-lunch search engine with
a focus on useability and speed.

.. hint::

   At the moment it is little more than an idea together with a proof of concept
   implementation of the web front-end and search technology on a small index.
   Mwmbl_ does not support regions, languages, safe-search or time range.
   search.

.. _Mwmbl: https://github.com/mwmbl/mwmbl

"""

import typing as t
from urllib.parse import urlencode
from searx.utils import searxng_useragent
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://github.com/mwmbl/mwmbl",
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}
paging = False
categories = ["general"]

api_url = "https://api.mwmbl.org/api/v1"


def request(query: str, params: "OnlineParams"):
    headers = {
        "User-Agent": searxng_useragent(),
    }
    params["headers"].update(headers)
    params["url"] = f"{api_url}/search/?{urlencode({'s': query})}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()
    json_results = resp.json()

    for result in json_results:
        title_parts = [title["value"] for title in result["title"]]
        extract_parts = [extract["value"] for extract in result.get("extract", [])]
        res.add(
            res.types.MainResult(
                url=result["url"],
                title="".join(title_parts),
                content="".join(extract_parts),
            )
        )

    return res
