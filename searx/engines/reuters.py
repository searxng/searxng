# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reuters_ (news) is an international news agency.

.. _Reuters: https://www.reuters.com

Configuration
=============

The engine has the following additional settings:

- :py:obj:`sort_order`

.. code:: yaml

   - name: reuters
     engine: reuters
     shortcut: reu
     sort_order: "relevance"

Implementations
===============

"""

from json import dumps
from urllib.parse import quote_plus
from datetime import datetime, timedelta
from dateutil import parser

from searx.result_types import EngineResults

about = {
    "website": "https://www.reuters.com",
    "wikidata_id": "Q130879",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["news"]
time_range_support = True
paging = True

base_url = "https://www.reuters.com"

results_per_page = 20
sort_order = "relevance"
"""Sort order, one of ``relevance``, ``display_date:desc`` or ``display_data:asc``."""

time_range_duration_map = {
    "day": 1,
    "week": 7,
    "month": 30,
    "year": 365,
}


def request(query, params):
    args = {
        "keyword": query,
        "offset": (params["pageno"] - 1) * results_per_page,
        "orderby": sort_order,
        "size": results_per_page,
        "website": "reuters",
    }
    if params["time_range"]:
        time_diff_days = time_range_duration_map[params["time_range"]]
        start_date = datetime.now() - timedelta(days=time_diff_days)
        args["start_date"] = start_date.isoformat()

    params["url"] = f"{base_url}/pf/api/v3/content/fetch/articles-by-search-v2?query={quote_plus(dumps(args))}"
    return params


def response(resp) -> EngineResults:
    res = EngineResults()

    resp_json = resp.json()
    if not resp_json.get("result"):
        return res

    for result in resp_json["result"].get("articles", []):
        res.add(
            res.types.MainResult(
                url=base_url + result["canonical_url"],
                title=result["web"],
                content=result["description"],
                thumbnail=resize_url(result.get("thumbnail", {}), height=80),
                metadata=result.get("kicker", {}).get("name"),
                publishedDate=parser.isoparse(result["display_time"]),
            )
        )
    return res


def resize_url(thumbnail: dict[str, str], width: int = 0, height: int = 0) -> str:
    """Generates a URL for Reuter's thumbnail with the dimensions *width* and
    *height*.  If no URL can be generated from the *thumbnail data*, an empty
    string will be returned.

    width: default is *unset* (``0``)
      Image width in pixels (negative values are ignored). If only width is
      specified, the height matches the original aspect ratio.

    height: default is *unset* (``0``)
      Image height in pixels (negative values are ignored). If only height is
      specified, the width matches the original aspect ratio.

    The file size of a full-size image is usually several MB; when reduced to a
    height of, for example, 80 points, only a few KB remain!

    Fields of the *thumbnail data* (``result.articles.[<int>].thumbnail``):

    thumbnail.url:
      Is a full-size image (>MB).

    thumbnail.width & .height:
      Dimensions of the full-size image.

    thumbnail.resizer_url:
      Reuters has a *resizer* `REST-API for the images`_, this is the URL of the
      service. This URL includes the ``&auth`` argument, other arguments are
      ``&width=<int>`` and ``&height=<int>``.

    .. _REST-API for the images:
        https://dev.arcxp.com/photo-center/image-resizer/resizer-v2-how-to-transform-images/#query-parameters
    """

    url = thumbnail.get("resizer_url")
    if not url:
        return ""
    if int(width) > 0:
        url += f"&width={int(width)}"
    if int(height) > 0:
        url += f"&height={int(height)}"
    return url
