# SPDX-License-Identifier: AGPL-3.0-or-later
"""Alibaba"""

from urllib.parse import quote

from lxml import html
from zhensa.engines.xpath import extract_text

about = {
    "website": 'https://www.alibaba.com',
    "wikidata_id": 'Q1359568',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['shopping']
paging = True

search_url = 'https://www.alibaba.com/trade/search?fsb=y&IndexArea=product_en&CatId=&SearchText={query}&viewtype=G&page={pageno}'

# XPath selectors - generic and robust for Alibaba
results_xpath = '//div[contains(@class, "item-main")] | //div[contains(@class, "item-content")] | //div[contains(@data-aplus, "")]'
url_xpath = './/a/@href'
title_xpath = './/h2//a | .//a[contains(@class, "title")] | .//h2/a'
content_xpath = './/div[contains(@class, "stitle")] | .//div[contains(@class, "desc")] | .//span[contains(text(), "MOQ")]'
price_xpath = './/div[contains(@class, "price")]//span | .//span[contains(@class, "price")] | .//span[contains(text(), "$")]'
thumbnail_xpath = './/img/@src'


def request(query, params):
    params['url'] = search_url.format(query=quote(query), pageno=params['pageno'])
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
            url = 'https://www.alibaba.com' + url

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