# SPDX-License-Identifier: AGPL-3.0-or-later
"""`Open Library`_ is an open, editable library catalog, building towards a web
page for every book ever published.

.. _Open Library: https://openlibrary.org

Configuration
=============

The service sometimes takes a very long time to respond, the ``timeout`` may
need to be adjusted.

.. code:: yaml

  - name: openlibrary
    engine: openlibrary
    shortcut: ol
    timeout: 10


Implementations
===============

"""

from datetime import datetime
import typing as t

from urllib.parse import urlencode
from dateutil import parser

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://openlibrary.org",
    "wikidata_id": "Q1201876",
    "require_api_key": False,
    "use_official_api": False,
    "official_api_documentation": "https://openlibrary.org/developers/api",
}

paging = True
categories = ["general", "books"]

base_url = "https://openlibrary.org"
search_api = "https://openlibrary.org/search.json"
"""The engine uses the API at the endpoint search.json_.

.. _search.json: https://openlibrary.org/dev/docs/api/search
"""
results_per_page = 10


def request(query: str, params: "OnlineParams") -> None:
    args = {
        "q": query,
        "page": params["pageno"],
        "limit": results_per_page,
        "fields": "*",
    }
    params["url"] = f"{search_api}?{urlencode(args)}"
    logger.debug("REST API: %s", params["url"])


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()
    json_data = resp.json()

    for item in json_data.get("docs", []):
        cover = ""
        if "lending_identifier_s" in item:
            cover = f"https://archive.org/services/img/{item['lending_identifier_s']}"

        published = item.get("publish_date")
        if published:
            published_dates = [date for date in map(_parse_date, published) if date]
            if published_dates:
                published = min(published_dates)

        if not published:
            published = _parse_date(str(item.get("first_publish_year")))

        content = " / ".join(item.get("first_sentence", []))
        res.add(
            res.types.Paper(
                url=f"{base_url}/{item['key']}",
                title=item["title"],
                content=content,
                isbn=item.get("isbn", [])[:5],
                authors=item.get("author_name", []),
                thumbnail=cover,
                publishedDate=published,
                tags=item.get("subject", [])[:10] + item.get("place", [])[:10],
            )
        )
    return res


def _parse_date(date: str) -> datetime | None:
    if not date:
        return None
    try:
        return parser.parse(date)
    except parser.ParserError:
        return None
