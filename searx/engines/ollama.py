# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ollama model search engine for searxng"""

from urllib.parse import urlencode
from datetime import datetime
from lxml import html

from searx.utils import eval_xpath_list, eval_xpath_getindex, eval_xpath, extract_text
from searx.result_types import EngineResults

about = {
    "website": "https://ollama.com",
    "wikidata_id": "Q124636097",
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

categories = ["it", "repos"]

base_url = "https://ollama.com"

results_xpath = '//li[@x-test-model]'
title_xpath = './/span[@x-test-search-response-title]/text()'
content_xpath = './/p[@class="max-w-lg break-words text-neutral-800 text-md"]/text()'
url_xpath = './a/@href'
publish_date_xpath = './/span[contains(@class, "flex items-center")]/@title'


def request(query, params):
    query_params = {"q": query}

    params['url'] = f"{base_url}/search?{urlencode(query_params)}"
    return params


def response(resp) -> EngineResults:
    res = EngineResults()

    dom = html.fromstring(resp.text)

    for item in eval_xpath_list(dom, results_xpath):
        published_date = None
        try:
            published_date = datetime.strptime(
                extract_text(eval_xpath(item, publish_date_xpath)), "%b %d, %Y %I:%M %p %Z"
            )
        except ValueError:
            pass

        res.add(
            res.types.MainResult(
                title=extract_text(eval_xpath(item, title_xpath)),
                content=extract_text(eval_xpath(item, content_xpath)),
                url=f"{base_url}{eval_xpath_getindex(item, url_xpath, 0)}",
                publishedDate=published_date,
            )
        )

    return res
