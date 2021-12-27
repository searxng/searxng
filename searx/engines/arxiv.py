# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 ArXiV (Scientific preprints)
"""

from lxml import html
from datetime import datetime
from searx.utils import eval_xpath_list, eval_xpath_getindex

# about
about = {
    "website": 'https://arxiv.org',
    "wikidata_id": 'Q118398',
    "official_api_documentation": 'https://arxiv.org/help/api',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'XML-RSS',
}

categories = ['science']
paging = True

base_url = (
    'https://export.arxiv.org/api/query?search_query=all:' + '{query}&start={offset}&max_results={number_of_results}'
)

# engine dependent config
number_of_results = 10


def request(query, params):
    # basic search
    offset = (params['pageno'] - 1) * number_of_results

    string_args = dict(query=query, offset=offset, number_of_results=number_of_results)

    params['url'] = base_url.format(**string_args)

    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.content)

    for entry in eval_xpath_list(dom, '//entry'):
        title = eval_xpath_getindex(entry, './/title', 0).text

        url = eval_xpath_getindex(entry, './/id', 0).text

        content_string = '{doi_content}{abstract_content}'

        abstract = eval_xpath_getindex(entry, './/summary', 0).text

        #  If a doi is available, add it to the snipppet
        doi_element = eval_xpath_getindex(entry, './/link[@title="doi"]', 0, default=None)
        doi_content = doi_element.text if doi_element is not None else ''
        content = content_string.format(doi_content=doi_content, abstract_content=abstract)

        if len(content) > 300:
            content = content[0:300] + "..."
        # TODO: center snippet on query term

        publishedDate = datetime.strptime(eval_xpath_getindex(entry, './/published', 0).text, '%Y-%m-%dT%H:%M:%SZ')

        res_dict = {'url': url, 'title': title, 'publishedDate': publishedDate, 'content': content}

        results.append(res_dict)

    return results
