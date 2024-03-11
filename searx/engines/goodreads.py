# SPDX-License-Identifier: AGPL-3.0-or-later
"""Goodreads (books)
"""

from urllib.parse import urlencode

from lxml import html
from searx.utils import extract_text, eval_xpath, eval_xpath_list

about = {
    'website': 'https://www.goodreads.com',
    'wikidata_id': 'Q2359213',
    'official_api_documentation': None,
    'use_official_api': False,
    'require_api_key': False,
    'results': 'HTML',
}
categories = []
paging = True

base_url = "https://www.goodreads.com"

results_xpath = "//table//tr"
thumbnail_xpath = ".//img[contains(@class, 'bookCover')]/@src"
url_xpath = ".//a[contains(@class, 'bookTitle')]/@href"
title_xpath = ".//a[contains(@class, 'bookTitle')]"
author_xpath = ".//a[contains(@class, 'authorName')]"
info_text_xpath = ".//span[contains(@class, 'uitext')]"


def request(query, params):
    args = {
        'q': query,
        'page': params['pageno'],
    }

    params['url'] = f"{base_url}/search?{urlencode(args)}"
    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, results_xpath):
        results.append(
            {
                'url': base_url + extract_text(eval_xpath(result, url_xpath)),
                'title': extract_text(eval_xpath(result, title_xpath)),
                'img_src': extract_text(eval_xpath(result, thumbnail_xpath)),
                'content': extract_text(eval_xpath(result, info_text_xpath)),
                'metadata': extract_text(eval_xpath(result, author_xpath)),
            }
        )

    return results
