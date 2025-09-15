# SPDX-License-Identifier: AGPL-3.0-or-later
"""The Astrophysics Data System (ADS_) is a digital library portal for
researchers in astronomy and physics, operated by the Smithsonian Astrophysical
Observatory (SAO) under a NASA grant.  The ADS_ is a solr instance, but not with
the standard API paths.

.. note::

   The ADS_ engine requires an :py:obj:`API key <api_key>`.

This engine uses the `search/query`_ API endpoint.  Since the user's search term
is passed through, the `search syntax`_ of ADS can be used (at least to some
extent).

.. _ADS: https://ui.adsabs.harvard.edu
.. _search/query: https://ui.adsabs.harvard.edu/help/api/api-docs.html#get-/search/query
.. _search syntax: https://ui.adsabs.harvard.edu/help/search/search-syntax


Configuration
=============

The engine has the following additional settings:

- :py:obj:`api_key`
- :py:obj:`ads_sort`

.. code:: yaml

  - name: astrophysics data system
    api_key: "..."
    inactive: false


Implementations
===============
"""

import typing as t

from datetime import datetime
from urllib.parse import urlencode

from searx.utils import html_to_text
from searx.exceptions import SearxEngineAPIException
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://ui.adsabs.harvard.edu/",
    "wikidata_id": "Q752099",
    "official_api_documentation": "https://ui.adsabs.harvard.edu/help/api/api-docs.html",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

categories = ["science", "scientific publications"]
paging = True
base_url = "https://api.adsabs.harvard.edu/v1/search/query"

api_key = "unset"
"""Get an API token as described in https://ui.adsabs.harvard.edu/help/api"""

ads_field_list = [
    "abstract",
    "author",
    "bibcode",
    "comment",
    "date",
    "doi",
    "isbn",
    "issn",
    "keyword",
    "page",
    "page_count",
    "page_range",
    "pub",
    "pubdate",
    "pubnote",
    "read_count",
    "title",
    "volume",
    "year",
]
"""Set of fields to return in the response from ADS."""

ads_rows = 10
"""How many records to return for the ADS request."""

ads_sort = "read_count desc"
"""The format is 'field' + 'direction' where direction is one of 'asc' or 'desc'
and field is any of the valid indexes."""


def setup(engine_settings: dict[str, t.Any]) -> bool:
    """Initialization of the ADS_ engine, checks whether the :py:obj:`api_key`
    is set, otherwise the engine is inactive.
    """
    key: str = engine_settings.get("api_key", "")
    if key and key not in ("unset", "unknown", "..."):
        return True
    logger.error("Astrophysics Data System (ADS) API key is not set or invalid.")
    return False


def request(query: str, params: "OnlineParams") -> None:

    args: dict[str, str | int] = {
        "q": query,
        "fl": ",".join(ads_field_list),
        "rows": ads_rows,
        "start": ads_rows * (params["pageno"] - 1),
    }
    if ads_sort:
        args["sort"] = ads_sort

    params["headers"]["Authorization"] = f"Bearer {api_key}"
    params["url"] = f"{base_url}?{urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:

    res = EngineResults()
    json_data: dict[str, dict[str, t.Any]] = resp.json()

    if "error" in json_data:
        raise SearxEngineAPIException(json_data["error"]["msg"])

    def _str(k: str) -> str:
        return str(doc.get(k, ""))

    def _list(k: str) -> list[str]:
        return doc.get(k, [])

    for doc in json_data["response"]["docs"]:
        authors: list[str] = doc["author"]
        if len(authors) > 15:
            # There are articles with hundreds of authors
            authors = authors[:15] + ["et al."]

        paper = res.types.Paper(
            url=f"https://ui.adsabs.harvard.edu/abs/{doc.get('bibcode')}/",
            title=html_to_text(_list("title")[0]),
            authors=authors,
            content=html_to_text(_str("abstract")),
            doi=_list("doi")[0],
            issn=_list("issn"),
            isbn=_list("isbn"),
            tags=_list("keyword"),
            pages=",".join(_list("page")),
            publisher=_str("pub") + " " + _str("year"),
            publishedDate=datetime.fromisoformat(_str("date")),
            volume=_str("volume"),
            views=_str("read_count"),
            comments=" / ".join(_list("pubnote")),
        )
        res.add(paper)

    return res
