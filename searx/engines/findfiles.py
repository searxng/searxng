# SPDX-License-Identifier: AGPL-3.0-or-later
"""FindFiles.net_ is a Germany-based file search engine.

FindFiles.net_ is a specialized file search engine designed to help you search
files online with precision. Unlike traditional search engines that mainly index
web pages, FindFiles focuses on finding real files on the internet - including
PDFs, documents, archives, videos, datasets, and more.

.. _FindFiles.net: https://findfiles.net
"""

from os.path import basename
from urllib.parse import urlencode
import typing as t

from lxml import html

from searx.result_types import EngineResults
from searx.utils import extract_text, eval_xpath, eval_xpath_list

if t.TYPE_CHECKING:
    from extended_types import SXNG_Response
    from search.processors import OnlineParams

about = {
    "website": "https://findfiles.net",
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

base_url = "https://findfiles.net"
categories = ["files"]
paging = True
safeserach = True

safesearch_map = {
    0: "contentguard.off",
    1: "contentguard.moderate",
    2: "contentguard.strict",
}

FindFilesCategory = t.Literal[
    "all",
    "document",
    "text",
    "image",
    "audio",
    "video",
]
FINDFILES_CATEGORIES = t.get_args(FindFilesCategory)

findfiles_categ: FindFilesCategory = "all"
"""Category to search in."""


def setup(_: dict[str, t.Any]) -> bool:
    if findfiles_categ not in FINDFILES_CATEGORIES:
        raise ValueError("invalid category: %s" % findfiles_categ)
    return True


def request(query: str, params: "OnlineParams") -> None:
    args = {
        "query": query,
        "contentguard": safesearch_map[params["safesearch"]],
        "page": params["pageno"],
    }
    # the language in the path doesn't change anything about the results, it
    # only changes the UI
    params["url"] = f"{base_url}/en/serp/{findfiles_categ}/?{urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    dom = html.fromstring(resp.text)
    if findfiles_categ == "image":
        for result in eval_xpath_list(
            dom, "//div[contains(@class, 'image-mosaic')]/div[contains(@class, 'image-item')]"
        ):
            res.add(
                res.types.Image(
                    url=extract_text(eval_xpath(result, ".//div[contains(@class, 'caption')]/a/@href")) or "",
                    title=extract_text(eval_xpath(result, ".//div[contains(@class, 'caption')]/a")) or "",
                    thumbnail_src=extract_text(eval_xpath(result, ".//img/@src")) or "",
                )
            )
    elif findfiles_categ == "video":
        for result in eval_xpath_list(
            dom, "//div[contains(@class, 'video-mosaic')]/div[contains(@class, 'video-item')]"
        ):
            video_src = extract_text(eval_xpath(result, ".//video/@src")) or ""
            res.add(
                res.types.LegacyResult(
                    template="videos.html",
                    url=video_src,
                    title=extract_text(eval_xpath(result, ".//div[contains(@class, 'caption')]/span")) or "",
                    iframe_src=video_src or "",
                )
            )
    else:
        for result in eval_xpath_list(dom, "//ol/li[contains(@class, 'result-item')]/article"):
            filename = basename(extract_text(eval_xpath(result, ".//h3")) or "")
            res.add(
                res.types.File(
                    url=extract_text(eval_xpath(result, ".//h3/a/@href")) or "",
                    title=filename,
                    content=" ".join(extract_text(el) or "" for el in eval_xpath_list(result, "./div/span")),
                    filename=filename,
                    size=extract_text(eval_xpath(result, "(.//span[@id])[1]")) or "",
                    embedded=extract_text(eval_xpath(result, ".//audio/@src")) or "",
                )
            )

    return res
