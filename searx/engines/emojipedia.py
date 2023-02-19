# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Emojipedia

Emojipedia is an emoji reference website which documents the meaning and
common usage of emoji characters in the Unicode Standard.  It is owned by Zedge
since 2021. Emojipedia is a voting member of The Unicode Consortium.[1]

[1] https://en.wikipedia.org/wiki/Emojipedia
"""

from urllib.parse import urlencode
from lxml import html

from searx.utils import (
    eval_xpath_list,
    eval_xpath_getindex,
    extract_text,
)

about = {
    "website": 'https://emojipedia.org',
    "wikidata_id": 'Q22908129',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = []
paging = False
time_range_support = False

base_url = 'https://emojipedia.org'
search_url = base_url + '/search/?{query}'


def request(query, params):
    params['url'] = search_url.format(
        query=urlencode({'q': query}),
    )
    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, "//ol[@class='search-results']/li"):

        extracted_desc = extract_text(eval_xpath_getindex(result, './/p', 0))

        if 'No results found.' in extracted_desc:
            break

        link = eval_xpath_getindex(result, './/h2/a', 0)

        url = base_url + link.attrib.get('href')
        title = extract_text(link)
        content = extracted_desc

        res = {'url': url, 'title': title, 'content': content}

        results.append(res)

    return results
