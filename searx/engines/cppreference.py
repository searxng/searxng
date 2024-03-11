# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cppreference
"""
from lxml import html
from searx.utils import eval_xpath


about = {
    "website": "https://en.cppreference.com/",
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}


categories = ['it']
url = 'https://en.cppreference.com/'
search_url = url + 'mwiki/index.php?title=Special%3ASearch&search={query}'


def request(query, params):
    params['url'] = search_url.format(query=query)
    return query


def response(resp):
    results = []
    dom = html.fromstring(resp.text)
    for result in eval_xpath(dom, '//div[contains(@class, "mw-search-result-heading")]'):
        results.append(
            {
                'url': url + eval_xpath(result, './/a/@href')[0],
                'title': eval_xpath(result, './/a/text()')[0],
            }
        )
    return results
