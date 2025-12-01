# SPDX-License-Identifier: AGPL-3.0-or-later
"""Browse one of the largest collections of copyleft icons
that can be used for own projects (e.g. apps, websites).

.. _Website: https://lucide.dev

"""

import typing as t

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from extended_types import SXNG_Response
    from search.processors.online import OnlineParams


about = {
    "website": "https://lucide.dev/",
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": True,
    "results": "JSON",
}

cdn_base_url = "https://cdn.jsdelivr.net/npm/lucide-static"
categories = ["images", "icons"]


def request(query: str, params: "OnlineParams"):
    params["url"] = f"{cdn_base_url}/tags.json"
    params['query'] = query
    return params


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()
    query_parts = resp.search_params["query"].lower().split(" ")

    def is_result_match(result: tuple[str, list[str]]) -> bool:
        icon_name, tags = result

        for part in query_parts:
            if part in icon_name:
                return True

            for tag in tags:
                if part in tag:
                    return True

        return False

    filtered_results = filter(is_result_match, resp.json().items())
    for icon_name, tags in filtered_results:
        img_src = f"{cdn_base_url}/icons/{icon_name}.svg"
        res.add(
            res.types.LegacyResult(
                {
                    "template": "images.html",
                    "url": img_src,
                    "title": icon_name,
                    "content": ", ".join(tags),
                    "img_src": img_src,
                    "img_format": "SVG",
                }
            )
        )

    return res
