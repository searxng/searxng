# SPDX-License-Identifier: AGPL-3.0-or-later
"""Vuhuv_ is a Turkish search engine, that also provides English results.

.. _Vuhuv : https://vuhuv.com
"""

import typing as t
from urllib.parse import urlencode

from lxml import html

from searx.result_types import EngineResults
from searx.utils import eval_xpath_list, eval_xpath, extract_text


if t.TYPE_CHECKING:
    from lxml.etree import ElementBase
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://vuhuv.com",
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

paging = True

base_url = "https://vuhuv.com"
vuhuv_category = "general"
"""Supported categories are ``general``, ``videos`` and ``images``."""


# corresponds to the "k" query param
category_map = {"general": 1, "images": 2, "videos": 3}


def init(_):
    if vuhuv_category not in category_map:
        raise ValueError("invalid category: %s" % vuhuv_category)


def request(query: str, params: "OnlineParams") -> None:
    # the purpose of "d" and "dh" are unknown, but the website
    # sends them, and without them the results are different
    args = {"k": category_map[vuhuv_category], "p": params["pageno"], "q": query, "d": 1, "dh": 1}
    params["url"] = f"{base_url}/veri2/?{urlencode(args)}"
    params["headers"]["Referer"] = f"{base_url}/"


def _general_results(doc: "ElementBase") -> EngineResults:
    res = EngineResults()
    for result in eval_xpath_list(doc, "//div[contains(@class, 'sonuc')]/div"):
        (
            res.add(
                res.types.MainResult(
                    url=extract_text(eval_xpath(result, "./a/@href")) or "",
                    title=extract_text(eval_xpath(result, "./a/span")) or "",
                    content=extract_text(eval_xpath(result, "./ins")) or "",
                ),
            )
        )
    return res


def _image_results(doc: "ElementBase") -> EngineResults:
    res = EngineResults()
    for result in eval_xpath_list(doc, "//div[contains(@class, 'item gorsel')]"):
        (
            res.add(
                res.types.Image(
                    url=extract_text(eval_xpath(result, "./a/@href")) or "",
                    title=extract_text(eval_xpath(result, "./a/@title")) or "",
                    resolution=extract_text(eval_xpath(result, "div[contains(@class, 'olculeri')]")) or "",
                    thumbnail_src="https:" + str(extract_text(eval_xpath(result, "./@data-kgorsel"))),
                    img_src=extract_text(eval_xpath(result, "./@data-resimurl")) or "",
                ),
            )
        )
    return res


def _video_results(doc: "ElementBase") -> EngineResults:
    res = EngineResults()
    for result in eval_xpath_list(doc, "//div[contains(@class, 'item video')]"):
        (
            res.add(
                res.types.MainResult(
                    template="videos.html",
                    url=extract_text(eval_xpath(result, "./a/@href")) or "",
                    title=extract_text(eval_xpath(result, "./a/@title")) or "",
                    content=extract_text(eval_xpath(result, ".//div[contains(@class, 'abaslik')]")) or "",
                    thumbnail=extract_text(eval_xpath(result, "./@data-kgorsel")) or "",
                    iframe_src=extract_text(eval_xpath(result, "./@data-embedurl")) or "",
                ),
            )
        )
    return res


def response(resp: "SXNG_Response") -> EngineResults:
    doc = html.fromstring(resp.text)
    match vuhuv_category:
        case "general":
            return _general_results(doc)
        case "images":
            return _image_results(doc)
        case "videos":
            return _video_results(doc)
        case _:
            raise ValueError("invalid vuhuv category: %s" % vuhuv_category)
