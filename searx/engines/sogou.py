# SPDX-License-Identifier: AGPL-3.0-or-later
"""Sogou search engine for searxng"""

import re
from urllib.parse import urlencode
from httpx import Response
from lxml import html

from searx.network import multi_requests, Request
from searx.exceptions import SearxEngineCaptchaException
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

# meta
META_RE = re.compile(r"""URL\s*=\s*['"]?(?P<url>[^'">]+)""")


def request(query, params):
    query_params = {
        "query": query,
        "page": params["pageno"],
    }

    if time_range_dict.get(params['time_range']):
        query_params["s_from"] = time_range_dict.get(params['time_range'])
        query_params["tsn"] = 1

    params["url"] = f"{base_url}/web?{urlencode(query_params)}"
    params["allow_redirects"] = False
    return params


def response(resp: Response):
    if (
        resp.status_code == 302
        and resp.next_request is not None
        and str(resp.next_request.url).startswith("http://www.sogou.com/antispider")
    ):
        raise SearxEngineCaptchaException()

    dom = html.fromstring(resp.text)
    results = []

    url_to_resolve = []
    url_to_result = []

    for i, item in enumerate(dom.xpath('//div[contains(@class, "vrwrap")]')):
        title = extract_text(item.xpath('.//h3[contains(@class, "vr-title")]/a'))
        url = extract_text(item.xpath('.//h3[contains(@class, "vr-title")]/a/@href'))

        if not title or not url:
            continue

        content = extract_text(item.xpath('.//div[contains(@class, "text-layout")]//p[contains(@class, "star-wiki")]'))
        if not content:
            content = extract_text(item.xpath('.//div[contains(@class, "fz-mid space-txt")]'))

        result = {
            "title": title,
            "url": url,
            "content": content,
        }

        results.append(result)

        if url.startswith("/link?url="):
            url = f"{base_url}{url}"
            url_to_resolve.append(url)
            url_to_result.append(result)

    #
    request_list = [
        Request.get(u, allow_redirects=False, headers=resp.search_params['headers']) for u in url_to_resolve
    ]

    response_list = multi_requests(request_list)
    for i, redirect_response in enumerate(response_list):
        if not isinstance(redirect_response, Exception):
            m = META_RE.search(redirect_response.text)
            if m:
                url_to_result[i]['url'] = m.group("url")

    return results
