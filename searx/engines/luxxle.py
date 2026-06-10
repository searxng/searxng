# SPDX-License-Identifier: AGPL-3.0-or-later
"""Luxxle_ is an American search engine focusing on providing "unbiased"
results.

.. _Luxxle: https://luxxle.com
"""

from json import dumps
from urllib.parse import quote_plus, unquote_plus

import typing as t
from lxml import html

from searx.result_types import EngineResults
from searx.network import get
from searx.utils import (
    extr,
    gen_useragent,
    eval_xpath_list,
    extract_text,
    eval_xpath,
    parse_duration_string,
    ElementType,
)

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams
    from searx.extended_types import SXNG_Response


about = {
    "website": "https://luxxle.com",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

categories = []
safeseach = True

base_url = "https://luxxle.com"

luxxle_categ = "search"
"""Supported categories: "search", "news", "images", "videos"."""

# otherwise all requests get blocked (http2-fingerprinted probably)
enable_http2 = False


safe_search_map = {0: "Off", 1: "Moderate", 2: "Strict"}


def init(_):
    if luxxle_categ not in ("search", "images", "videos", "news"):
        raise ValueError("invalid luxxle category: %s" % luxxle_categ)


def _obtain_telemetry_data(query: str) -> dict[str, str]:
    """This data is required for sending search queries.

    The luxsearch page (for general results) has a JS dict called ``telemetryData``
    that contains all the important info, but the others don't, so we don't use it
    here. But it's useful to understand which info is needed.

    .. code-block:: javascript

        var telemetryData = {
            errorInformation: errorInformation,
            query: "youapps club",
            ip: "10.10.10.10",
            timeOf: "1781119224",
            authorization: "db889e0ae67d3c320858ad97f51cc4f0a4d8e1913c4f5ebe5d2eafef606521dd",
        };

    This data is only valid for very short times
    """
    resp = get(
        f"{base_url}/lux{luxxle_categ}?q={quote_plus(query)}", headers={"User-Agent": gen_useragent(), "Sec-GPC": "1"}
    )

    def extr_js_variable(name: str) -> str:
        val = extr(resp.text, f"var {name} = \"", "\";")
        if not val:
            val = extr(resp.text, f"var {name} = '", "';")
        return val

    return {
        "ip": extr_js_variable("ip"),
        "timeOf": extr_js_variable("timeOf"),
        "authorization": extr_js_variable("authorization"),
        "preferencesCookie": extr_js_variable("preferencesCookie"),
    }


def request(query: str, params: "OnlineParams") -> None:
    telemetry_data = _obtain_telemetry_data(query)

    market = params["searxng_locale"]
    if market == "all":
        market = "en-US"

    params["url"] = f"{base_url}/load_{luxxle_categ}.php"
    search_data = {
        **telemetry_data,
        "query": query,
        "market": market,
        "safeSearch": safe_search_map[params["safesearch"]],
        "freshness": "",
        "language": "english",  # UI language
    }
    if luxxle_categ == "images":
        # for some reason this is sent as form data
        params["data"] = {"searchData": dumps(search_data)}
    else:
        params["json"] = {"searchData": search_data}
    params["method"] = "POST"


def _extract_url_from_redirect(url: str):
    # urls usually look like "/redirect?url=<url>"
    query_start_idx = url.find("?url=")
    if query_start_idx < 0:
        return url

    url_start_idx = query_start_idx + len("?url=")
    return unquote_plus(url[url_start_idx:])


def _general_results(doc: ElementType, res: EngineResults):
    for result in eval_xpath_list(doc, "//div[@id='mainResults']/div[contains(@class, 'resultsContainer')]"):
        res.add(
            res.types.MainResult(
                url=_extract_url_from_redirect(
                    extract_text(eval_xpath(result, "./div[contains(@class, 'urlAddressLink')]/a/@href")) or ""
                ),
                title=extract_text(eval_xpath(result, "./div[contains(@class, 'urlname')]")) or "",
                content=extract_text(eval_xpath(result, "./div[contains(@class, 'urlSnippet')]")) or "",
            )
        )


def _news_results(doc: ElementType, res: EngineResults):
    for result in eval_xpath_list(
        doc, "//div[contains(@class, 'newsResults')]/div[contains(@class, 'mediaResultNewsPage')]"
    ):
        res.add(
            res.types.MainResult(
                url=_extract_url_from_redirect(
                    extract_text(eval_xpath(result, ".//div[contains(@class, 'mediaResultNewsPageTitle')]/a/@href"))
                    or ""
                ),
                title=extract_text(eval_xpath(result, ".//div[contains(@class, 'mediaResultNewsPageTitle')]/a")) or "",
                content=extract_text(eval_xpath(result, ".//div[contains(@class, 'mediaResultNewsPageDescription')]"))
                or "",
                thumbnail=extract_text(eval_xpath(result, ".//div[contains(@class, 'mediaResultThumbnail')]//img/@src"))
                or "",
            )
        )


def _video_results(doc: ElementType, res: EngineResults):
    for result in eval_xpath_list(doc, "//div[@id='mainResults']/div[contains(@class, 'mediaResult')]"):
        res.add(
            res.types.MainResult(
                template="videos.html",
                url=extract_text(eval_xpath(result, "./@data-url")) or "",
                title=extract_text(eval_xpath(result, ".//div[contains(@class, 'mediaResultTitleVideo')]/a")) or "",
                content=extract_text(eval_xpath(result, ".//div[contains(@class, 'mediaResultDescription')]")) or "",
                thumbnail=extract_text(eval_xpath(result, ".//img[contains(@class, 'videoThumbnail')]/@src")) or "",
                author=extract_text(eval_xpath(result, ".//div[contains(@class, 'videoCreator')]")) or "",
                length=parse_duration_string(
                    extract_text(eval_xpath(result, ".//span[contains(@class, 'mediaResultDuration')]")) or ""
                ),
            )
        )


def _image_results(doc: ElementType, res: EngineResults):
    for result in eval_xpath_list(doc, "//div[contains(@class, 'imageResultsWrapper')]/div"):
        res.add(
            res.types.Image(
                url=_extract_url_from_redirect(
                    extract_text(eval_xpath(result, ".//a[contains(@class, 'imageResultSource')]/@href")) or ""
                ),
                title=extract_text(eval_xpath(result, ".//a[contains(@class, 'imageResultTitle')]")) or "",
                source=extract_text(eval_xpath(result, ".//div[contains(@class, 'imageResultSource')]")) or "",
                thumbnail_src=extract_text(eval_xpath(result, "./@data-thumbnail-src")) or "",
                img_src=extract_text(eval_xpath(result, "./@data-image-src")) or "",
            )
        )


def response(resp: "SXNG_Response") -> EngineResults:
    doc = html.fromstring(resp.text)
    res = EngineResults()

    match luxxle_categ:
        case "search":
            _general_results(doc, res)
        case "images":
            _image_results(doc, res)
        case "videos":
            _video_results(doc, res)
        case "news":
            _news_results(doc, res)
        case _:
            raise ValueError("unsupported category: %s" % luxxle_categ)

    return res
