# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Google Shopping"""

from urllib.parse import urlencode
from lxml import html
from searx.utils import extract_text

from searx.engines.google import (
    get_lang_info,
    detect_google_sorry,
)

# pylint: disable=unused-import
from searx.engines.google import (
    supported_languages_url,
    _fetch_supported_languages,
)

# pylint: enable=unused-import

about = {
    "website": "https://shopping.google.com",
    "wikidata_id": "Q1433417",
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

categories = ["shopping"]
paging = True

search_url = "https://shopping.google.com/search?{query}&tbm=shop&start={pageno}"

results_xpath = '//div[@class="op4oU"]/div[@role="listitem" and @style=""]'
title_xpath = './/h2[@class="MPhl6c pqv9ne azTb0d ulfEhd YAEPj XkyFEf"]'
url_xpath = './/a[@class="loT5Qd kneS6c"]/@href'
price_xpath = './/span[@class="aZK3gc Lhpu7d"]'
thumbnail_xpath = './/img[@class="Ws3Esf"]/@src'
shipping_xpath = './/div[@class="KT7Ysc"]'
site_xpath = './/div[@class="X8HN5e FAZYFf ApBhXe"]'
condition_xpath = './/span[@class="JkJxid HFeBod"]'


def request(query, params):
    pageno = (params["pageno"] - 1) * 60
    lang_info = get_lang_info(params, supported_languages, language_aliases, False)

    params["url"] = search_url.format(query=urlencode({"q": query}), pageno=pageno)

    params['headers'].update(lang_info['headers'])
    params['headers']['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'

    params['cookies']['CONSENT'] = "YES+"

    return params


def response(resp):
    results = []

    detect_google_sorry(resp)

    dom = html.fromstring(resp.text)

    res = dom.xpath(results_xpath)
    for result in res:
        url = extract_text(result.xpath(url_xpath))
        title = extract_text(result.xpath(title_xpath))
        price = extract_text(result.xpath(price_xpath))
        thumbnail = extract_text(result.xpath(thumbnail_xpath))
        shipping = extract_text(result.xpath(shipping_xpath))
        site = extract_text(result.xpath(site_xpath))
        condition = extract_text(result.xpath(condition_xpath))

        results.append(
            {
                "url": url,
                "title": title,
                "price": price,
                "thumbnail": thumbnail,
                "template": "products.html",
                "shipping": shipping,
                "content": condition,
                "source_country": site,
            }
        )

    return results
