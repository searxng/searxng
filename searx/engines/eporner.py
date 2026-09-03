# SPDX-License-Identifier: AGPL-3.0-or-later
"""Eporner_ is one of the largest adult video tubes (18+ content).  This engine
queries the public `API v2`_ which does not require an API key.

.. _Eporner: https://www.eporner.com
.. _API v2: https://www.eporner.com/api/v2/

"""

from datetime import datetime, timezone
from urllib.parse import urlencode

from searx.utils import html_to_text

about = {
    "website": "https://www.eporner.com",
    "wikidata_id": None,
    "official_api_documentation": "https://www.eporner.com/api/v2/",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

# engine dependent config
categories = ["adult"]
paging = True
safesearch = False
"""The API does not support a safesearch flag."""

base_url = "https://www.eporner.com"
search_url = base_url + "/api/v2/video/search/"

results_per_page = 20
"""Number of videos per page, valid range is 1..1000."""

thumb_size = "big"
"""Thumbnail size: ``small`` (190x152), ``medium`` (427x240) or ``big`` (640x360)."""

order = "most-popular"
"""Result order: ``latest``, ``longest``, ``shortest``, ``top-rated``,
``most-popular``, ``top-weekly`` or ``top-monthly``."""

gay_content = 1
"""Include gay content: ``0`` exclude, ``1`` include, ``2`` only gay content."""

low_quality = 1
"""Include low quality content: ``0`` exclude, ``1`` include, ``2`` only low quality."""


def request(query, params):
    args = {
        "query": query,
        "per_page": results_per_page,
        "page": params["pageno"],
        "thumbsize": thumb_size,
        "order": order,
        "gay": gay_content,
        "lq": low_quality,
        "format": "json",
    }
    params["url"] = f"{search_url}?{urlencode(args)}"
    return params


def response(resp):
    results = []

    data = resp.json()
    for video in data.get("videos") or []:
        results.append(
            {
                "template": "videos.html",
                "url": video["url"],
                "title": video["title"],
                "content": html_to_text(video.get("keywords") or ""),
                "thumbnail": video.get("default_thumb", {}).get("src"),
                "iframe_src": video.get("embed"),
                "length": video.get("length_min"),
                "views": video.get("views"),
                "publishedDate": _parse_date(video.get("added")),
            }
        )

    return results


def _parse_date(date_str):
    """Convert ``YYYY-MM-DD HH:MM:SS`` (UTC) into a timezone aware datetime.

    Missing dates are reported by the API as epoch (``1970-01-01 ..``),
    those and invalid values give ``None``.
    """
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    if dt.year <= 1970:
        return None
    return dt
