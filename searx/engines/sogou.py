# SPDX-License-Identifier: AGPL-3.0-or-later
"""Sogou search engine for searxng"""

from urllib.parse import urlencode
from lxml import html

from searx.utils import extract_text

# Metadata
about = {
    "website": "https://www.sogou.com/",
    "wikidata_id": "Q7554565",
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
    "language": "zh",
}

# Engine Configuration
categories = ["general"]
paging = True
time_range_support = True

time_range_dict = {'day': 'inttime_day', 'week': 'inttime_week', 'month': 'inttime_month', 'year': 'inttime_year'}

# Base URL
base_url = "https://www.sogou.com"


def request(query, params):
    query_params = {
        "query": query,
        "page": params["pageno"],
    }

    if time_range_dict.get(params['time_range']):
        query_params["s_from"] = time_range_dict.get(params['time_range'])
        query_params["tsn"] = 1

    params["url"] = f"{base_url}/web?{urlencode(query_params)}"
    return params


def response(resp):
    dom = html.fromstring(resp.text)
    results = []

    for item in dom.xpath('//div[contains(@class, "vrwrap")]'):
        title = extract_text(item.xpath('.//h3[contains(@class, "vr-title")]/a'))
        url = extract_text(item.xpath('.//h3[contains(@class, "vr-title")]/a/@href'))

        if url.startswith("/link?url="):
            url = f"{base_url}{url}"

        content = extract_text(item.xpath('.//div[contains(@class, "text-layout")]//p[contains(@class, "star-wiki")]'))
        if not content:
            content = extract_text(item.xpath('.//div[contains(@class, "fz-mid space-txt")]'))

        if title and url:
            results.append(
                {
                    "title": title,
                    "url": url,
                    "content": content,
                }
            )

    return results
