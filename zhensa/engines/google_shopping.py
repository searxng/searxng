# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google Shopping"""

from urllib.parse import quote

from lxml import html
from zhensa.engines.xpath import extract_text

about = {
    "website": 'https://www.google.com',
    "wikidata_id": 'Q9366',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['shopping']
paging = True

search_url = 'https://www.google.com/search?tbm=shop&q={query}&start={pageno}0'

# XPath selectors for Google Shopping
results_xpath = '//div[contains(@class, "sh-dgr__gr-auto")] | //div[contains(@class, "sh-dlr__list-result")] | //div[contains(@data-docid, "")]'
url_xpath = './/a[contains(@href, "/shopping/product/")]/@href'
title_xpath = './/h3[contains(@class, "tAxDx")] | .//span[contains(@class, "A8OWCb")] | .//a[contains(@href, "/shopping/product/")]//span'
content_xpath = './/div[contains(@class, "aULzUe")] | .//span[contains(@class, "a8Pemb")]'
price_xpath = './/span[contains(@class, "a8Pemb")] | .//span[contains(@class, "T14wmb")] | .//span[contains(text(), "$")]'
thumbnail_xpath = './/img[contains(@src, "data:image") or contains(@src, "http")]/@src'


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
            url = 'https://www.google.com' + url

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