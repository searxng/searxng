# SPDX-License-Identifier: AGPL-3.0-or-later
"""`Marginalia Search`_ is an independent open source Internet search engine
operating out of Sweden. It is principally developed and operated by Viktor
Lofgren .

.. _Marginalia Search:
   https://about.marginalia-search.com/

Configuration
=============

The engine has the following required settings:

- :py:obj:`api_key`

You can configure a Marginalia engine by:

.. code:: yaml

   - name: marginalia
     engine: marginalia
     shortcut: mar
     api_key: ...

Implementations
===============

"""
from __future__ import annotations

import typing as t
from urllib.parse import urlencode, quote_plus
from searx.utils import searxng_useragent
from searx.result_types import EngineResults
from searx.extended_types import SXNG_Response

about = {
    "website": "https://marginalia.nu",
    "wikidata_id": None,
    "official_api_documentation": "https://about.marginalia-search.com/article/api/",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

base_url = "https://api.marginalia.nu"
safesearch = True
categories = ["general"]
paging = False
results_per_page = 20
api_key = None
"""To get an API key, please follow the instructions from `Key and license`_

.. _Key and license:
   https://about.marginalia-search.com/article/api/

"""


class ApiSearchResult(t.TypedDict):
    """Marginalia's ApiSearchResult_ class definition.

    .. _ApiSearchResult:
       https://github.com/MarginaliaSearch/MarginaliaSearch/blob/master/code/services-application/api-service/java/nu/marginalia/api/model/ApiSearchResult.java
    """

    url: str
    title: str
    description: str
    quality: float
    format: str
    details: str


class ApiSearchResults(t.TypedDict):
    """Marginalia's ApiSearchResults_ class definition.

    .. _ApiSearchResults:
       https://github.com/MarginaliaSearch/MarginaliaSearch/blob/master/code/services-application/api-service/java/nu/marginalia/api/model/ApiSearchResults.java
    """

    license: str
    query: str
    results: list[ApiSearchResult]


def request(query: str, params: dict[str, t.Any]):

    query_params = {
        "count": results_per_page,
        "nsfw": min(params["safesearch"], 1),
    }

    params["url"] = f"{base_url}/{api_key}/search/{quote_plus(query)}?{urlencode(query_params)}"
    params["headers"]["User-Agent"] = searxng_useragent()


def response(resp: SXNG_Response):

    res = EngineResults()
    resp_json: ApiSearchResults = resp.json()  # type: ignore

    for item in resp_json.get("results", []):
        res.add(
            res.types.MainResult(
                title=item["title"],
                url=item["url"],
                content=item.get("description", ""),
            )
        )

    return res


def init(engine_settings: dict[str, t.Any]):

    _api_key = engine_settings.get("api_key")
    if not _api_key:
        logger.error("missing api_key: see https://about.marginalia-search.com/article/api")
        return False

    if _api_key == "public":
        logger.error("invalid api_key (%s): see https://about.marginalia-search.com/article/api", api_key)

    return True
