# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Bing (News)
"""

from urllib.parse import (
    urlencode,
    urlparse,
    parse_qsl,
    quote,
)
from datetime import datetime
from dateutil import parser

import babel
from lxml import etree, html
from lxml.etree import XPath

from searx.utils import (
    eval_xpath_getindex,
    eval_xpath,
)

# about
about = {
    "website": 'https://www.bing.com/news',
    "wikidata_id": 'Q2878637',
    "official_api_documentation": 'https://docs.microsoft.com/en-us/bing/search-apis/bing-news-search',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'RSS',
}

# engine dependent config
categories = ['news']
paging = True
time_range_support = True
supported_languages_url = 'https://docs.microsoft.com/en-us/bing/search-apis/bing-web-search/reference/market-codes'

# search-url
base_url = 'https://www.bing.com/news'

#search_string_with_time = 'news/search?{query}&first={offset}&qft=interval%3d"{interval}"&format=RSS'

#https://www.bing.com/news/search?q=foo&format=RSS
#https://www.bing.com/news/search?q=foo&setmkt=de&first=1&qft=interval%3D%227%22&format=RSS

# https://www.bing.com/news/search?q=foo&cc=en-UK&first=1&qft=interval%3D%227%22&format=RSS

time_range_dict = {'day': '7', 'week': '8', 'month': '9'}



def request(query, params):

    language = params['language']
    if language == 'all':
        language = 'en-US'
    locale = babel.Locale.parse(language, sep='-')

    req_args = {
        'q' : query,
        'format': 'RSS'
    }

    if locale.territory:
        market_code = locale.language + '-' + locale.territory
        if market_code in supported_languages:
            req_args['setmkt'] = market_code
        else:
            # Seems that language code can be used as market_code alternative,
            # when bing-news does not support the market_code (including
            # territory), but news results are better if there is a territory
            # given.
            req_args['setmkt'] = locale.language

    if params['pageno'] > 1:
        req_args['first'] =  (params['pageno'] - 1) * 10 + 1

    params['url'] = base_url + '/search?' + urlencode(req_args)

    interval = time_range_dict.get(params['time_range'])
    if interval:
        params['url'] += f'&qft=interval%3d"{interval}"'

    ac_lang = locale.language
    if locale.territory:
        ac_lang = "%s-%s,%s;q=0.5" % (locale.language, locale.territory, locale.language)
    logger.debug("headers.Accept-Language --> %s", ac_lang)
    params['headers']['Accept-Language'] = ac_lang
    params['headers']['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'

    return params


def response(resp):

    try:
        rss = etree.fromstring(resp.content)
    except etree.XMLSyntaxError:
        return []

    results = []
    namespaces = rss.nsmap

    for item in rss.xpath('./channel/item'):
        # url / title / content
        url = url_cleanup(eval_xpath_getindex(item, './link/text()', 0, default=None))
        title = eval_xpath_getindex(item, './title/text()', 0, default=url)
        content = eval_xpath_getindex(item, './description/text()', 0, default='')

        # publishedDate
        publishedDate = eval_xpath_getindex(item, './pubDate/text()', 0, default=None)
        try:
            publishedDate = parser.parse(publishedDate, dayfirst=False)
        except TypeError:
            publishedDate = datetime.now()
        except ValueError:
            publishedDate = datetime.now()

        # thumbnail
        thumbnail = eval_xpath_getindex(item, XPath('./News:Image/text()', namespaces=namespaces), 0, default=None)
        if thumbnail is not None:
            thumbnail = image_url_cleanup(thumbnail)

        # append result
        if thumbnail is not None:
            results.append(
                {'url': url, 'title': title, 'publishedDate': publishedDate, 'content': content, 'img_src': thumbnail}
            )
        else:
            results.append({'url': url, 'title': title, 'publishedDate': publishedDate, 'content': content})

    return results

def url_cleanup(url_string):
    """remove click"""

    parsed_url = urlparse(url_string)
    if parsed_url.netloc == 'www.bing.com' and parsed_url.path == '/news/apiclick.aspx':
        query = dict(parse_qsl(parsed_url.query))
        url_string = query.get('url', None)
    return url_string


def image_url_cleanup(url_string):
    """replace the http://*bing.com/th?id=... by https://www.bing.com/th?id=..."""

    parsed_url = urlparse(url_string)
    if parsed_url.netloc.endswith('bing.com') and parsed_url.path == '/th':
        query = dict(parse_qsl(parsed_url.query))
        url_string = "https://www.bing.com/th?id=" + quote(query.get('id'))
    return url_string


def _fetch_supported_languages(resp):
    """Market and language codes used by Bing Web Search API"""

    dom = html.fromstring(resp.text)

    market_codes = eval_xpath(
        dom,
        "//th[normalize-space(text()) = 'Market code']/../../../tbody/tr/td[3]/text()",
    )
    m_codes = set()
    for value in market_codes:
        m_codes.add(value)

    # country_codes =  eval_xpath(
    #     dom,
    #     "//th[normalize-space(text()) = 'Country Code']/../../../tbody/tr/td[2]/text()",
    # )
    # c_codes = set()
    # for value in country_codes:
    #     c_codes.add(value)

    # language_codes =  eval_xpath(
    #     dom,
    #     "//th[normalize-space(text()) = 'Language Code']/../../../tbody/tr/td[2]/text()",
    # )
    # l_codes = set()
    # for value in language_codes:
    #     l_codes.add(value)

    return list(m_codes)
