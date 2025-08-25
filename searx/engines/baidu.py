# SPDX-License-Identifier: AGPL-3.0-or-later
"""Baidu_

.. _Baidu: https://www.baidu.com
"""

# There exits a https://github.com/ohblue/baidu-serp-api/
# but we don't use it here (may we can learn from).

from urllib.parse import urlencode
from datetime import datetime
from html import unescape
import time
import json

from searx.exceptions import SearxEngineAPIException, SearxEngineCaptchaException
from searx.utils import html_to_text

about = {
    "website": "https://www.baidu.com",
    "wikidata_id": "Q14772",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
    "language": "zh",
}

paging = True
categories = []
results_per_page = 10

baidu_category = 'general'

time_range_support = True
time_range_dict = {"day": 86400, "week": 604800, "month": 2592000, "year": 31536000}


def init(_):
    if baidu_category not in ('general', 'images', 'it'):
        raise SearxEngineAPIException(f"Unsupported category: {baidu_category}")


def request(query, params):
    page_num = params["pageno"]

    category_config = {
        'general': {
            'endpoint': 'https://www.baidu.com/s',
            'params': {
                "wd": query,
                "rn": results_per_page,
                "pn": (page_num - 1) * results_per_page,
                "tn": "json",
            },
        },
        'images': {
            'endpoint': 'https://image.baidu.com/search/acjson',
            'params': {
                "word": query,
                "rn": results_per_page,
                "pn": (page_num - 1) * results_per_page,
                "tn": "resultjson_com",
            },
        },
        'it': {
            'endpoint': 'https://kaifa.baidu.com/rest/v1/search',
            'params': {
                "wd": query,
                "pageSize": results_per_page,
                "pageNum": page_num,
                "paramList": f"page_num={page_num},page_size={results_per_page}",
                "position": 0,
            },
        },
    }

    query_params = category_config[baidu_category]['params']
    query_url = category_config[baidu_category]['endpoint']

    if params.get("time_range") in time_range_dict:
        now = int(time.time())
        past = now - time_range_dict[params["time_range"]]

        if baidu_category == 'general':
            query_params["gpc"] = f"stf={past},{now}|stftype=1"

        if baidu_category == 'it':
            query_params["paramList"] += f",timestamp_range={past}-{now}"

    params["url"] = f"{query_url}?{urlencode(query_params)}"
    params["allow_redirects"] = False
    return params


def response(resp):
    # Detect Baidu Captcha, it will redirect to wappass.baidu.com
    if 'wappass.baidu.com/static/captcha' in resp.headers.get('Location', ''):
        raise SearxEngineCaptchaException(suspended_time=300, message="Baidu CAPTCHA detected. Please try again later.")

    text = resp.text
    if baidu_category == 'images':
        # baidu's JSON encoder wrongly quotes / and ' characters by \\ and \'
        text = text.replace(r"\/", "/").replace(r"\'", "'")
    data = json.loads(text, strict=False)
    parsers = {'general': parse_general, 'images': parse_images, 'it': parse_it}

    return parsers[baidu_category](data)


def parse_general(data):
    results = []
    if not data.get("feed", {}).get("entry"):
        raise SearxEngineAPIException("Invalid response")

    for entry in data["feed"]["entry"]:
        if not entry.get("title") or not entry.get("url"):
            continue

        published_date = None
        if entry.get("time"):
            try:
                published_date = datetime.fromtimestamp(entry["time"])
            except (ValueError, TypeError):
                published_date = None

        # title and content sometimes containing characters such as &amp; &#39; &quot; etc...
        title = unescape(entry["title"])
        content = unescape(entry.get("abs", ""))

        results.append(
            {
                "title": title,
                "url": entry["url"],
                "content": content,
                "publishedDate": published_date,
            }
        )
    return results


def parse_images(data):
    results = []
    if "data" in data:
        for item in data["data"]:
            if not item:
                # the last item in the JSON list is empty, the JSON string ends with "}, {}]"
                continue
            replace_url = item.get("replaceUrl", [{}])[0]
            width = item.get("width")
            height = item.get("height")
            img_date = item.get("bdImgnewsDate")
            publishedDate = None
            if img_date:
                publishedDate = datetime.strptime(img_date, "%Y-%m-%d %H:%M")
            results.append(
                {
                    "template": "images.html",
                    "url": replace_url.get("FromURL"),
                    "thumbnail_src": item.get("thumbURL"),
                    "img_src": replace_url.get("ObjURL"),
                    "title": html_to_text(item.get("fromPageTitle")),
                    "source": item.get("fromURLHost"),
                    "resolution": f"{width} x {height}",
                    "img_format": item.get("type"),
                    "filesize": item.get("filesize"),
                    "publishedDate": publishedDate,
                }
            )
    return results


def parse_it(data):
    results = []
    if not data.get("data", {}).get("documents", {}).get("data"):
        raise SearxEngineAPIException("Invalid response")

    for entry in data["data"]["documents"]["data"]:
        results.append(
            {
                'title': entry["techDocDigest"]["title"],
                'url': entry["techDocDigest"]["url"],
                'content': entry["techDocDigest"]["summary"],
            }
        )
    return results
