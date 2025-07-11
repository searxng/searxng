# SPDX-License-Identifier: AGPL-3.0-or-later
"""Wordnik (general)"""

from lxml.html import fromstring
from searx.utils import extract_text

from searx.result_types import EngineResults

# about
about = {
    "website": 'https://www.wordnik.com',
    "wikidata_id": 'Q8034401',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['dictionaries', 'define']
paging = False


def request(query, params):
    params['url'] = f"https://www.wordnik.com/words/{query}"
    return params


def response(resp):
    results = EngineResults()

    dom = fromstring(resp.text)

    for src in dom.xpath('//*[@id="define"]//h3[@class="source"]'):
        item = results.types.Translations.Item(text="")
        for def_item in src.xpath('following-sibling::ul[1]/li'):
            def_abbr = extract_text(def_item.xpath('.//abbr')).strip()
            def_text = extract_text(def_item).strip()
            if def_abbr:
                def_text = def_text[len(def_abbr) :].strip()

            # use first result as summary
            if not item.text:
                item.text = def_text
            item.definitions.append(def_text)

        results.add(results.types.Translations(translations=[item], url=resp.search_params["url"]))

    return results
