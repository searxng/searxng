# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Dictzone
"""

import urllib.parse
from lxml import html

from searx.utils import eval_xpath, extract_text
from searx.result_types import EngineResults
from searx.network import get as http_get  # https://github.com/searxng/searxng/issues/762

# about
about = {
    "website": 'https://dictzone.com/',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

engine_type = 'online_dictionary'
categories = ['general', 'translate']
base_url = "https://dictzone.com"
weight = 100
https_support = True


def request(query, params):  # pylint: disable=unused-argument

    from_lang = params["from_lang"][2]  # "english"
    to_lang = params["to_lang"][2]  # "german"
    query = params["query"]

    params["url"] = f"{base_url}/{from_lang}-{to_lang}-dictionary/{urllib.parse.quote_plus(query)}"
    return params


def _clean_up_node(node):
    for x in ["./i", "./span", "./button"]:
        for n in node.xpath(x):
            n.getparent().remove(n)


def response(resp) -> EngineResults:
    results = EngineResults()

    item_list = []

    if not resp.ok:
        return results

    dom = html.fromstring(resp.text)

    for result in eval_xpath(dom, ".//table[@id='r']//tr"):

        # each row is an Translations.Item

        td_list = result.xpath("./td")
        if len(td_list) != 2:
            # ignore header columns "tr/th"
            continue

        col_from, col_to = td_list
        _clean_up_node(col_from)

        text = f"{extract_text(col_from)}"

        synonyms = []
        p_list = col_to.xpath(".//p")

        for i, p_item in enumerate(p_list):

            smpl: str = extract_text(p_list[i].xpath("./i[@class='smpl']"))  # type: ignore
            _clean_up_node(p_item)
            p_text: str = extract_text(p_item)  # type: ignore

            if smpl:
                p_text += " // " + smpl

            if i == 0:
                text += f" : {p_text}"
                continue

            synonyms.append(p_text)

        item = results.types.Translations.Item(text=text, synonyms=synonyms)
        item_list.append(item)

    # the "autotranslate" of dictzone is loaded by the JS from URL:
    #  https://dictzone.com/trans/hello%20world/en_de

    from_lang = resp.search_params["from_lang"][1]  # "en"
    to_lang = resp.search_params["to_lang"][1]  # "de"
    query = resp.search_params["query"]

    # works only sometimes?
    autotranslate = http_get(f"{base_url}/trans/{query}/{from_lang}_{to_lang}", timeout=1.0)
    if autotranslate.ok and autotranslate.text:
        item_list.insert(0, results.types.Translations.Item(text=autotranslate.text))

    if item_list:
        results.add(results.types.Translations(translations=item_list, url=resp.search_params["url"]))
    return results
