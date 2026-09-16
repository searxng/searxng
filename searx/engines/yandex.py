# SPDX-License-Identifier: AGPL-3.0-or-later
"""Yandex (Web, images)"""

import typing as t
from json import JSONDecodeError, loads
from urllib.parse import urlencode
from lxml import html
from searx.exceptions import SearxEngineCaptchaException, SearxEngineResponseException
from searx.result_types import EngineResults
from searx.utils import humanize_bytes, eval_xpath, eval_xpath_list, extract_text, html_to_text

if t.TYPE_CHECKING:
    from searx import logger  # logger is injected by searx.engines.set_loggers()
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

# Engine metadata
about = {
    "website": "https://yandex.com/",
    "wikidata_id": "Q5281",
    "official_api_documentation": "?",
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

# Engine configuration
categories = []
paging = True
enable_http3 = True
search_type = ""

# Search URL
base_url_web = "https://yandex.com/search/site/"
base_url_images = "https://yandex.com/images/search"

# Supported languages
yandex_supported_langs = [
    "ru",  # Russian
    "en",  # English
    "be",  # Belarusian
    "fr",  # French
    "de",  # German
    "id",  # Indonesian
    "kk",  # Kazakh
    "tt",  # Tatar
    "tr",  # Turkish
    "uk",  # Ukrainian
]

results_xpath = '//li[contains(@class, "serp-item")]'
url_xpath = './/a[@class="b-serp-item__title-link"]/@href'
title_xpath = './/h3[@class="b-serp-item__title"]/a[@class="b-serp-item__title-link"]/span'
content_xpath = './/div[@class="b-serp-item__content"]//div[@class="b-serp-item__text"]'


def catch_bad_response(resp: "SXNG_Response") -> None:
    if resp.headers.get("x-yandex-captcha") == "captcha":
        raise SearxEngineCaptchaException()


def request(query: str, params: "OnlineParams") -> None:
    query_params_web = {
        "tmpl_version": "releases",
        "text": query,
        "web": "1",
        "frame": "1",
        "searchid": "3131712",
    }

    lang = params["language"].split("-")[0]  # type: ignore
    if lang in yandex_supported_langs:
        query_params_web["lang"] = lang

    query_params_images = {
        "text": query,
        "uinfo": "sw-1920-sh-1080-ww-1125-wh-999",
    }

    if params["pageno"] > 1:
        query_params_web["p"] = params["pageno"] - 1  # type: ignore
        query_params_images["p"] = params["pageno"] - 1  # type: ignore

    params["cookies"] = {"cookie": "yp=1716337604.sp.family%3A0#1685406411.szm.1:1920x1080:1920x999"}

    if search_type == "web":
        params["url"] = f"{base_url_web}?{urlencode(query_params_web)}"
    elif search_type == "images":
        params["url"] = f"{base_url_images}?{urlencode(query_params_images)}"


def _parse_json_results(dom: html.HtmlElement) -> dict[str, t.Any]:
    # attempt to parse using xpath - finding element with "data-state" attribute
    data_elements = dom.xpath("//*[@data-state]/@data-state")
    for json_data in data_elements:
        try:
            json_resp = loads(json_data)
            if json_resp.get("location") == "/images/search/":
                return json_resp
        except JSONDecodeError:
            logger.debug("failed parsing data-state json")

    raise SearxEngineResponseException("failed to parse JSON data")


def response(resp: "SXNG_Response") -> EngineResults:
    catch_bad_response(resp)
    results = EngineResults()
    dom = html.fromstring(resp.text)

    match search_type:
        case "web":
            for result in eval_xpath_list(dom, results_xpath):
                url = extract_text(eval_xpath(result, url_xpath))
                title = extract_text(eval_xpath(result, title_xpath))
                content = extract_text(eval_xpath(result, content_xpath))
                results.add(results.types.MainResult(url=url, title=str(title), content=str(content)))
        case "images":
            json_resp = _parse_json_results(dom)

            # build results from loaded json values
            for item_data in json_resp["initialState"]["serpList"]["items"]["entities"].values():
                viewerData: dict[str, t.Any] = item_data["viewerData"]
                snippet: dict[str, str] = viewerData.get("snippet", {})

                # return the image with largest dimensions
                image_sources = viewerData.get("dups", []) + viewerData.get("preview", [])
                image_source = max(image_sources, key=lambda x: x["h"] * x["w"])

                humanized_filesize = None
                if image_source.get("fileSizeInBytes"):
                    humanized_filesize = humanize_bytes(image_source["fileSizeInBytes"])

                results.add(
                    results.types.Image(
                        title=snippet.get("title"),  # type: ignore
                        content=html_to_text(snippet.get("text")),  # type: ignore
                        url=snippet.get("url"),
                        img_src=image_source["url"],
                        filesize=humanized_filesize,  # type: ignore
                        thumbnail_src=item_data["image"],
                        resolution=f"{image_source['w']} x {image_source['h']}",
                    )
                )

    return results
