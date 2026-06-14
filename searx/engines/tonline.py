# SPDX-License-Identifier: AGPL-3.0-or-later
"""T-Online_ is a German news portal, which is powered by Ströer, a German
advertising company, not by Deutsche Telekom (contrary to its name).

It gets its web results from Google, image results from Flickr and videos
results from YouTube.

.. _T-Online: https://www.t-online.de/

"""

import typing as t
from urllib.parse import urlencode

from lxml import html

from searx.utils import eval_xpath_list, eval_xpath, extract_text, get_embeded_stream_url, ElementType
from searx.result_types import EngineResults
from searx.enginelib import EngineAbout

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = EngineAbout(
    website="https://www.t-online.de",
    wikidata_id="Q590940",
    results="HTML",
)

paging = True
time_range_support = True

base_url = "https://suche.t-online.de"
tonline_categ = "web"
"""Supported categories are ``web``, ``videos``, ``news`` and ``images``."""

time_range_map = {"day": "d", "week": "w", "month": "m", "year": "y"}

# result provider has to be specified during pagination, pagination can alternatively
# use "tonline" to only search for results from t-online news articles
tonline_channel_map = {"images": "flickr", "videos": "yt"}

language = "de"


def init(_):
    if tonline_categ not in ("web", "images", "videos", "news"):
        raise ValueError("invalid category: %s" % tonline_categ)


def request(query: str, params: "OnlineParams") -> None:
    # "mandant", "dia" and "ptl" are not needed, but this might reduce changes of captchas
    args = {"q": query, "mandant": "toi", "dia": "suche", "ptl": "std"}
    if params["time_range"]:
        args["age"] = time_range_map[params["time_range"]]

    if params["pageno"] > 1 and tonline_categ in tonline_channel_map:
        ch = tonline_channel_map[tonline_categ]
        args["ch"] = ch
        args[f"{ch}_page"] = str(params["pageno"])
    else:
        args["page"] = str(params["pageno"])

    params["url"] = f"{base_url}/{tonline_categ}?{urlencode(args)}"


def _general_results(doc: ElementType, res: EngineResults):
    result: ElementType
    for result in eval_xpath_list(doc, "//div[@id='google_re']/div[contains(@class, 'doc')]"):
        (
            res.add(
                res.types.MainResult(
                    url=extract_text(eval_xpath(result, "./a/@href") or ""),
                    title=extract_text(eval_xpath(result, ".//span[contains(@class, 'tMMReshl')]") or "") or "",
                    content=extract_text(eval_xpath(result, ".//div[contains(@class, 'tMMRest')]") or "") or "",
                ),
            )
        )
    suggestion: ElementType
    for suggestion in eval_xpath_list(doc, "//div[starts-with(@class, 'rsbl')]/a"):
        res.add(res.types.LegacyResult({"suggestion": extract_text(suggestion)}))


def _image_results(doc: ElementType, res: EngineResults):
    result: ElementType
    for result in eval_xpath_list(doc, "//div[@class='doc']"):
        (
            res.add(
                res.types.Image(
                    url=extract_text(eval_xpath(result, "./a/@href") or ""),
                    title=extract_text(eval_xpath(result, ".//div[contains(@class, 'doc_info')]") or "") or "",
                    thumbnail_src=extract_text(eval_xpath(result, ".//img/@src") or "") or "",
                ),
            )
        )


def _news_results(doc: ElementType, res: EngineResults):
    result: ElementType
    title_parts: list[ElementType]
    for result in eval_xpath_list(doc, "//div[@id='portal_re']/div[contains(@class, 'doc')]"):
        title_parts = eval_xpath(result, ".//a[starts-with(@class, 'tMMReshl')]")
        (
            res.add(
                res.types.MainResult(
                    url=extract_text(eval_xpath(result, "(./a/@href)[1]") or ""),
                    title=" - ".join(extract_text(part) or "" for part in title_parts),
                    content=extract_text(eval_xpath(result, ".//div[contains(@class, 'tMMRest')]") or "") or "",
                    thumbnail=extract_text(eval_xpath(result, ".//img[contains(@class, 'desk')]/@src") or "") or "",
                ),
            )
        )


def _video_results(doc: ElementType, res: EngineResults):
    result: ElementType
    for result in eval_xpath_list(doc, "//div[@class='doc']"):
        url: str | None = extract_text(eval_xpath(result, "./a/@href") or "")
        if url is None:
            continue
        title_parts: list[ElementType] = eval_xpath(result, ".//a[starts-with(@class, 'tMMReshl')]")
        res.add(
            res.types.LegacyResult(
                template="videos.html",
                url=url,
                title=" - ".join(extract_text(part) or "" for part in title_parts),
                thumbnail=extract_text(eval_xpath(result, ".//img/@src") or "") or "",
                iframe_src=get_embeded_stream_url(url) or "",
            )
        )


def response(resp: "SXNG_Response") -> EngineResults:
    doc = html.fromstring(resp.text)
    res = EngineResults()
    match tonline_categ:
        case "web":
            _general_results(doc, res)
        case "news":
            _news_results(doc, res)
        case "images":
            _image_results(doc, res)
        case "videos":
            _video_results(doc, res)
        case _:
            raise ValueError("invalid category: %s" % tonline_categ)
    return res
