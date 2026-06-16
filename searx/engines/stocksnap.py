# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stocksnap_ is a search engine for CC0-licensed images.

.. _Stocksnap: https://stocksnap.io
"""

import typing as t

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://stocksnap.io",
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}
# otherwise all requests get blocked, probably HTTP2 fingerprinting
enable_http2 = False

base_url = "https://stocksnap.io"
cdn_url = "https://cdn.stocksnap.io"

categories = ["images"]
paging = True


def request(query: str, params: "OnlineParams") -> None:
    params["url"] = f"{base_url}/api/search-photos/{query}/relevance/desc/{params['pageno']}"


def response(resp: "SXNG_Response"):
    res = EngineResults()

    result: dict[str, str]  # TBH: dict[str, t.Any]
    for result in resp.json()["results"]:
        slug = "-".join(result['keywords'][:1]) + "-" + result["img_id"]
        res.add(
            res.types.Image(
                title=result["tags"],
                url=f"{base_url}/photo/{slug}",
                thumbnail_src=f"{cdn_url}/img-thumbs/280h/{result['img_id']}.jpg",
                img_src=f"{cdn_url}/img-thumbs/960w/{result['img_id']}.jpg",
                img_format="JPEG",
                resolution=f"{result['img_width']}x{result['img_height']}",
            )
        )

    return res
