# SPDX-License-Identifier: AGPL-3.0-or-later
"""Amazon"""

from urllib.parse import urlencode, quote_plus
from lxml import html

from searx.utils import extract_text, eval_xpath, eval_xpath_list

about = {
    "website": 'https://www.amazon.com',
    "wikidata_id": 'Q3884',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['shopping']
paging = True

# Amazon search URL - using .com as default, can be configured per region
search_url = 'https://www.amazon.com/s?k={query}&page={pageno}'


def request(query, params):
    # Allow configuring different Amazon domains (e.g., amazon.co.uk, amazon.de)
    base_url = getattr(params, 'base_url', 'https://www.amazon.com')
    search_url_formatted = base_url + '/s?' + urlencode({
        'k': query,
        'page': params['pageno']
    })

    params['url'] = search_url_formatted
    params['headers']['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    # Amazon product results - multiple selectors for different layouts
    product_selectors = [
        '//div[contains(@data-component-type, "s-search-result")]',  # Standard search results
        '//div[contains(@class, "s-result-item")]',  # Alternative layout
        '//div[contains(@data-asin, "")]',  # Products with ASIN
    ]

    products = []
    for selector in product_selectors:
        products = eval_xpath_list(dom, selector)
        if products:
            break

    for product in products[:20]:  # Limit to 20 results
        # Extract title
        title_selectors = [
            './/h2[contains(@class, "a-size-mini")]/a/span',  # Product title
            './/span[contains(@class, "a-text-normal")]',  # Alternative title
            './/h2/a/span',  # Simple title link
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
            './/h2[contains(@class, "a-size-mini")]/a/@href',  # Title link
            './/a[contains(@class, "a-link-normal")]/@href',  # Product link
        ]

        url = None
        for sel in url_selectors:
            url_elem = eval_xpath(product, sel)
            if url_elem:
                url = url_elem[0] if isinstance(url_elem, list) else url_elem
                if url and not url.startswith('http'):
                    url = 'https://www.amazon.com' + url
                break

        if not url:
            continue

        # Extract price
        price_selectors = [
            './/span[contains(@class, "a-price-whole")]',  # Whole price
            './/span[contains(@class, "a-color-price")]',  # Price span
            './/span[contains(@class, "a-price")]',  # Price container
        ]

        price = None
        for sel in price_selectors:
            price_elem = eval_xpath(product, sel)
            if price_elem:
                price_text = extract_text(price_elem)
                if price_text:
                    # Combine whole and fractional parts if available
                    fraction_elem = eval_xpath(product, './/span[contains(@class, "a-price-fraction")]')
                    if fraction_elem:
                        fraction_text = extract_text(fraction_elem)
                        if fraction_text:
                            price_text += '.' + fraction_text
                    price = '$' + price_text
                    break

        # Extract content/description
        content_selectors = [
            './/div[contains(@class, "a-row")]/span[contains(@class, "a-size-base")]',  # Description
            './/span[contains(@class, "a-size-small")]',  # Additional info
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
            './/img[contains(@class, "s-image")]/@src',  # Product image
            './/img/@src',
        ]

        thumbnail = None
        for sel in thumbnail_selectors:
            thumb_elem = eval_xpath(product, sel)
            if thumb_elem:
                thumbnail = thumb_elem[0] if isinstance(thumb_elem, list) else thumb_elem
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