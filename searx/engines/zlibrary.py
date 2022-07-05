# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Z-Library

Z-Library uses regional domains (see https://z-lib.org). Known ``base_url:``

- base_url: https://b-ok.cc
- base_url: https://de1lib.org
- base_url: https://booksc.eu does not have cover preview
- base_url: https://booksc.org does not have cover preview

"""

from urllib.parse import quote
from lxml import html

from searx.utils import extract_text, eval_xpath
from searx.network import get as http_get

# about
about = {
    "website": "https://z-lib.org",
    "wikidata_id": "Q104863992",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['files']
paging = True
base_url = ''


def init(engine_settings=None):
    global base_url  # pylint: disable=global-statement

    if "base_url" not in engine_settings:
        resp = http_get('https://z-lib.org', timeout=5.0)
        if resp.ok:
            dom = html.fromstring(resp.text)
            base_url = extract_text(
                eval_xpath(dom, './/a[contains(@class, "domain-check-link") and @data-mode="books"]/@href')
            )
    logger.debug("using base_url: %s" % base_url)


def request(query, params):
    search_url = base_url + '/s/{search_query}/?page={pageno}'
    params['url'] = search_url.format(search_query=quote(query), pageno=params['pageno'])
    return params


def response(resp):
    results = []
    dom = html.fromstring(resp.text)

    for item in dom.xpath('//div[@id="searchResultBox"]//div[contains(@class, "resItemBox")]'):
        result = {}

        result["url"] = base_url + item.xpath('(.//a[starts-with(@href, "/book/")])[1]/@href')[0]

        result["title"] = extract_text(eval_xpath(item, './/*[@itemprop="name"]'))

        year = extract_text(
            eval_xpath(item, './/div[contains(@class, "property_year")]//div[contains(@class, "property_value")]')
        )
        if year:
            year = '(%s) ' % year

        result[
            "content"
        ] = "{year}{authors}. {publisher}. Language: {language}. {file_type}. \
            Book rating: {book_rating}, book quality: {book_quality}".format(
            year=year,
            authors=extract_text(eval_xpath(item, './/div[@class="authors"]')),
            publisher=extract_text(eval_xpath(item, './/div[@title="Publisher"]')),
            file_type=extract_text(
                eval_xpath(item, './/div[contains(@class, "property__file")]//div[contains(@class, "property_value")]')
            ),
            language=extract_text(
                eval_xpath(
                    item, './/div[contains(@class, "property_language")]//div[contains(@class, "property_value")]'
                )
            ),
            book_rating=extract_text(eval_xpath(item, './/span[contains(@class, "book-rating-interest-score")]')),
            book_quality=extract_text(eval_xpath(item, './/span[contains(@class, "book-rating-quality-score")]')),
        )

        result["img_src"] = extract_text(eval_xpath(item, './/img[contains(@class, "cover")]/@data-src'))

        results.append(result)

    return results
