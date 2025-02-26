# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=invalid-name
"""360So search engine for searxng"""

from urllib.parse import urlencode
from lxml import html

# Metadata
about = {
    "website": "https://www.so.com/",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

# Engine Configuration
categories = ["general"]
paging = True
max_page = 10
time_range_support = True

time_range_dict = {'day': 'd', 'week': 'w', 'month': 'm', 'year': 'y'}

# Base URL
base_url = "https://www.so.com/s"


def request(query, params):
    query_params = {
        "pn": params["pageno"],
        "q": query,
    }

    if 'time_range' in params and params['time_range'] in time_range_dict:
        query_params["adv_t"] = time_range_dict[params['time_range']]

    params["url"] = f"{base_url}?{urlencode(query_params)}"
    return params


def response(resp):
    dom = html.fromstring(resp.text)
    results = []

    for item in dom.xpath('//li[contains(@class, "res-list")]'):
        title_elem = item.xpath('.//h3[contains(@class, "res-title")]/a')
        title = title_elem[0].text_content().strip() if title_elem else ""

        url_elem = item.xpath('.//h3[contains(@class, "res-title")]/a/@data-mdurl')
        if not url_elem:
            url_elem = item.xpath('.//h3[contains(@class, "res-title")]/a/@href')
        url = url_elem[0] if url_elem else ""

        content_elem = item.xpath('.//p[@class="res-desc"]/text()')
        if not content_elem:
            content_elem = item.xpath('.//span[@class="res-list-summary"]/text()')
        content = " ".join(content_elem).strip() if content_elem else ""

        if title and url:
            results.append(
                {
                    "title": title,
                    "url": url,
                    "content": content,
                }
            )

    return results
