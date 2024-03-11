# SPDX-License-Identifier: AGPL-3.0-or-later
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

base_url = 'https://emojipedia.org'
search_url = base_url + '/search?{query}'


def request(query, params):
    params['url'] = search_url.format(
        query=urlencode({'q': query}),
    )
    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, '//div[starts-with(@class, "EmojisList")]/a'):

        url = base_url + result.attrib.get('href')
        res = {'url': url, 'title': extract_text(result), 'content': ''}

        results.append(res)

    return results
