# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=invalid-name
"""500px_ is a online network for photographers with millions of members
worldwide. Photographers come to 500px to discover and share incredible photos,
gain meaningful exposure, compete in photo contests, and license their photos
through our exclusive distribution partners.

.. _500px: https://500px.com

"""

import typing as t

import random
import string

from searx.result_types import EngineResults
from searx.enginelib import EngineCache

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


# about
about = {
    "website": "https://500px.com",
    "wikidata_id": "Q354894",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

base_url = "https://500px.com"
api_url = "https://api.500px.com"

categories = ["images"]

paging = True
results_per_page = 30
"""Number of results to return in the request.

The default was taken from the WEB UI, where the GraphQL query sets the value to
*static*: ``first: 30``.
"""


def page_hash(pageno: int, query: str):
    return f"<pageno:{pageno} ({results_per_page})>" + CACHE.secret_hash(query)


CACHE: EngineCache
"""Persistent (SQLite) key/value cache that deletes its values after ``expire``
seconds.

For introspection (in the developer environment) use::

    $ ./manage dev.env
    (dev.env)$ python -m searx.enginelib cache status
    ...
    [eng_500px] 2026-05-18 18:52:38 <pageno:2 (40)>6da7...76a3f7 --> (str:8) cG9zLTM5
    [eng_500px] 2026-05-18 18:52:43 <pageno:3 (40)>6da7...76a3f7 --> (str:8) cG9zLTc5

In the output from the example above, we see cached *cursor* for follow up
pages, the query term is a hash value and the date shows the expire date and
time."""


SXNG_query = """query PhotoSearchPaginationContainerQuery(
    $first: Int, $cursor: String, $search: String!, $sort: PhotoSort, $filters: [PhotoSearchFilter!], $nlp: Boolean
) {
  ...SXNG_query
}

fragment SXNG_query on Query {
  photoSearch(sort: $sort, first: $first, after: $cursor, search: $search, filters: $filters, nlp: $nlp) {
    edges {
      node {
        id
        canonicalPath
        name
        description
        width
        height
        photographer: uploader {
          displayName
        }
        images(sizes: [35, 33]) {
          size
          url
          jpegUrl
          webpUrl
          id
        }
      }
      cursor
    }
    pageInfo {
      endCursor
      hasNextPage
    }
  }
}
"""


def setup(engine_settings: dict[str, t.Any]) -> bool:
    global CACHE, SXNG_query  # pylint: disable=global-statement
    CACHE = EngineCache(str(engine_settings.get("name")))
    rand_str: str = "".join(random.choice(string.ascii_letters) for _ in range(5))
    SXNG_query = SXNG_query.replace("SXNG_query", "PhotoSearchPaginationContainer_query_1" + rand_str)
    return True


def request(query: str, params: "OnlineParams") -> None:

    cursor: str | None = None
    if params["pageno"] > 1:
        cursor = CACHE.get(page_hash(pageno=params["pageno"], query=query))
        if not cursor:
            params["url"] = None
            return

    params["url"] = f"{api_url}/graphql"
    params["method"] = "POST"
    params["json"] = {
        "operationName": "PhotoSearchPaginationContainerQuery",
        "variables": {
            "first": results_per_page,
            "cursor": cursor,
            "search": query,
            "sort": "RELEVANCE",
            "filters": [],
            "nlp": False,
        },
        "query": SXNG_query,
    }


def response(resp: "SXNG_Response"):
    res = EngineResults()
    json_data = resp.json()["data"]["photoSearch"]

    for edge in json_data["edges"]:
        node = edge["node"]  # pyright: ignore[reportAny]
        if not node["images"]:
            continue
        images: list[dict[str, str]] = sorted(node["images"], key=lambda i: i["size"])
        thumbnail_src = images[0]["url"]
        img_src = images[-1]["url"]
        res.add(
            res.types.LegacyResult(
                {
                    "template": "images.html",
                    "url": base_url + node["canonicalPath"],
                    "thumbnail_src": thumbnail_src,
                    "img_src": img_src,
                    "title": node["name"],
                    "content": node["description"],
                    "author": node["photographer"]["displayName"],
                    "resolution": f"{node['width']}x{node['height']}",
                }
            )
        )

    page_info: dict[str, str] = json_data["pageInfo"]  # pyright: ignore[reportAny]
    if page_info["hasNextPage"]:
        key = page_hash(pageno=resp.search_params["pageno"] + 1, query=resp.search_params["query"])
        CACHE.set(key=key, value=page_info["endCursor"], expire=3600)

    return res
