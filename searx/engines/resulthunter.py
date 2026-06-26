# SPDX-License-Identifier: AGPL-3.0-or-later
"""Resulthunter_ is an American search engine with results from Brave.

.. _Resulthunter : https://resulthunter.com
"""

import typing as t
from urllib.parse import urlencode

from lxml import html

from searx import locales
from searx.result_types import EngineResults
from searx.utils import eval_xpath_list, eval_xpath, extract_text

# as it uses brave internally, it has the same locales and timerange/safesearch types
from searx.engines.brave import safesearch_map, time_range_map, fetch_traits  # pylint: disable=unused-import

if t.TYPE_CHECKING:
    from lxml.etree import ElementBase
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams
    from searx.enginelib.traits import EngineTraits

    traits: EngineTraits

about = {
    "website": "https://resulthunter.com",
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

paging = True
safesearch = True
time_range_support = True

base_url = "https://resulthunter.com"
resulthunter_categ = "web"
"""Supported categories are ``web`` and ``images``."""


def init(_):
    if resulthunter_categ not in ("web", "images"):
        raise ValueError("invalid category: %s" % resulthunter_categ)


def request(query: str, params: "OnlineParams") -> None:
    args = {
        "q": query,
        "search_type": resulthunter_categ,
        "offset": params["pageno"] - 1,
    }

    # uses Brave's engine traits
    ui_lang = locales.get_engine_locale(params["searxng_locale"], traits.custom["ui_lang"], "all")
    if ui_lang and ui_lang != "all":
        args["search_lang"] = ui_lang.split("-")[0]

    engine_region = traits.get_region(params["searxng_locale"], "all")
    if engine_region and engine_region != "all":
        args["country"] = engine_region

    if params["time_range"]:
        args["freshness"] = time_range_map[params["time_range"]]

    params["cookies"]["safesearch"] = safesearch_map[params["safesearch"]]

    params["url"] = f"{base_url}/search?{urlencode(args)}"


def _general_results(doc: "ElementBase") -> EngineResults:
    res = EngineResults()
    for result in eval_xpath_list(
        doc, "//div[contains(@class, 'organic-results-container')]/div/div[contains(@class, 'group')]"
    ):
        url = extract_text(eval_xpath(result, ".//a/@href"))
        if not url:
            continue
        (
            res.add(
                res.types.MainResult(
                    url=url,
                    title=extract_text(eval_xpath(result, ".//a/h3")) or "",
                    content=extract_text(eval_xpath(result, ".//p")) or "",
                ),
            )
        )
    return res


def _image_results(doc: "ElementBase") -> EngineResults:
    res = EngineResults()
    for result in eval_xpath_list(
        doc, "//div[contains(@class, 'organic-results-container')]//a[contains(@class, 'group')]"
    ):
        (
            res.add(
                res.types.Image(
                    url=extract_text(eval_xpath(result, "./@href")) or "",
                    title=extract_text(eval_xpath(result, "./img/@alt")) or "",
                    img_src=extract_text(eval_xpath(result, "./img/@src")) or "",
                ),
            )
        )
    return res


def response(resp: "SXNG_Response") -> EngineResults:
    doc = html.fromstring(resp.text)

    match resulthunter_categ:
        case "web":
            return _general_results(doc)
        case "images":
            return _image_results(doc)
        case _:
            raise ValueError("invalid resulthunter category: %s" % resulthunter_categ)
