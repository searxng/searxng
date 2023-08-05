# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Brave (General, news, videos, images)
"""

from urllib.parse import urlencode
from lxml import html
from searx.utils import extract_text, eval_xpath, eval_xpath_list
import chompjs, json
import re

about = {
    "website": 'https://search.brave.com/',
    "wikidata_id": 'Q22906900',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}
base_url = "https://search.brave.com/"
paging = False
categories = ['images', 'videos', 'news'] # images, videos, news

def request(query, params):
    args = {
        'q': query,
        'spellcheck': 1,
    }
    params["url"] = f"{base_url}{categories[0]}?{urlencode(args)}"

def get_image_results(text):
    results = []

    datastr = ""
    for line in text.split("\n"):
        if "const data = " in line:
            datastr = line.replace("const data = ", "").strip()[:-1]
            break

    json_data = chompjs.parse_js_object(datastr)

    for result in json_data[1]["data"]["body"]["response"]["results"]:
        results.append(
            {
                'template': 'images.html',
                'url': result['url'],
                'thumbnail_src': result['thumbnail']['src'],
                'img_src': result['properties']['url'],
                'content': result['description'],
                'title': result['title'],
                'source': result['source'],
                'img_format': result['properties']['format'],
            }
        )

    return results

def response(resp):
    dom = html.fromstring(resp.text)

    match categories[0]:
        case 'images':
            return get_image_results(resp.text)
        case _:
            return []