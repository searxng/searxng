# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Presearch (general, images, videos, news)
"""

from urllib.parse import urlencode
from searx.network import get
from searx.utils import gen_useragent, html_to_text

about = {
    "website": "https://presearch.io",
    "wikidiata_id": "Q7240905",
    "official_api_documentation": "https://docs.presearch.io/nodes/api",
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}
paging = True
time_range_support = True
categories = ["general", "web"]  # general, images, videos, news

search_type = "search"  # must be any of "search", "images", "videos", "news"

base_url = "https://presearch.com"
safesearch_map = {0: 'false', 1: 'true', 2: 'true'}


def _get_request_id(query, page, time_range, safesearch):
    args = {
        "q": query,
        "page": page,
    }
    if time_range:
        args["time_range"] = time_range

    url = f"{base_url}/{search_type}?{urlencode(args)}"
    headers = {
        'User-Agent': gen_useragent(),
        'Cookie': f"b=1;presearch_session=;use_safe_search={safesearch_map[safesearch]}",
    }
    resp_text = get(url, headers=headers).text

    for line in resp_text.split("\n"):
        if "window.searchId = " in line:
            return line.split("= ")[1][:-1].replace('"', "")

    return None


def _is_valid_img_src(url):
    # in some cases, the image url is a base64 encoded string, which has to be skipped
    return "https://" in url


def request(query, params):
    request_id = _get_request_id(query, params["pageno"], params["time_range"], params["safesearch"])

    params["headers"]["Accept"] = "application/json"
    params["url"] = f"{base_url}/results?id={request_id}"

    return params


def response(resp):
    results = []

    json = resp.json()

    json_results = []
    if search_type == "search":
        json_results = json['results'].get('standardResults', [])
    else:
        json_results = json.get(search_type, [])

    for json_result in json_results:
        result = {
            'url': json_result['link'],
            'title': json_result['title'],
            'content': html_to_text(json_result.get('description', '')),
        }
        if search_type == "images":
            result['template'] = 'images.html'

            if not _is_valid_img_src(json_result['image']):
                continue

            result['img_src'] = json_result['image']
            if _is_valid_img_src(json_result['thumbnail']):
                result['thumbnail'] = json_result['thumbnail']

        elif search_type == "videos":
            result['template'] = 'videos.html'

            if _is_valid_img_src(json_result['image']):
                result['thumbnail'] = json_result['image']

            result['duration'] = json_result['duration']
            result['length'] = json_result['duration']

        results.append(result)

    return results
