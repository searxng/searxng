# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bing Shopping"""

from urllib.parse import quote

from lxml import html
from zhensa.engines.xpath import extract_text

about = {
    "website": 'https://www.bing.com',
    "wikidata_id": 'Q182496',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['shopping']
paging = True

search_url = 'https://www.bing.com/shop?q={query}&first={pageno}'

# XPath selectors for Bing Shopping
results_xpath = '//div[contains(@class, "iusc")] | //div[contains(@class, "ius")] | //li[contains(@class, "iusc")]'
url_xpath = './/a[contains(@href, "/shop/product")]/@href'
title_xpath = './/h2//a | .//a[contains(@href, "/shop/product")] | .//div[contains(@class, "iusc")]//h2'
content_xpath = './/div[contains(@class, "iusc")]//p | .//div[contains(@class, "b_caption")]//p | .//span[contains(@class, "b_secondaryText")]'
price_xpath = './/span[contains(@class, "b_price")] | .//span[contains(@class, "price")] | .//span[contains(text(), "$")]'
thumbnail_xpath = './/img[contains(@src, "http") or contains(@src, "data:image")]/@src'


def request(query, params):
    # Bing uses 1-based indexing for first parameter
    first = (params['pageno'] - 1) * 10 + 1
    params['url'] = search_url.format(query=quote(query), pageno=first)
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
            url = 'https://www.bing.com' + url

        if not url:
            continue

        # Format price
        if price and not price.startswith('$'):
            price = '$' + price.replace('from ', '').replace('to ', '')

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