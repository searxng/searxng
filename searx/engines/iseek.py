# SPDX-License-Identifier: AGPL-3.0-or-later
"""iseek_ is a search engine by the AI company Vantage Labs LLC,
that focuses on medical and educational applicances.
Although it's an AI company, it doesn't include any AI stuff in its results.

.. _iseek : https://www.iseek.ai/
"""

import base64
from hashlib import sha256
import typing as t
from urllib.parse import urlencode

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams
    from searx.extended_types import SXNG_Response


about = {
    "website": 'https://www.iseek.com',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}
categories = ["general"]
paging = True

base_url = "https://api.iseek.com"
page_size = 10


def _get_new_token(query: str, pageno: int) -> str:
    """Create a new ``qToken``. This reduced the time for fetching subsequent pages
    from 4 seconds to 200ms when testing."""
    # The website uses a random value as qToken for the first page. For our use case,
    # it's easier if the qToken can be deterministically re-calculated based on the search query,
    # so that we can the same result when calling _get_new_token for the second, third, ... page
    #
    # var qToken = Math.ceil(Math.random() * parseInt("ZZZZ", 36)).toString(36);
    # while (qToken.length < 4) qToken = '0' + qToken;
    # qToken = qToken + "_" + pageno
    query_hash = sha256(query.encode()).digest()
    hash_start = base64.b64encode(query_hash).decode()[0:4]
    return f"{hash_start}_{pageno}"


def request(query: str, params: "OnlineParams"):
    offset = (params["pageno"] - 1) * page_size

    # always seems to find 20 results max
    if offset >= 20:
        params["url"] = None
        return

    args = {
        "q": query,
        "key": "core-web",
        "num": str(page_size),
        "off": offset,
        "rSort": "__metasearch_score_d:desc",
        # it supports many more fields, but none of them are really relevant
        "names": "title_t,content_txt,url_s",
        "qNames": "title_t",
        "qToken": _get_new_token(query, params["pageno"]),
    }
    params["url"] = f"{base_url}/search?{urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    for group in resp.json()["data"]:
        group: dict[str, t.Any]
        for result in group["doclist"]["docs"]:
            result: dict[str, str]
            res.add(
                res.types.MainResult(
                    url=result["url_s"],
                    title=result["title_t"],
                    content="".join(result["content_txt"]),
                )
            )

    return res
