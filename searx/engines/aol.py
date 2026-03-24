# SPDX-License-Identifier: AGPL-3.0-or-later
"""AOL supports WEB, image, and video search.  Internally, it uses the Bing
index.

AOL doesn't seem to support setting the language via request parameters, instead
the results are based on the URL.  For example, there is

- `search.aol.com <https://search.aol.com>`_ for English results
- `suche.aol.de <https://suche.aol.de>`_ for German results

However, AOL offers its services only in a few regions:

- en-US: search.aol.com
- de-DE: suche.aol.de
- fr-FR: recherche.aol.fr
- en-GB: search.aol.co.uk
- en-CA: search.aol.ca

In order to still offer sufficient support for language and region, the `search
keywords`_ known from Bing, ``language`` and ``loc`` (region), are added to the
search term (AOL is basically just a proxy for Bing).

.. _search keywords:
    https://support.microsoft.com/en-us/topic/advanced-search-keywords-ea595928-5d63-4a0b-9c6b-0b769865e78a

"""

from urllib.parse import urlencode, unquote_plus
import typing as t

from lxml import html
from dateutil import parser

from searx.result_types import EngineResults
from searx.utils import eval_xpath_list, eval_xpath, extract_text

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://www.aol.com",
    "wikidata_id": "Q2407",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

categories = ["general"]
search_type = "search"  # supported: search, image, video

paging = True
safesearch = True
time_range_support = True
results_per_page = 10


base_url = "https://search.aol.com"
time_range_map = {"day": "1d", "week": "1w", "month": "1m", "year": "1y"}
safesearch_map = {0: "p", 1: "r", 2: "i"}


def init(_):
    if search_type not in ("search", "image", "video"):
        raise ValueError(f"unsupported search type {search_type}")


def request(query: str, params: "OnlineParams") -> None:

    language, region = (params["searxng_locale"].split("-") + [None])[:2]
    if language and language != "all":
        query = f"{query} language:{language}"
    if region:
        query = f"{query} loc:{region}"

    args: dict[str, str | int | None] = {
        "q": query,
        "b": params["pageno"] * results_per_page + 1,  # page is 1-indexed
        "pz": results_per_page,
    }

    if params["time_range"]:
        args["fr2"] = "time"
        args["age"] = params["time_range"]
    else:
        args["fr2"] = "sb-top-search"

    params["cookies"]["sB"] = f"vm={safesearch_map[params['safesearch']]}"
    params["url"] = f"{base_url}/aol/{search_type}?{urlencode(args)}"
    logger.debug(params)


def _deobfuscate_url(obfuscated_url: str) -> str | None:
    # URL looks like "https://search.aol.com/click/_ylt=AwjFSDjd;_ylu=JfsdjDFd/RV=2/RE=1774058166/RO=10/RU=https%3a%2f%2fen.wikipedia.org%2fwiki%2fTree/RK=0/RS=BP2CqeMLjscg4n8cTmuddlEQA2I-"  # pylint: disable=line-too-long
    if not obfuscated_url:
        return None

    for part in obfuscated_url.split("/"):
        if part.startswith("RU="):
            return unquote_plus(part[3:])
    # pattern for de-obfuscating URL not found, fall back to Yahoo's tracking link
    return obfuscated_url


def _general_results(doc: html.HtmlElement) -> EngineResults:
    res = EngineResults()

    for result in eval_xpath_list(doc, "//div[@id='web']//ol/li[not(contains(@class, 'first'))]"):
        obfuscated_url = extract_text(eval_xpath(result, ".//h3/a/@href"))
        if not obfuscated_url:
            continue

        url = _deobfuscate_url(obfuscated_url)
        if not url:
            continue

        res.add(
            res.types.MainResult(
                url=url,
                title=extract_text(eval_xpath(result, ".//h3/a")) or "",
                content=extract_text(eval_xpath(result, ".//div[contains(@class, 'compText')]")) or "",
                thumbnail=extract_text(eval_xpath(result, ".//a[contains(@class, 'thm')]/img/@data-src")) or "",
            )
        )
    return res


def _video_results(doc: html.HtmlElement) -> EngineResults:
    res = EngineResults()

    for result in eval_xpath_list(doc, "//div[contains(@class, 'results')]//ol/li"):
        obfuscated_url = extract_text(eval_xpath(result, ".//a/@href"))
        if not obfuscated_url:
            continue

        url = _deobfuscate_url(obfuscated_url)
        if not url:
            continue

        published_date_raw = extract_text(eval_xpath(result, ".//div[contains(@class, 'v-age')]"))
        try:
            published_date = parser.parse(published_date_raw or "")
        except parser.ParserError:
            published_date = None

        res.add(
            res.types.LegacyResult(
                {
                    "template": "videos.html",
                    "url": url,
                    "title": extract_text(eval_xpath(result, ".//h3")),
                    "content": extract_text(eval_xpath(result, ".//div[contains(@class, 'compText')]")),
                    "thumbnail": extract_text(eval_xpath(result, ".//img[contains(@class, 'thm')]/@src")),
                    "length": extract_text(eval_xpath(result, ".//span[contains(@class, 'v-time')]")),
                    "publishedDate": published_date,
                }
            )
        )

    return res


def _image_results(doc: html.HtmlElement) -> EngineResults:
    res = EngineResults()

    for result in eval_xpath_list(doc, "//section[@id='results']//ul/li"):
        obfuscated_url = extract_text(eval_xpath(result, "./a/@href"))
        if not obfuscated_url:
            continue

        url = _deobfuscate_url(obfuscated_url)
        if not url:
            continue

        res.add(
            res.types.LegacyResult(
                {
                    "template": "images.html",
                    # results don't have an extra URL, only the image source
                    "url": url,
                    "title": extract_text(eval_xpath(result, ".//a/@aria-label")),
                    "thumbnail_src": extract_text(eval_xpath(result, ".//img/@src")),
                    "img_src": url,
                }
            )
        )

    return res


def response(resp: "SXNG_Response") -> EngineResults:
    doc = html.fromstring(resp.text)

    match search_type:
        case "search":
            results = _general_results(doc)
        case "image":
            results = _image_results(doc)
        case "video":
            results = _video_results(doc)
        case _:
            raise ValueError("unsupported search type")

    for suggestion in eval_xpath_list(doc, ".//ol[contains(@class, 'searchRightBottom')]//table//a"):
        results.add(results.types.LegacyResult({"suggestion": extract_text(suggestion)}))

    return results
