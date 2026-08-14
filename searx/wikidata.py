# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared methods for accessing Wikidata."""

import typing as t
from urllib.parse import urlencode

from searx.network import get, post
from searx.utils import gen_useragent


# SPARQL
SPARQL_ENDPOINT_URL = "https://query.wikidata.org/sparql"
SPARQL_EXPLAIN_URL = "https://query.wikidata.org/bigdata/namespace/wdq/sparql?explain"


def send_wikidata_query(query: str, method: str = "GET", **kwargs: dict[str, t.Any]) -> dict[str, t.Any]:
    if method == "GET":
        # query will be cached by wikidata
        http_response = get(
            SPARQL_ENDPOINT_URL + "?" + urlencode({"query": query}), headers=get_wikidata_headers(), **kwargs
        )
    else:
        # query won't be cached by wikidata
        http_response = post(SPARQL_ENDPOINT_URL, data={"query": query}, headers=get_wikidata_headers(), **kwargs)

    http_response.raise_for_status()
    return http_response.json()


def get_wikidata_headers() -> dict[str, str]:
    # user agent: https://www.mediawiki.org/wiki/Wikidata_Query_Service/User_Manual#Query_limits
    return {
        "Accept": "application/sparql-results+json",
        "User-Agent": gen_useragent(),
    }
