# SPDX-License-Identifier: AGPL-3.0-or-later
"""Geizhals is a German website to compare the price of a product on the
most common German shopping sites and find the lowest price.

The sorting of the search results can be influenced by the following additions
to the search term:

``asc`` or ``price``
  To sort by price in ascending order.

``desc``
  To sort by price in descending order.

"""

import re

from urllib.parse import urlencode
from lxml import html

from searx.utils import eval_xpath, eval_xpath_list, extract_text

about = {
    'website': 'https://geizhals.de',
    'wikidata_id': 'Q15977657',
    'use_official_api': False,
    'official_api_documentation': None,
    'require_api_key': False,
    'results': 'HTML',
    'language': 'de',
}
paging = True
categories = ['shopping']

base_url = "https://geizhals.de"
sort_order = 'relevance'

SORT_RE = re.compile(r"sort:(\w+)")
sort_order_map = {
    'relevance': None,
    'price': 'p',
    'asc': 'p',
    'desc': '-p',
}


def request(query, params):
    sort = None

    sort_order_path = SORT_RE.search(query)
    if sort_order_path:
        sort = sort_order_map.get(sort_order_path.group(1))
        query = SORT_RE.sub("", query)
        logger.debug(query)

    args = {
        'fs': query,
        'pg': params['pageno'],
        'toggle_all': 1,  # load item specs
        'sort': sort,
    }
    params['url'] = f"{base_url}/?{urlencode(args)}"

    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)
    for result in eval_xpath_list(dom, "//article[contains(@class, 'listview__item')]"):
        content = []
        for spec in eval_xpath_list(result, ".//div[contains(@class, 'specs-grid__item')]"):
            content.append(f"{extract_text(eval_xpath(spec, './dt'))}: {extract_text(eval_xpath(spec, './dd'))}")

        metadata = [
            extract_text(eval_xpath(result, ".//div[contains(@class, 'stars-rating-label')]")),
            extract_text(eval_xpath(result, ".//div[contains(@class, 'listview__offercount')]")),
        ]

        item = {
            'template': 'products.html',
            'url': (
                base_url + "/" + extract_text(eval_xpath(result, ".//a[contains(@class, 'listview__name-link')]/@href"))
            ),
            'title': extract_text(eval_xpath(result, ".//h3[contains(@class, 'listview__name')]")),
            'content': ' | '.join(content),
            'thumbnail': extract_text(eval_xpath(result, ".//img[contains(@class, 'listview__image')]/@src")),
            'metadata': ', '.join(item for item in metadata if item),
        }

        best_price = extract_text(eval_xpath(result, ".//a[contains(@class, 'listview__price-link')]")).split(" ")
        if len(best_price) > 1:
            item["price"] = f"Bestes Angebot: {best_price[1]}€"
        results.append(item)

    return results
