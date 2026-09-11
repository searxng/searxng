# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pinterest (images)"""

from json import dumps
import typing as t
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://www.pinterest.com/",
    "wikidata_id": "Q255381",
    "official_api_documentation": "https://developers.pinterest.com/docs/api/v5/",
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["images"]
paging = True

base_url = "https://www.pinterest.com"


def request(query: str, params: "OnlineParams") -> None:

    args = {
        "options": {
            "query": query,
            "bookmarks": [params["engine_data"].get("bookmark", "")],
        },
        "context": {},
    }
    params["url"] = f"{base_url}/resource/BaseSearchResource/get/?data={dumps(args)}"
    params["headers"] = {
        "X-Requested-With": "XMLHttpRequest",
        "X-Pinterest-AppState": "active",
        "X-Pinterest-Source-Url": "/ideas/",
        "X-Pinterest-PWS-Handler": "www/ideas.js",
    }


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()
    json_resp: dict[str, t.Any] = resp.json()  # type: ignore

    res.add(
        {
            "engine_data": json_resp["resource_response"]["bookmark"],
            # it's called bookmark by pinterest, but it's rather a nextpage
            # parameter to get the next results
            "key": "bookmark",
        }
    )

    for result in json_resp["resource_response"]["data"]["results"]:

        if result["type"] == "story":
            continue

        main_image = result["images"]["orig"]

        title = result.get("title") or result.get("grid_title") or ""
        if len(title) < 5:
            visual_annotation = result.get("pin_join", {}).get("visual_annotation")
            if visual_annotation:
                title = visual_annotation[0]
            else:
                title = result.get("name") or result.get("auto_alt_text") or ""

        res.add(
            res.types.Image(
                url=result.get("link") or f"{base_url}/pin/{result['id']}/",
                title=title,
                content=(result.get("rich_summary") or {}).get("display_description") or "",
                img_src=main_image["url"],
                thumbnail_src=result["images"]["236x"]["url"],
                source=(result.get("rich_summary") or {}).get("site_name") or "",
                resolution=f"{main_image['width']}x{main_image['height']}",
                author=f"{result['pinner'].get('full_name')} ({result['pinner']['username']})",
            )
        )

    return res
