# SPDX-License-Identifier: AGPL-3.0-or-later
"""Flipkart"""

from urllib.parse import urlencode, quote_plus
from lxml import html

from searx.utils import extract_text, eval_xpath, eval_xpath_list

about = {
    "website": 'https://www.flipkart.com',
    "wikidata_id": 'Q612740',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['shopping']
paging = True

search_url = 'https://www.flipkart.com/search?q={query}&page={pageno}'


def request(query, params):
    params['url'] = search_url.format(query=quote_plus(query), pageno=params['pageno'])
    params['headers']['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    # Flipkart product results
    product_selectors = [
        '//*[@data-id]',  # Products with data-id attribute
        '//div[contains(@class, "_1AtVbE")]//div[contains(@class, "_13oc-S")]',  # Product containers
    ]

    products = []
    for selector in product_selectors:
        products = eval_xpath_list(dom, selector)
        if products:
            break

    for product in products[:20]:  # Limit to 20 results
        # Extract title
        title_selectors = [
            './/div[contains(@class, "_4rR01T")]',  # Product title
            './/a[contains(@class, "s1Q9rs")]',  # Alternative title
            './/img/@alt',  # Image alt text as fallback
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
            './/a[contains(@class, "_1fQZEK")]/@href',  # Product link
            './/a[contains(@class, "s1Q9rs")]/@href',  # Alternative link
        ]

        url = None
        for sel in url_selectors:
            url_elem = eval_xpath(product, sel)
            if url_elem:
                url = url_elem[0] if isinstance(url_elem, list) else url_elem
                if url and not url.startswith('http'):
                    url = 'https://www.flipkart.com' + url
                break

        if not url:
            continue

        # Extract price
        price_selectors = [
            './/div[contains(@class, "_30jeq3")]',  # Current price
            './/div[contains(@class, "_3I9_wc")]',  # Original price
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
            './/div[contains(@class, "_3Djpdu")]',  # Product description
            './/ul[contains(@class, "_1xgFaf")]',  # Feature list
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
            './/img[contains(@class, "_396cs4")]/@src',  # Product image
            './/img/@src',
        ]

        thumbnail = None
        for sel in thumbnail_selectors:
            thumb_elem = eval_xpath(product, sel)
            if thumb_elem:
                thumbnail = thumb_elem[0] if isinstance(thumb_elem, list) else thumb_elem
                if thumbnail and thumbnail.startswith('//'):
                    thumbnail = 'https:' + thumbnail
                break

        results.append({
            'url': url,
            'title': title,
            'content': content or '',
            'price': price,
            'thumbnail': thumbnail,
            'template': 'products.html',
        })

    return results