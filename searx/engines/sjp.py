# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Słownik Języka Polskiego

Dictionary of the polish language from PWN (sjp.pwn)
"""

from lxml.html import fromstring
from searx import logger
from searx.utils import extract_text
from searx.network import raise_for_httperror

logger = logger.getChild('sjp engine')

# about
about = {
    "website": 'https://sjp.pwn.pl',
    "wikidata_id": 'Q55117369',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
    "language": 'pl',
}

categories = ['dictionaries']
paging = False

URL = 'https://sjp.pwn.pl'
SEARCH_URL = URL + '/szukaj/{query}.html'

word_xpath = '//div[@class="query"]'
dict_xpath = [
    '//div[@class="wyniki sjp-so-wyniki sjp-so-anchor"]',
    '//div[@class="wyniki sjp-wyniki sjp-anchor"]',
    '//div[@class="wyniki sjp-doroszewski-wyniki sjp-doroszewski-anchor"]',
]


def request(query, params):
    params['url'] = SEARCH_URL.format(query=query)
    logger.debug(f"query_url --> {params['url']}")
    return params


def response(resp):
    results = []

    raise_for_httperror(resp)
    dom = fromstring(resp.text)
    word = extract_text(dom.xpath(word_xpath))

    definitions = []

    for dict_src in dict_xpath:
        for src in dom.xpath(dict_src):
            src_text = extract_text(src.xpath('.//span[@class="entry-head-title"]/text()')).strip()

            src_defs = []
            for def_item in src.xpath('.//div[contains(@class, "ribbon-element")]'):
                if def_item.xpath('./div[@class="znacz"]'):
                    sub_defs = []
                    for def_sub_item in def_item.xpath('./div[@class="znacz"]'):
                        def_sub_text = extract_text(def_sub_item).lstrip('0123456789. ')
                        sub_defs.append(def_sub_text)
                    src_defs.append((word, sub_defs))
                else:
                    def_text = extract_text(def_item).strip()
                    def_link = def_item.xpath('./span/a/@href')
                    if 'doroszewski' in def_link[0]:
                        def_text = f"<a href='{def_link[0]}'>{def_text}</a>"
                    src_defs.append((def_text, ''))

            definitions.append((src_text, src_defs))

    if not definitions:
        return results

    infobox = ''
    for src in definitions:
        infobox += f"<div><small>{src[0]}</small>"
        infobox += "<ul>"
        for (def_text, sub_def) in src[1]:
            infobox += f"<li>{def_text}</li>"
            if sub_def:
                infobox += "<ol>"
                for sub_def_text in sub_def:
                    infobox += f"<li>{sub_def_text}</li>"
                infobox += "</ol>"
        infobox += "</ul></div>"

    results.append(
        {
            'infobox': word,
            'content': infobox,
        }
    )

    return results
