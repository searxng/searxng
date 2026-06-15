# SPDX-License-Identifier: AGPL-3.0-or-later
"""Icons8_ is a database for icons."""

from urllib.parse import urlencode

import typing as t

from searx.result_types import EngineResults, ImageRef
from searx.network import multi_requests, Request

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://icons8.com",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

base_url = "https://icons8.com"
api_url = "https://search-app.icons8.com"
cdn_url = "https://img.icons8.com"

categories = ["images", "icons"]
paging = True

fetch_svg = False
"""
Whether to additionally load the full resolution SVG icon. This does one request
per icon, so be aware that this might be very slow and the engine timeout should
be increased.
"""

results_per_page = 20


def request(query: str, params: "OnlineParams") -> None:
    args = {
        "amount": results_per_page,
        "offset": (params["pageno"] - 1) * results_per_page,
        "term": query,
    }
    params["url"] = f"{api_url}/api/iconsets/v7/search?{urlencode(args)}"


def _fetch_svgs(ids: list[str]) -> dict[str, str]:
    responses = multi_requests(
        [
            Request.get(
                f"https://api-icons.icons8.com/siteApi/icons/icon?id={id}&svg=true",
            )
            for id in ids
        ]
    )

    svgs = {}
    for i, resp in enumerate(responses):
        if isinstance(resp, Exception):
            continue

        # the image is a base64 encoded SVG, so we can display it
        # as data:image
        b64_svg = resp.json()["icon"]["svg"]
        svgs[ids[i]] = f"data:image/svg+xml;base64,{b64_svg}"

    return svgs


# any very big resolution will give us the max-res image
def _get_image_url(result: dict[str, t.Any], img_format: str, resolution: int = 10000) -> str:
    return f"{cdn_url}/{result['platform']}/{resolution}/{result['commonName']}.{img_format}"


def response(resp: "SXNG_Response"):
    res = EngineResults()
    icons = resp.json()["icons"]

    svgs = {}
    if fetch_svg:
        svgs = _fetch_svgs(list(icon["id"] for icon in icons))

    for result in icons:
        result: dict[str, t.Any]

        extra_formats = [
            ImageRef(
                url=_get_image_url(result, "png"),
                subtype="png",
            ),
            ImageRef(
                url=_get_image_url(result, "jpg"),
                subtype="jpeg",
            ),
        ]
        if result["id"] in svgs:
            img_url = thumbnail_url = svgs[result["id"]]
            default_format = "SVG"
        else:
            img_url = extra_formats.pop(0).url
            thumbnail_url = _get_image_url(result, "png", resolution=512)
            default_format = "JPEG"

        res.add(
            res.types.Image(
                url=f"{base_url}/icon/{result['id']}/{result['commonName']}",
                thumbnail_src=thumbnail_url,
                img_src=img_url,
                title=result["name"],
                content=result.get("subcategory") or "",
                img_format=default_format,
                formats=extra_formats,
            )
        )

    return res
