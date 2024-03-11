# SPDX-License-Identifier: AGPL-3.0-or-later
"""Imgur (images)
"""

from urllib.parse import urlencode
from lxml import html
from searx.utils import extract_text, eval_xpath, eval_xpath_list

about = {
    "website": 'https://imgur.com/',
    "wikidata_id": 'Q355022',
    "official_api_documentation": 'https://api.imgur.com/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['images']
paging = True
time_range_support = True

base_url = "https://imgur.com"

results_xpath = "//div[contains(@class, 'cards')]/div[contains(@class, 'post')]"
url_xpath = "./a/@href"
title_xpath = "./a/img/@alt"
thumbnail_xpath = "./a/img/@src"


def request(query, params):
    time_range = params['time_range'] or 'all'
    args = {
        'q': query,
        'qs': 'thumbs',
        'p': params['pageno'] - 1,
    }
    params['url'] = f"{base_url}/search/score/{time_range}?{urlencode(args)}"
    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, results_xpath):
        thumbnail_src = extract_text(eval_xpath(result, thumbnail_xpath))
        img_src = thumbnail_src.replace("b.", ".")

        # that's a bug at imgur's side:
        # sometimes there's just no preview image, hence we skip the image
        if len(thumbnail_src) < 25:
            continue

        results.append(
            {
                'template': 'images.html',
                'url': base_url + extract_text(eval_xpath(result, url_xpath)),
                'title': extract_text(eval_xpath(result, title_xpath)),
                'img_src': img_src,
                'thumbnail_src': thumbnail_src,
            }
        )

    return results
