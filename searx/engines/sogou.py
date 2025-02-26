# SPDX-License-Identifier: AGPL-3.0-or-later
"""Sogou search engine for searxng"""

from urllib.parse import urlencode
from lxml import html

# Metadata
about = {
    "website": "https://www.sogou.com/",
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

time_range_dict = {'day': 'inttime_day', 'week': 'inttime_week', 'month': 'inttime_month', 'year': 'inttime_year'}

# Base URL
base_url = "https://www.sogou.com/web"


def request(query, params):
    query_params = {
        "query": query,
        "page": params["pageno"],
    }

    if 'time_range' in params and params['time_range'] in time_range_dict:
        query_params["s_from"] = time_range_dict[params['time_range']]
        query_params["tsn"] = 1

    params["url"] = f"{base_url}?{urlencode(query_params)}"
    return params


def response(resp):
    dom = html.fromstring(resp.text)
    results = []

    for item in dom.xpath('//div[contains(@class, "vrwrap")]'):
        title_elem = item.xpath('.//h3[contains(@class, "vr-title")]/a')
        title = title_elem[0].text_content().strip() if title_elem else ""

        url_elem = item.xpath('.//h3[contains(@class, "vr-title")]/a/@href')
        url = url_elem[0] if url_elem else ""

        if url.startswith("/link?url="):
            url = f"https://www.sogou.com{url}"

        content_elem = item.xpath('.//div[contains(@class, "text-layout")]//p[contains(@class, "star-wiki")]/text()')
        content = " ".join(content_elem).strip() if content_elem else ""
        if not content:
            content_elem = item.xpath('.//div[contains(@class, "fz-mid space-txt")]/text()')
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
