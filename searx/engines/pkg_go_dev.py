# SPDX-License-Identifier: AGPL-3.0-or-later
"""pkg.go.dev (packages)"""

import re
from urllib.parse import urlencode
from dateutil import parser

import babel
import flask_babel
from lxml import html
from searx.utils import eval_xpath, eval_xpath_list, extract_text

about = {
    'website': 'https://pkg.go.dev/',
    'use_official_api': False,
    'official_api_documentation': None,
    'require_api_key': False,
    'results': 'HTML',
}

categories = ["packages", "it"]

base_url = "https://pkg.go.dev"
max_result_count = 50

results_xpath = '/html/body/main/div[contains(@class,"SearchResults")]/div[not(@class)]/div[@class="SearchSnippet"]'
url_xpath = './div[@class="SearchSnippet-headerContainer"]/h2/a/@href'
title_xpath = './div[@class="SearchSnippet-headerContainer"]/h2/a/text()'
package_name_xpath = './div[@class="SearchSnippet-headerContainer"]/h2/a/span/text()'
version_xpath = './div[contains(@class, "SearchSnippet-infoLabel")]/span/strong[1]/text()'
updated_xpath = (
    './div[contains(@class, "SearchSnippet-infoLabel")]/span/span[@data-test-id="snippet-published"]/strong/text()'
)
content_xpath = './p[@class="SearchSnippet-synopsis"]'
popularity_xpath = './div[contains(@class, "SearchSnippet-infoLabel")]/a/strong/text()'
license_name_xpath = './div[contains(@class, "SearchSnippet-infoLabel")]/span[@data-test-id="snippet-license"]/a/text()'
license_url_xpath = './div[contains(@class, "SearchSnippet-infoLabel")]/span[@data-test-id="snippet-license"]/a/@href'


def request(query, params):
    args = {
        'q': query,
        'm': 'package',
        'limit': max_result_count,
    }
    params['url'] = f"{base_url}/search?{urlencode(args)}"

    return params


def response(resp):
    results = []

    doc = html.fromstring(resp.text)

    for result in eval_xpath_list(doc, results_xpath):
        publishedDate = extract_text(eval_xpath(result, updated_xpath))
        try:
            publishedDate = parser.parse(publishedDate)
        except parser.ParserError:
            publishedDate = None

        # 110n 15,000.00 (EN) --> 15.000,00 (DE)
        popularity = extract_text(eval_xpath(result, popularity_xpath)).strip()
        popularity = babel.numbers.parse_decimal(popularity, locale='en_US')
        # popularity is of type str ..
        popularity = flask_babel.format_decimal(popularity)

        results.append(
            {
                'template': 'packages.html',
                'url': base_url + extract_text(eval_xpath(result, url_xpath)),
                'title': extract_text(eval_xpath(result, title_xpath)),
                'content': extract_text(eval_xpath(result, content_xpath)),
                'package_name': re.sub(r"\(|\)", "", extract_text(eval_xpath(result, package_name_xpath))),
                'version': extract_text(eval_xpath(result, version_xpath)),
                'popularity': popularity,
                'license_name': extract_text(eval_xpath(result, license_name_xpath)),
                'license_url': base_url + extract_text(eval_xpath(result, license_url_xpath)),
                'publishedDate': publishedDate,
            }
        )

    return results
