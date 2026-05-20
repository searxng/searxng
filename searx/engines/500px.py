# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=invalid-name
"""500px_ is a online network for photographers with millions of members
worldwide. Photographers come to 500px to discover and share incredible photos,
gain meaningful exposure, compete in photo contests, and license their photos
through our exclusive distribution partners.

.. _500px: https://500px.com

"""

import typing as t

import codecs
import random
import string

from searx.result_types import EngineResults

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
  }
}
"""


def setup(_) -> bool:
    global SXNG_query  # pylint: disable=global-statement
    rand_str: str = "".join(random.choice(string.ascii_letters) for _ in range(5))
    SXNG_query = SXNG_query.replace("SXNG_query", "PhotoSearchPaginationContainer_query_1" + rand_str)
    return True


def request(query: str, params: "OnlineParams") -> None:
    # cursor is the base64 hash of the string "pos-<offset-1>", e.g. "pos-29" -> "cG9zLTI5"
    offset = ((params["pageno"] - 1) * results_per_page) - 1
    cursor = codecs.encode(f"pos-{offset}".encode("utf-8"), "base64").decode("utf-8")

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

    return res
