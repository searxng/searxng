# SPDX-License-Identifier: AGPL-3.0-or-later
"""Alibaba"""

from urllib.parse import urlencode, quote_plus
from lxml import html

from searx.utils import extract_text, eval_xpath, eval_xpath_list

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


def request(query, params):
    params['url'] = search_url.format(query=quote_plus(query), pageno=params['pageno'])
    params['headers']['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    # Alibaba product results
    product_selectors = [
        '//div[contains(@class, "organic-list")]/div[contains(@class, "item-main")]',  # Main product containers
        '//div[contains(@class, "item-content")]',  # Alternative containers
        '//div[contains(@data-aplus, "")]',  # Products with tracking data
    ]

    products = []
    for selector in product_selectors:
        products = eval_xpath_list(dom, selector)
        if products:
            break

    for product in products[:20]:  # Limit to 20 results
        # Extract title
        title_selectors = [
            './/h2[contains(@class, "title")]/a',  # Product title link
            './/a[contains(@class, "title")]',  # Title link
            './/h2/a',  # Simple title
        ]

        title = None
        for sel in title_selectors:
            title_elem = eval_xpath(product, sel)
            if title_elem:
                title = extract_text(title_elem)
                if title:
                    break

        if not title:
            continue

        # Extract URL
        url_selectors = [
            './/h2[contains(@class, "title")]/a/@href',  # Title link href
            './/a[contains(@class, "title")]/@href',  # Alternative link
        ]

        url = None
        for sel in url_selectors:
            url_elem = eval_xpath(product, sel)
            if url_elem:
                url = url_elem[0] if isinstance(url_elem, list) else url_elem
                if url and not url.startswith('http'):
                    url = 'https://www.alibaba.com' + url
                break

        if not url:
            continue

        # Extract price
        price_selectors = [
            './/div[contains(@class, "price")]/span',  # Price span
            './/span[contains(@class, "price")]',  # Price element
            './/b[contains(text(), "$")]',  # Price in bold
        ]

        price = None
        for sel in price_selectors:
            price_elem = eval_xpath(product, sel)
            if price_elem:
                price = extract_text(price_elem)
                if price:
                    break

        # Extract content/description
        content_selectors = [
            './/div[contains(@class, "stitle")]',  # Subtitle/description
            './/div[contains(@class, "desc")]',  # Description
            './/p[contains(@class, "desc")]',  # Paragraph description
        ]

        content = None
        for sel in content_selectors:
            content_elem = eval_xpath(product, sel)
            if content_elem:
                content = extract_text(content_elem)
                if content:
                    break

        # Extract thumbnail
        thumbnail_selectors = [
            './/img[contains(@class, "pic")]/@src',  # Product image
            './/img/@src',  # Any image
        ]

        thumbnail = None
        for sel in thumbnail_selectors:
            thumb_elem = eval_xpath(product, sel)
            if thumb_elem:
                thumbnail = thumb_elem[0] if isinstance(thumb_elem, list) else thumb_elem
                if thumbnail and thumbnail.startswith('//'):
                    thumbnail = 'https:' + thumbnail
                break

        # Extract minimum order quantity (MOQ)
        moq_selectors = [
            './/span[contains(text(), "MOQ")]',  # MOQ text
            './/div[contains(text(), "MOQ")]',  # MOQ in div
        ]

        moq = None
        for sel in moq_selectors:
            moq_elem = eval_xpath(product, sel)
            if moq_elem:
                moq = extract_text(moq_elem)
                if moq:
                    break

        # Combine content with MOQ if available
        if moq and content:
            content = f"{content} | {moq}"
        elif moq:
            content = moq

        results.append({
            'url': url,
            'title': title,
            'content': content or '',
            'price': price,
            'thumbnail': thumbnail,
            'template': 'products.html',
        })

    return results