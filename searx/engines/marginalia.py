# SPDX-License-Identifier: AGPL-3.0-or-later
"""`Marginalia Search`_ is an independent open source Internet search engine
operating out of Sweden. It is principally developed and operated by Viktor
Lofgren .

.. _Marginalia Search:
   https://about.marginalia-search.com/


.. _marginalia filters:

Marginalia Filters
=================

Custom filters enable server-side customization of Marginalia search results.
Filter definitions are written in XML and scoped to an API key.  Filters can
not be used with the public API key ``public``.  The
`Marginalia Filter Editor`_ can be used to create custom filters with a GUI.
Alternatively, filters can be written manually in XML.  To associate a filter
definition with an API key, upload the XML data to the ``/filter/<NAME>`` API
endpoint, where ``<NAME>`` is the name for the newly created filter.  For more
information, see the `Marginalia filters announcement blogpost`_ and the
official `Marginalia API documentation`_.

.. _Marginalia Filter Editor: https://marginalia-search.com/filters
.. _Marginalia filters announcement blogpost: https://www.marginalia.nu/log/a_127_index_filtering/
.. _Marginalia API documentation: https://about.marginalia-search.com/article/api/


Configuration
=============

The engine has the following required settings:

- :py:obj:`api_key`

The engine has the following optional settings:

- :py:obj:`filter_name`

You can configure a Marginalia engine by:

.. code:: yaml

   - name: marginalia
     engine: marginalia
     shortcut: mar
     api_key: ...
     filter_name: ...

Implementations
===============

"""

import typing as t
from urllib.parse import urlencode

from searx.network import get
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

base_url = "https://api2.marginalia-search.com"
safesearch = True
categories = ["general", "blogs"]
paging = True
results_per_page = 20
api_key = None
"""To get an API key, please follow the instructions from `Key and license`_

.. _Key and license:
   https://about.marginalia-search.com/article/api/

"""
filter_name: str | None = None
"""The name of the custom filter to apply to each search."""


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


def _marginalia_headers() -> dict[str, t.Any]:
    return {
        "User-Agent": searxng_useragent(),
        "API-Key": api_key,
    }


def _get_filter_names() -> list[str]:

    resp = get(f"{base_url}/filter", headers=_marginalia_headers())
    if resp.ok:
        filter_names = resp.json()
    else:
        filter_names = []
    if not isinstance(filter_names, list):
        raise TypeError("marginalia api returned invalid filter list format")
    return filter_names


def request(query: str, params: dict[str, t.Any]):

    query_params = {
        "page": params["pageno"],
        "count": results_per_page,
        "nsfw": min(params["safesearch"], 1),
        "query": query,
    }
    if filter_name:
        query_params["filter"] = filter_name

    params["url"] = f"{base_url}/search?{urlencode(query_params)}"
    params["headers"].update(_marginalia_headers())


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


def init(_: dict[str, t.Any]):

    if not api_key:
        logger.error("missing api_key: see https://about.marginalia-search.com/article/api")
        return False

    if api_key == "public":
        logger.error("invalid api_key (%s): see https://about.marginalia-search.com/article/api", api_key)
    elif filter_name:
        filter_names: list[str] = _get_filter_names()
        if filter_name not in filter_names:
            logger.error(f"invalid value for filter_name: '{filter_name}'")
            return False

    return True
