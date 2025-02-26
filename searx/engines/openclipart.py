# SPDX-License-Identifier: AGPL-3.0-or-later
"""OpenClipArt (images)"""

from urllib.parse import urlencode
from lxml import html
from searx.utils import extract_text, eval_xpath, eval_xpath_list

about = {
    "website": 'https://openclipart.org/',
    "wikidata_id": 'Q979593',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['images']
paging = True

base_url = "https://openclipart.org"


def request(query, params):
    args = {
        'query': query,
        'p': params['pageno'],
    }
    params['url'] = f"{base_url}/search/?{urlencode(args)}"
    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, "//div[contains(@class, 'gallery')]/div[contains(@class, 'artwork')]"):
        results.append(
            {
                'template': 'images.html',
                'url': base_url + extract_text(eval_xpath(result, "./a/@href")),
                'title': extract_text(eval_xpath(result, "./a/img/@alt")),
                'img_src': base_url + extract_text(eval_xpath(result, "./a/img/@src")),
            }
        )

    return results
