# SPDX-License-Identifier: AGPL-3.0-or-later
"""Svgrepo (images)
"""

from lxml import html
from searx.utils import extract_text, eval_xpath, eval_xpath_list

about = {
    "website": 'https://www.svgrepo.com',
    "official_api_documentation": 'https://svgapi.com',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

paging = True
categories = ['images']
base_url = "https://www.svgrepo.com"

results_xpath = "//div[@class='style_nodeListing__7Nmro']/div"
url_xpath = ".//a/@href"
title_xpath = ".//a/@title"
img_src_xpath = ".//img/@src"


def request(query, params):
    params['url'] = f"{base_url}/vectors/{query}/{params['pageno']}/"
    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)
    for result in eval_xpath_list(dom, results_xpath):
        results.append(
            {
                'template': 'images.html',
                'url': base_url + extract_text(eval_xpath(result, url_xpath)),
                'title': extract_text(eval_xpath(result, title_xpath)).replace(" SVG File", "").replace("Show ", ""),
                'img_src': extract_text(eval_xpath(result, img_src_xpath)),
            }
        )

    return results
