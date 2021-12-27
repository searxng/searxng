# SPDX-License-Identifier: AGPL-3.0-or-later
"""Wordnik (general)

"""

from lxml.html import fromstring
from searx.utils import extract_text
from searx.network import raise_for_httperror

# about
about = {
    "website": 'https://www.wordnik.com',
    "wikidata_id": 'Q8034401',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['general']
paging = False

URL = 'https://www.wordnik.com'
SEARCH_URL = URL + '/words/{query}'


def request(query, params):
    params['url'] = SEARCH_URL.format(query=query)
    logger.debug(f"query_url --> {params['url']}")
    return params


def response(resp):
    results = []

    raise_for_httperror(resp)
    dom = fromstring(resp.text)
    word = extract_text(dom.xpath('//*[@id="headword"]/text()'))

    definitions = []
    for src in dom.xpath('//*[@id="define"]//h3[@class="source"]'):
        src_text = extract_text(src).strip()
        if src_text.startswith('from '):
            src_text = src_text[5:]

        src_defs = []
        for def_item in src.xpath('following-sibling::ul[1]/li'):
            def_abbr = extract_text(def_item.xpath('.//abbr')).strip()
            def_text = extract_text(def_item).strip()
            if def_abbr:
                def_text = def_text[len(def_abbr) :].strip()
            src_defs.append((def_abbr, def_text))

        definitions.append((src_text, src_defs))

    if not definitions:
        return results

    infobox = ''
    for src_text, src_defs in definitions:
        infobox += f"<small>{src_text}</small>"
        infobox += "<ul>"
        for def_abbr, def_text in src_defs:
            if def_abbr:
                def_abbr += ": "
            infobox += f"<li><i>{def_abbr}</i> {def_text}</li>"
        infobox += "</ul>"

    results.append(
        {
            'infobox': word,
            'content': infobox,
        }
    )

    return results
