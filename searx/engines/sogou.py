# SPDX-License-Identifier: AGPL-3.0-or-later
"""Sogou search engine for searxng"""

import re
from datetime import datetime
from urllib.parse import urlencode
from lxml import html

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

time_range_dict = {
    "day": "inttime_day",
    "week": "inttime_week",
    "month": "inttime_month",
    "year": "inttime_year",
}

# Base URL
base_url = "https://www.sogou.com"


def request(query, params):
    query_params = {
        "query": query,
        "page": params["pageno"],
    }

    if time_range_dict.get(params["time_range"]):
        query_params["s_from"] = time_range_dict.get(params["time_range"])
        query_params["tsn"] = 1

    params["allow_redirects"] = False
    params["url"] = f"{base_url}/web?{urlencode(query_params)}"
    return params


def response(resp):
    if (
        resp.status_code == 302
        and resp.next_request is not None
        and str(resp.next_request.url).startswith("http://www.sogou.com/antispider")
    ):
        raise SearxEngineCaptchaException()

    dom = html.fromstring(resp.text)
    results = []

    # pylint: disable=line-too-long
    for item in dom.xpath(
        '//div[contains(@class, "rb")] | //div[contains(@class, "vrwrap") and not(.//div[contains(@class, "special-wrap")])]'
    ):
        item_html = html.tostring(item, encoding="unicode")

        if item.xpath('.//h3[@class="pt"]/a'):
            result = _parse_results(item, item_html)
        elif item.xpath('.//h3[contains(@class, "vr-title")]/a'):
            result = _parse_results_with_image(item, item_html)
        else:
            continue

        if result["title"] and result["url"]:
            results.append(result)

    return results


def _extract_url(url, item_html):
    if url and url.startswith("/link?url="):
        match = re.search(r'data-url="([^"]+)"', item_html)
        if match:
            return match.group(1)
        return f"{base_url}{url}"
    return url


def _parse_date(text):
    if text:
        text = text.strip().lstrip("-").strip()
        date_match = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", text)
        if date_match:
            try:
                return datetime.strptime(date_match.group(1), "%Y-%m-%d")
            except (ValueError, TypeError):
                pass
    return None


def _parse_results(item, item_html):
    title = extract_text(item.xpath('.//h3[@class="pt"]/a'))
    content = extract_text(item.xpath('.//div[@class="ft"]'))
    url = _extract_url(extract_text(item.xpath('.//h3[@class="pt"]/a/@href')), item_html)
    publishedDate = _parse_date(extract_text(item.xpath(".//cite")))
    return {
        "title": title,
        "url": url,
        "content": content,
        "publishedDate": publishedDate,
    }


def _parse_results_with_image(item, item_html):
    title = extract_text(item.xpath('.//h3[contains(@class, "vr-title")]/a'))
    content = extract_text(item.xpath('.//div[contains(@class, "attribute-centent")]'))
    if not content:
        content = extract_text(item.xpath('.//div[contains(@class, "fz-mid space-txt")]'))
    url = _extract_url(extract_text(item.xpath('.//h3[contains(@class, "vr-title")]/a/@href')), item_html)
    publishedDate = _parse_date(extract_text(item.xpath('.//span[@class="cite-date"]')))

    thumbnail = None
    try:
        thumbnail_src = extract_text(item.xpath('.//div[contains(@class, "img-layout")]//img/@src'))
        if thumbnail_src:
            thumbnail = thumbnail_src.replace("http://", "https://")
    except (ValueError, TypeError):
        pass

    return {
        "title": title,
        "url": url,
        "content": content,
        "publishedDate": publishedDate,
        "thumbnail": thumbnail,
    }
