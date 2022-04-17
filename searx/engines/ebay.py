# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Ebay (Videos, Music, Files)
"""

from lxml import html
from searx.engines.xpath import extract_text
from urllib.parse import quote

# about
about = {
    "website": 'https://www.ebay.com',
    "wikidata_id": 'Q58024',
    "official_api_documentation": 'https://developer.ebay.com/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['shopping']
paging = True

# Set base_url in settings.yml in order to
# have the desired local TLD.
base_url = None
search_url = '/sch/i.html?_nkw={query}&_sacat={pageno}'

results_xpath = '//li[contains(@class, "s-item")]'
url_xpath = './/a[@class="s-item__link"]/@href'
title_xpath = './/h3[@class="s-item__title"]'
content_xpath = './/div[@span="SECONDARY_INFO"]'
price_xpath = './/div[contains(@class, "s-item__detail")]/span[@class="s-item__price"][1]/text()'
shipping_xpath = './/span[contains(@class, "s-item__shipping")]/text()'
source_country_xpath = './/span[contains(@class, "s-item__location")]/text()'
thumbnail_xpath = './/img[@class="s-item__image-img"]/@src'


def request(query, params):
    params['url'] = f'{base_url}' + search_url.format(query=quote(query), pageno=params['pageno'])
    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)
    results_dom = dom.xpath(results_xpath)
    if not results_dom:
        return []

    for result_dom in results_dom:
        url = extract_text(result_dom.xpath(url_xpath))
        title = extract_text(result_dom.xpath(title_xpath))
        content = extract_text(result_dom.xpath(content_xpath))
        price = extract_text(result_dom.xpath(price_xpath))
        shipping = extract_text(result_dom.xpath(shipping_xpath))
        source_country = extract_text(result_dom.xpath(source_country_xpath))
        thumbnail = extract_text(result_dom.xpath(thumbnail_xpath))

        if title == "":
            continue

        results.append(
            {
                'url': url,
                'title': title,
                'content': content,
                'price': price,
                'shipping': shipping,
                'source_country': source_country,
                'thumbnail': thumbnail,
                'template': 'products.html',
            }
        )

    return results
