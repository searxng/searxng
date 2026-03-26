# SPDX-License-Identifier: AGPL-3.0-or-later
"""Baidu"""

from urllib.parse import urlencode, unquote
from datetime import datetime
from html import unescape
import time
import json

from searx.exceptions import SearxEngineAPIException, SearxEngineCaptchaException
from searx.utils import html_to_text

try:
    from curl_cffi import requests as curl_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

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
use_impersonate = True

def init(_):
    if baidu_category not in ('general', 'images', 'it'):
        raise SearxEngineAPIException(f"Unsupported category: {baidu_category}")

def request(query, params):
    page_num = params["pageno"]
    category_config = {
        'general': {
            'endpoint': 'http://www.baidu.com/s',
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
    # Use curl_cffi to bypass captcha
    if HAS_CURL_CFFI and use_impersonate and baidu_category == 'general':
        try:
            import sys
            from urllib.parse import parse_qs, urlparse
            
            # 从原始 URL 中提取正确编码的 wd 参数
            parsed = urlparse(str(resp.url))
            qs = parse_qs(parsed.query)
            wd_encoded = qs.get('wd', ['test'])[0]
            # 直接使用已编码的值
            print(f"[BAIDU] wd_encoded: {wd_encoded}", file=sys.stderr)
            
            # 构建新 URL，直接使用已编码的 wd
            test_url = f"http://www.baidu.com/s?wd={wd_encoded}&rn={results_per_page}&pn=0&tn=json"
            print(f"[BAIDU] test_url: {test_url}", file=sys.stderr)
            
            curl_resp = curl_requests.get(
                test_url,
                impersonate="chrome",
                timeout=15,
                allow_redirects=True
            )
            print(f"[BAIDU] curl_cffi: {curl_resp.status_code}, URL: {str(curl_resp.url)[:60]}", file=sys.stderr)
            
            if 'wappass.baidu.com' not in str(curl_resp.url) and curl_resp.status_code == 200:
                text = curl_resp.text
                data = json.loads(text, strict=False)
                return parse_general(data)
        except Exception as e:
            import sys
            print(f"[BAIDU] curl_cffi error: {e}", file=sys.stderr)
    
    # Fallback
    if 'wappass.baidu.com/static/captcha' in resp.headers.get('Location', ''):
        raise SearxEngineCaptchaException()

    text = resp.text
    if baidu_category == 'images':
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
        title = unescape(entry["title"])
        content = unescape(entry.get("abs", ""))
        results.append({
            "title": title,
            "url": entry["url"],
            "content": content,
            "publishedDate": published_date,
        })
    return results

def parse_images(data):
    results = []
    if "data" in data:
        for item in data["data"]:
            if not item:
                continue
            results.append({
                "title": item.get("fromPageTitleEnc", ""),
                "url": item.get("fromURL", ""),
                "img_src": item.get("objURL", ""),
                "thumbnail_src": item.get("thumbURL", ""),
                "source": item.get("fromURLHost", ""),
                "template": "images.html",
            })
    return results

def parse_it(data):
    results = []
    for res in data.get("data", {}).get("documents", []):
        results.append({
            "url": res.get("url", ""),
            "title": res.get("title", ""),
            "content": res.get("content", ""),
        })
    return results
