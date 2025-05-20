# SPDX-License-Identifier: AGPL-3.0-or-later
"""`Adobe Stock`_ is a service that gives access to millions of royalty-free
assets. Assets types include photos, vectors, illustrations, templates, 3D
assets, videos, motion graphics templates and audio tracks.

.. Adobe Stock: https://stock.adobe.com/

Configuration
=============

The engine has the following mandatory setting:

- SearXNG's :ref:`engine categories`
- Adobe-Stock's :py:obj:`adobe_order`
- Adobe-Stock's :py:obj:`adobe_content_types`

.. code:: yaml

  - name: adobe stock
    engine: adobe_stock
    shortcut: asi
    categories: [images]
    adobe_order: relevance
    adobe_content_types: ["photo", "illustration", "zip_vector", "template", "3d", "image"]

  - name: adobe stock video
    engine: adobe_stock
    network: adobe stock
    shortcut: asi
    categories: [videos]
    adobe_order: relevance
    adobe_content_types: ["video"]

Implementation
==============

"""
from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import datetime, timedelta
from urllib.parse import urlencode

import isodate

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

about = {
    "website": "https://stock.adobe.com/",
    "wikidata_id": "Q5977430",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

categories = []
paging = True
send_accept_language_header = True
results_per_page = 10

base_url = "https://stock.adobe.com"

adobe_order: str = ""
"""Sort order, can be one of:

- ``relevance`` or
- ``featured`` or
- ``creation`` (most recent) or
- ``nb_downloads`` (number of downloads)
"""

ADOBE_VALID_TYPES = ["photo", "illustration", "zip_vector", "video", "template", "3d", "audio", "image"]
adobe_content_types: list = []
"""A list of of content types.  The following content types are offered:

- Images: ``image``
- Videos: ``video``
- Templates: ``template``
- 3D: ``3d``
- Audio ``audio``

Additional subcategories:

- Photos: ``photo``
- Illustrations: ``illustration``
- Vectors: ``zip_vector`` (Vectors),
"""

# Do we need support for "free_collection" and "include_stock_enterprise"?


def init(_):
    if not categories:
        raise ValueError("adobe_stock engine: categories is unset")

    # adobe_order
    if not adobe_order:
        raise ValueError("adobe_stock engine: adobe_order is unset")
    if adobe_order not in ["relevance", "featured", "creation", "nb_downloads"]:
        raise ValueError(f"unsupported adobe_order: {adobe_order}")

    # adobe_content_types
    if not adobe_content_types:
        raise ValueError("adobe_stock engine: adobe_content_types is unset")

    if isinstance(adobe_content_types, list):
        for t in adobe_content_types:
            if t not in ADOBE_VALID_TYPES:
                raise ValueError("adobe_stock engine: adobe_content_types: '%s' is invalid" % t)
    else:
        raise ValueError(
            "adobe_stock engine: adobe_content_types must be a list of strings not %s" % type(adobe_content_types)
        )


def request(query, params):

    args = {
        "k": query,
        "limit": results_per_page,
        "order": adobe_order,
        "search_page": params["pageno"],
        "search_type": "pagination",
    }

    for content_type in ADOBE_VALID_TYPES:
        args[f"filters[content_type:{content_type}]"] = 1 if content_type in adobe_content_types else 0

    params["url"] = f"{base_url}/de/Ajax/Search?{urlencode(args)}"

    # headers required to bypass bot-detection
    if params["searxng_locale"] == "all":
        params["headers"]["Accept-Language"] = "en-US,en;q=0.5"

    return params


def parse_image_item(item):
    return {
        "template": "images.html",
        "url": item["content_url"],
        "title": item["title"],
        "content": item["asset_type"],
        "img_src": item["content_thumb_extra_large_url"],
        "thumbnail_src": item["thumbnail_url"],
        "resolution": f"{item['content_original_width']}x{item['content_original_height']}",
        "img_format": item["format"],
        "author": item["author"],
    }


def parse_video_item(item):

    # in video items, the title is more or less a "content description", we try
    # to reduce the length of the title ..

    title = item["title"]
    content = ""
    if "." in title.strip()[:-1]:
        content = title
        title = title.split(".", 1)[0]
    elif "," in title:
        content = title
        title = title.split(",", 1)[0]
    elif len(title) > 50:
        content = title
        title = ""
        for w in content.split(" "):
            title += f" {w}"
            if len(title) > 50:
                title = title.strip() + "\u2026"
                break

    return {
        "template": "videos.html",
        "url": item["content_url"],
        "title": title,
        "content": content,
        # https://en.wikipedia.org/wiki/ISO_8601#Durations
        "length": isodate.parse_duration(item["time_duration"]),
        "publishedDate": datetime.fromisoformat(item["creation_date"]),
        "thumbnail": item["thumbnail_url"],
        "iframe_src": item["video_small_preview_url"],
        "metadata": item["asset_type"],
    }


def parse_audio_item(item):
    audio_data = item["audio_data"]
    content = audio_data.get("description") or ""
    if audio_data.get("album"):
        content = audio_data["album"] + " - " + content

    return {
        "url": item["content_url"],
        "title": item["title"],
        "content": content,
        # "thumbnail": base_url + item["thumbnail_url"],
        "iframe_src": audio_data["preview"]["url"],
        "publishedDate": datetime.fromisoformat(audio_data["release_date"]) if audio_data["release_date"] else None,
        "length": timedelta(seconds=round(audio_data["duration"] / 1000)) if audio_data["duration"] else None,
        "author": item.get("artist_name"),
    }


def response(resp):
    results = []

    json_resp = resp.json()

    if isinstance(json_resp["items"], list):
        return None
    for item in json_resp["items"].values():
        if item["asset_type"].lower() in ["image", "premium-image", "illustration", "vector"]:
            result = parse_image_item(item)
        elif item["asset_type"].lower() == "video":
            result = parse_video_item(item)
        elif item["asset_type"].lower() == "audio":
            result = parse_audio_item(item)
        else:
            logger.error("no handle for %s --> %s", item["asset_type"], item)
            continue
        results.append(result)

    return results
