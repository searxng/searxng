# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Dictzone
"""

from lxml import html
from searx.utils import eval_xpath

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
url = 'https://dictzone.com/{from_lang}-{to_lang}-dictionary/{query}'
weight = 100

results_xpath = './/table[@id="r"]/tr'
https_support = True


def request(query, params):  # pylint: disable=unused-argument
    params['url'] = url.format(from_lang=params['from_lang'][2], to_lang=params['to_lang'][2], query=params['query'])

    return params


def response(resp):
    dom = html.fromstring(resp.text)

    translations = []
    for result in eval_xpath(dom, results_xpath)[1:]:
        try:
            from_result, to_results_raw = eval_xpath(result, './td')
        except:  # pylint: disable=bare-except
            continue

        to_results = []
        for to_result in eval_xpath(to_results_raw, './p/a'):
            t = to_result.text_content()
            if t.strip():
                to_results.append(to_result.text_content())

        translations.append(
            {
                'text': f"{from_result.text_content()} - {'; '.join(to_results)}",
            }
        )

    if translations:
        result = {
            'answer': translations[0]['text'],
            'translations': translations,
            'answer_type': 'translations',
        }

    return [result]
