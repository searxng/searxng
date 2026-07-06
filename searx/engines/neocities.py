# SPDX-License-Identifier: AGPL-3.0-or-later
"""Neocities_ is open source software for creating blogs.

.. _Neocities : https://github.com/neocities/neocities
"""

from urllib.parse import urlencode
import typing as t

from lxml import html

from searx.utils import eval_xpath, eval_xpath_list, extract_text
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from extended_types import SXNG_Response
    from search.processors import OnlineParams


# Engine metadata
about = {
    "website": "https://neocities.org/",
    "wikidata_id": "Q17071099",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

# Engine configuration
categories = ["general", "blogs"]
paging = True

# Search URL
base_url = "https://neocities.org"

results_xpath = "//div[@class='result-item']"
url_xpath = './/div[@class="result-url"]/a/@href'
title_xpath = './/h3[@class="result-title"]/a/text()'
content_xpath = './/p[@class="result-snippet"]//text()'
screenshot_xpath = './/a[@class="result-screenshot"]/img/@src'


def request(query: str, params: "OnlineParams") -> None:
    query_params: dict[str, t.Any] = {"q": query}
    if params['pageno'] > 1:
        offset = (params["pageno"] - 1) * 100
        query_params["start"] = offset
    params["url"] = f"{base_url}/search?{urlencode(query_params)}"


def response(resp: "SXNG_Response") -> EngineResults:
    results = EngineResults()
    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, results_xpath):
        results.add(
            results.types.MainResult(
                url=extract_text(eval_xpath(result, url_xpath)),
                title=extract_text(eval_xpath(result, title_xpath)) or "",
                content=extract_text(eval_xpath(result, content_xpath)) or "",
                thumbnail=base_url + (extract_text(eval_xpath(result, screenshot_xpath)) or ""),
            )
        )

    return results
