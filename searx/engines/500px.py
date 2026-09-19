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
api_url = "https://api-neo.500px.com"

categories = ["stock images"]
paging = True

results_per_page = 30
"""Number of results to return in the request.

The default was taken from the WEB UI, where the GraphQL query sets the value to
*static*: ``first: 30``.
"""


SXNG_query = """
query searchResource(
  $keyword: String!
  $type: SearchType = TEXT
  $first: Int!
  $after: String
  $resourceTypes: [SearchResourceType!]
  $categories: [String!]
  $equipments: [String!]
  $downloadable: PhotoDownloadable
  $sort: SearchSortOption = RELEVANCE
  $excludeNsfw: Boolean
) {
  searchResource(
    keyword: $keyword
    type: $type
    first: $first
    after: $after
    resourceTypes: $resourceTypes
    categories: $categories
    equipments: $equipments
    downloadable: $downloadable
    sort: $sort
    excludeNsfw: $excludeNsfw
  ) {
    edges {
      cursor
      node {
        __typename
        ... on Photo {
          id
          title
          description
          licensing {
            status
            __typename
          }
          urls {
            size_600
            size_1024
            size_2048
            size_4k
            __typename
          }
          uploader {
            displayName
            __typename
          }
          isNsfw
          width
          height
          dominantColorLight
          dominantColorDark
          uploadedAt
          __typename
        }
      }
      __typename
    }
    __typename
  }
}
"""


def request(query: str, params: "OnlineParams") -> None:
    # cursor is the base64 hash of the string "pos-<offset-1>", e.g. "pos-29" -> "cG9zLTI5"
    offset = ((params["pageno"] - 1) * results_per_page) - 1
    cursor = codecs.encode(f"pos-{offset}".encode("utf-8"), "base64").decode("utf-8")

    params["url"] = f"{api_url}/graphql"
    params["method"] = "POST"
    params["json"] = {
        "operationName": "searchResource",
        "variables": {
            "after": cursor,
            "first": results_per_page,
            "keyword": query,
            "resourceTypes": ["PHOTO"],
            "sort": "RELEVANCE",
            "type": "TEXT",
        },
        "query": SXNG_query,
    }


def response(resp: "SXNG_Response"):
    res = EngineResults()
    json_data = resp.json()["data"]["searchResource"]

    for edge in json_data["edges"]:
        node = edge["node"]  # pyright: ignore[reportAny]
        image_urls = [url for (resolution, url) in node["urls"].items() if resolution.startswith("size_")]
        res.add(
            res.types.Image(
                url=f"{base_url}/photo/{node['id']}",
                thumbnail_src=image_urls[0],
                img_src=image_urls[-1],
                title=node["title"],
                content=node["description"] or "",
                author=node["uploader"]["displayName"],
                resolution=f"{node['width']}x{node['height']}",
            )
        )

    return res
