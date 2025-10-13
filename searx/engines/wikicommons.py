# SPDX-License-Identifier: AGPL-3.0-or-later
"""`Wikimedia Commons`_ is a collection of more than 120 millions freely usable
media files to which anyone can contribute.

This engine uses the `MediaWiki query API`_, with which engines can be configured
for searching images, videos, audio, and other files in the Wikimedia.

.. _MediaWiki query API: https://commons.wikimedia.org/w/api.php?action=help&modules=query
.. _Wikimedia Commons: https://commons.wikimedia.org/


Configuration
=============

The engine has the following additional settings:

.. code:: yaml

   - name: wikicommons.images
     engine: wikicommons
     wc_search_type: image

   - name: wikicommons.videos
     engine: wikicommons
     wc_search_type: video

   - name: wikicommons.audio
     engine: wikicommons
     wc_search_type: audio

   - name: wikicommons.files
     engine: wikicommons
     wc_search_type: file


Implementations
===============

"""

import typing as t

import datetime
import pathlib
from urllib.parse import urlencode, unquote

from searx.utils import html_to_text, humanize_bytes
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://commons.wikimedia.org/",
    "wikidata_id": "Q565",
    "official_api_documentation": "https://commons.wikimedia.org/w/api.php",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories: list[str] = []
paging = True
number_of_results = 10

wc_api_url = "https://commons.wikimedia.org/w/api.php"
wc_search_type: str = ""

SEARCH_TYPES: dict[str, str] = {
    "image": "bitmap|drawing",
    "video": "video",
    "audio": "audio",
    "file": "multimedia|office|archive|3d",
}
# FileType = t.Literal["bitmap", "drawing", "video", "audio", "multimedia", "office", "archive", "3d"]
# FILE_TYPES = list(t.get_args(FileType))


def setup(engine_settings: dict[str, t.Any]) -> bool:
    """Initialization of the Wikimedia engine, checks if the value configured in
    :py:obj:`wc_search_type` is valid."""

    if engine_settings.get("wc_search_type") not in SEARCH_TYPES:
        logger.error(
            "wc_search_type: %s isn't a valid file type (%s)",
            engine_settings.get("wc_search_type"),
            ",".join(SEARCH_TYPES.keys()),
        )
        return False
    return True


def request(query: str, params: "OnlineParams") -> None:
    uselang: str = "en"
    if params["searxng_locale"] != "all":
        uselang = params["searxng_locale"].split("-")[0]
    filetype = SEARCH_TYPES[wc_search_type]
    args = {
        # https://commons.wikimedia.org/w/api.php
        "format": "json",
        "uselang": uselang,
        "action": "query",
        # https://commons.wikimedia.org/w/api.php?action=help&modules=query
        "prop": "info|imageinfo",
        # generator (gsr optins) https://commons.wikimedia.org/w/api.php?action=help&modules=query%2Bsearch
        "generator": "search",
        "gsrnamespace": "6",  # https://www.mediawiki.org/wiki/Help:Namespaces#Renaming_namespaces
        "gsrprop": "snippet",
        "gsrlimit": number_of_results,
        "gsroffset": number_of_results * (params["pageno"] - 1),
        "gsrsearch": f"filetype:{filetype} {query}",
        # imageinfo: https://commons.wikimedia.org/w/api.php?action=help&modules=query%2Bimageinfo
        "iiprop": "url|size|mime",
        "iiurlheight": "180",  # needed for the thumb url
    }
    params["url"] = f"{wc_api_url}?{urlencode(args, safe=':|')}"


def response(resp: "SXNG_Response") -> EngineResults:

    res = EngineResults()
    json_data = resp.json()
    pages = json_data.get("query", {}).get("pages", {}).values()

    for item in pages:

        if not item.get("imageinfo", []):
            continue
        imageinfo = item["imageinfo"][0]

        title: str = item["title"].replace("File:", "").rsplit(".", 1)[0]
        content = html_to_text(item["snippet"])

        url: str = imageinfo["descriptionurl"]
        media_url: str = imageinfo["url"]
        mimetype: str = imageinfo["mime"]
        thumbnail: str = imageinfo["thumburl"]
        size = imageinfo.get("size")
        if size:
            size = humanize_bytes(size)

        duration = None
        seconds: str = imageinfo.get("duration")
        if seconds:
            try:
                duration = datetime.timedelta(seconds=int(seconds))
            except OverflowError:
                pass

        if wc_search_type == "file":
            res.add(
                res.types.File(
                    title=title,
                    url=url,
                    content=content,
                    size=size,
                    mimetype=mimetype,
                    filename=unquote(pathlib.Path(media_url).name),
                    embedded=media_url,
                    thumbnail=thumbnail,
                )
            )
            continue

        if wc_search_type == "image":
            res.add(
                res.types.LegacyResult(
                    template="images.html",
                    title=title,
                    url=url,
                    content=content,
                    img_src=imageinfo["url"],
                    thumbnail_src=thumbnail,
                    resolution=f"{imageinfo['width']} x {imageinfo['height']}",
                    img_format=imageinfo["mime"],
                    filesize=size,
                )
            )
            continue

        if wc_search_type == "video":
            res.add(
                res.types.LegacyResult(
                    template="videos.html",
                    title=title,
                    url=url,
                    content=content,
                    iframe_src=media_url,
                    length=duration,
                )
            )
            continue

        if wc_search_type == "audio":
            res.add(
                res.types.MainResult(
                    template="default.html",
                    title=title,
                    url=url,
                    content=content,
                    audio_src=media_url,
                    length=duration,
                )
            )
            continue

    return res
