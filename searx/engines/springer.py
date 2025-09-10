# SPDX-License-Identifier: AGPL-3.0-or-later
"""`Springer Nature`_ is a global publisher dedicated to providing service to
research community with official Springer-API_ (API-Playground_).

.. note::

   The Springer engine requires an API key, which can be obtained via the
   `Springer subscription`_.

Since the search term is passed 1:1 to the API, SearXNG users can use the
`Supported Query Parameters`_.

- ``!springer (doi:10.1007/s10948-025-07019-1 OR doi:10.1007/s10948-025-07035-1)``
- ``!springer keyword:ybco``

However, please note that the available options depend on the subscription type.

For example, the ``year:`` filter requires a *Premium Plan* subscription.

- ``!springer keyword:ybco year:2024``

The engine uses the REST Meta-API_ `v2` endpoint, but there is also a `Python
API Wrapper`_.

.. _Python API Wrapper: https://pypi.org/project/springernature-api-client/
.. _Springer Nature: https://www.springernature.com/
.. _Springer subscription:  https://dev.springernature.com/subscription/
.. _Springer-API: https://dev.springernature.com/docs/introduction/
.. _API-Playground: https://dev.springernature.com/docs/live-documentation/
.. _Meta-API: https://dev.springernature.com/docs/api-endpoints/meta-api/
.. _Supported Query Parameters: https://dev.springernature.com/docs/supported-query-params/


Configuration
=============

The engine has the following additional settings:

- :py:obj:`api_key`

.. code:: yaml

  - name: springer nature
    api_key: "..."
    inactive: false


Implementations
===============

"""

import typing as t

from datetime import datetime
from urllib.parse import urlencode

from searx.network import raise_for_httperror
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://www.springernature.com/",
    "wikidata_id": "Q21096327",
    "official_api_documentation": "https://dev.springernature.com/docs/live-documentation/",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

categories = ["science", "scientific publications"]

paging = True
nb_per_page = 10
"""Number of results to return in the request, see `Pagination and Limits`_ for
more details.

.. _Pagination and Limits:
    https://dev.springernature.com/docs/advanced-querying/pagination-limits/
"""

api_key = ""
"""Key used for the Meta-API_.  Get your API key from: `Springer subscription`_"""

base_url = "https://api.springernature.com/meta/v2/json"
"""An enhanced endpoint with additional metadata fields and optimized queries
for more efficient and comprehensive retrieval (Meta-API_ `v2`).
"""


def setup(engine_settings: dict[str, t.Any]) -> bool:
    """Initialization of the Springer engine, checks whether the
    :py:obj:`api_key` is set, otherwise the engine is inactive.
    """
    key: str = engine_settings.get("api_key", "")
    try:
        # Springer's API key is a hex value
        int(key, 16)
        return True
    except ValueError:
        logger.error("Springer's API key is not set or invalid.")
        return False


def request(query: str, params: "OnlineParams") -> None:
    args = {
        "api_key": api_key,
        "q": query,
        "s": nb_per_page * (params["pageno"] - 1),
        "p": nb_per_page,
    }
    params["url"] = f"{base_url}?{urlencode(args)}"
    # For example, the ``year:`` filter requires a *Premium Plan* subscription.
    params["raise_for_httperror"] = False


def response(resp: "SXNG_Response") -> EngineResults:

    res = EngineResults()
    json_data = resp.json()

    if (
        resp.status_code == 403
        and json_data["status"].lower() == "fail"
        and "premium feature" in json_data["message"].lower()
    ):
        return res
    raise_for_httperror(resp)

    def field(k: str) -> str:
        return str(record.get(k, ""))

    for record in json_data["records"]:
        published = datetime.strptime(record["publicationDate"], "%Y-%m-%d")
        authors: list[str] = [" ".join(author["creator"].split(", ")[::-1]) for author in record["creators"]]

        pdf_url = ""
        html_url = ""
        url_list: list[dict[str, str]] = record["url"]

        for item in url_list:
            if item["platform"] != "web":
                continue
            val = item["value"].replace("http://", "https://", 1)
            if item["format"] == "html":
                html_url = val
            elif item["format"] == "pdf":
                pdf_url = val

        paper = res.types.Paper(
            url=html_url,
            # html_url=html_url,
            pdf_url=pdf_url,
            title=field("title"),
            content=field("abstract"),
            comments=field("publicationName"),
            tags=record.get("keyword", []),
            publishedDate=published,
            type=field("contentType"),
            authors=authors,
            publisher=field("publisher"),
            journal=field("publicationName"),
            volume=field("volume"),
            pages="-".join([x for x in [field("startingPage"), field("endingPage")] if x]),
            number=field("number"),
            doi=field("doi"),
            issn=[x for x in [field("issn")] if x],
            isbn=[x for x in [field("isbn")] if x],
        )
        res.add(paper)

    return res
