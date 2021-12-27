# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Yahoo (News)

Yahoo News is "English only" and do not offer localized nor language queries.

"""

# pylint: disable=invalid-name

import re
from urllib.parse import urlencode
from datetime import datetime, timedelta
from dateutil import parser
from lxml import html

from searx.utils import (
    eval_xpath_list,
    eval_xpath_getindex,
    extract_text,
)

from searx.engines.yahoo import parse_url

# about
about = {
    "website": 'https://news.yahoo.com',
    "wikidata_id": 'Q3044717',
    "official_api_documentation": 'https://developer.yahoo.com/api/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

language_support = False
time_range_support = False
safesearch = False
paging = True
categories = ['news']

# search-url
search_url = (
    # fmt: off
    'https://news.search.yahoo.com/search'
    '?{query}&b={offset}'
    # fmt: on
)

AGO_RE = re.compile(r'([0-9]+)\s*(year|month|week|day|minute|hour)')
AGO_TIMEDELTA = {
    'minute': timedelta(minutes=1),
    'hour': timedelta(hours=1),
    'day': timedelta(days=1),
    'week': timedelta(days=7),
    'month': timedelta(days=30),
    'year': timedelta(days=365),
}


def request(query, params):
    offset = (params['pageno'] - 1) * 10 + 1

    params['url'] = search_url.format(offset=offset, query=urlencode({'p': query}))
    logger.debug("query_url --> %s", params['url'])
    return params


def response(resp):
    results = []
    dom = html.fromstring(resp.text)

    # parse results
    for result in eval_xpath_list(dom, '//ol[contains(@class,"searchCenterMiddle")]//li'):

        url = eval_xpath_getindex(result, './/h4/a/@href', 0, None)
        if url is None:
            continue
        url = parse_url(url)
        title = extract_text(result.xpath('.//h4/a'))
        content = extract_text(result.xpath('.//p'))
        img_src = eval_xpath_getindex(result, './/img/@data-src', 0, None)

        item = {'url': url, 'title': title, 'content': content, 'img_src': img_src}

        pub_date = extract_text(result.xpath('.//span[contains(@class,"s-time")]'))
        ago = AGO_RE.search(pub_date)
        if ago:
            number = int(ago.group(1))
            delta = AGO_TIMEDELTA[ago.group(2)]
            pub_date = datetime.now() - delta * number
        else:
            try:
                pub_date = parser.parse(pub_date)
            except parser.ParserError:
                pub_date = None

        if pub_date is not None:
            item['publishedDate'] = pub_date
        results.append(item)

        for suggestion in eval_xpath_list(dom, '//div[contains(@class,"AlsoTry")]//td'):
            results.append({'suggestion': extract_text(suggestion)})

    return results
