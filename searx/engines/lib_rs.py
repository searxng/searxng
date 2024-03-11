# SPDX-License-Identifier: AGPL-3.0-or-later
"""lib.rs (packages)"""

from urllib.parse import quote_plus
from lxml import html
from searx.utils import eval_xpath, eval_xpath_list, extract_text

about = {
    'website': 'https://lib.rs',
    'wikidata_id': 'Q113486010',
    'use_official_api': False,
    'require_api_key': False,
    'results': "HTML",
}

categories = ["it", "packages"]

base_url = 'https://lib.rs'

results_xpath = '/html/body/main/div/ol/li/a'
url_xpath = './@href'
title_xpath = './div[@class="h"]/h4'
content_xpath = './div[@class="h"]/p'
version_xpath = './div[@class="meta"]/span[contains(@class, "version")]'
download_count_xpath = './div[@class="meta"]/span[@class="downloads"]'
tags_xpath = './div[@class="meta"]/span[contains(@class, "k")]/text()'


def request(query, params):
    params['url'] = f"{base_url}/search?q={quote_plus(query)}"

    return params


def response(resp):
    results = []

    doc = html.fromstring(resp.text)

    for result in eval_xpath_list(doc, results_xpath):
        package_name = extract_text(eval_xpath(result, title_xpath))
        results.append(
            {
                'template': 'packages.html',
                'title': package_name,
                'url': base_url + extract_text(eval_xpath(result, url_xpath)),  # type: ignore
                'content': extract_text(eval_xpath(result, content_xpath)),
                'package_name': package_name,
                'version': extract_text(eval_xpath(result, version_xpath)),
                'popularity': extract_text(eval_xpath(result, download_count_xpath)),
                'tags': eval_xpath_list(result, tags_xpath),
            }
        )

    return results
