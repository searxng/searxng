# SPDX-License-Identifier: AGPL-3.0-or-later
"""Baidu Shopping"""

from urllib.parse import quote

from lxml import html
from searx.engines.xpath import extract_text

about = {
    "website": 'https://www.baidu.com',
    "wikidata_id": 'Q14772',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['shopping']
paging = True

search_url = 'https://www.baidu.com/s?wd={query}&ie=utf-8&rsv_dl=0_right_fyb_pchot_20811&pn={pageno}'

# XPath selectors for Baidu Shopping (using general search with shopping parameters)
results_xpath = '//div[contains(@class, "result")] | //div[contains(@class, "c-container")]'
url_xpath = './/h3//a/@href | .//a[contains(@class, "t")]/@href'
title_xpath = './/h3//a | .//a[contains(@class, "t")]'
content_xpath = './/div[contains(@class, "c-abstract")] | .//span[contains(@class, "c-abstract")] | .//p[contains(@class, "c-abstract")]'
price_xpath = './/span[contains(text(), "¥")] | .//span[contains(text(), "价格")] | .//em[contains(text(), "¥")]'
thumbnail_xpath = './/img[contains(@src, "http") or contains(@src, "data:image")]/@src'


def request(query, params):
    # Baidu uses pn parameter for pagination (0-based, 10 results per page)
    pn = (params['pageno'] - 1) * 10
    params['url'] = search_url.format(query=quote(query), pageno=pn)
    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)
    results_dom = dom.xpath(results_xpath)
    if not results_dom:
        return []

    # Process only first 15 results for reasonable speed
    for result_dom in results_dom[:15]:
        url = extract_text(result_dom.xpath(url_xpath))
        title = extract_text(result_dom.xpath(title_xpath))
        content = extract_text(result_dom.xpath(content_xpath))
        price = extract_text(result_dom.xpath(price_xpath))
        thumbnail = extract_text(result_dom.xpath(thumbnail_xpath))

        if not title or len(title.strip()) < 3:
            continue

        if url and not url.startswith('http'):
            url = 'https://www.baidu.com' + url

        if not url:
            continue

        # Format price - Baidu uses ¥ symbol
        if price and not price.startswith('¥'):
            price = '¥' + price.replace('from ', '').replace('to ', '')

        # Fix thumbnail URL
        if thumbnail and thumbnail.startswith('//'):
            thumbnail = 'https:' + thumbnail

        results.append(
            {
                'url': url,
                'title': title.strip(),
                'content': content,
                'price': price,
                'thumbnail': thumbnail,
                'template': 'products.html',
            }
        )

    return results