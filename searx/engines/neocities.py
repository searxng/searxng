# SPDX-License-Identifier: AGPL-3.0-or-later
"""neocities (general, blogs)"""

from urllib.parse import urlencode
from lxml import html

from searx.utils import eval_xpath, eval_xpath_list, extract_text
from searx.result_types import EngineResults

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
base_url = "https://neocities.org/search"

results_xpath = "//div[@class='result-item']"
url_xpath = './/div[@class="result-url"]/a/@href'
title_xpath = './/h3[@class="result-title"]/a/text()'
content_xpath = './/p[@class="result-snippet"]//text()'
screenshot_xpath = './/a[@class="result-screenshot"]/img/@src'


def request(query, params):
    query_params = {"q": query}

    if params['pageno'] > 1:
        offset = (params["pageno"] - 1) * 100
        query_params["start"] = offset

    params["url"] = f"{base_url}?{urlencode(query_params)}"
    return params


def response(resp) -> EngineResults:
    results = EngineResults()
    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, results_xpath):
        url = extract_text(eval_xpath(result, url_xpath))
        title = extract_text(eval_xpath(result, title_xpath))
        content = extract_text(eval_xpath(result, content_xpath))
        screenshot = extract_text(eval_xpath(result, screenshot_xpath))

        results.add(
            results.types.MainResult(
                url=url,
                title=title,
                content=content,
                thumbnail='https://neocities.org' + screenshot,
            )
        )

    return results
