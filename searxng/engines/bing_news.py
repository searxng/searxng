# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Bing (News)
"""

from datetime import datetime
from dateutil import parser
from urllib.parse import urlencode, urlparse, parse_qsl
from lxml import etree
from lxml.etree import XPath
from searxng.utils import match_language, eval_xpath_getindex
from searxng.engines.bing import language_aliases
from searxng.engines.bing import _fetch_supported_languages, supported_languages_url  # NOQA # pylint: disable=unused-import

# about
about = {
    "website": 'https://www.bing.com/news',
    "wikidata_id": 'Q2878637',
    "official_api_documentation": 'https://www.microsoft.com/en-us/bing/apis/bing-news-search-api',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'RSS',
}

# engine dependent config
categories = ['news']
paging = True
time_range_support = True

# search-url
base_url = 'https://www.bing.com/'
search_string = 'news/search?{query}&first={offset}&format=RSS'
search_string_with_time = 'news/search?{query}&first={offset}&qft=interval%3d"{interval}"&format=RSS'
time_range_dict = {'day': '7',
                   'week': '8',
                   'month': '9'}


# remove click
def url_cleanup(url_string):
    parsed_url = urlparse(url_string)
    if parsed_url.netloc == 'www.bing.com' and parsed_url.path == '/news/apiclick.aspx':
        query = dict(parse_qsl(parsed_url.query))
        return query.get('url', None)
    return url_string


# replace the http://*bing4.com/th?id=... by https://www.bing.com/th?id=...
def image_url_cleanup(url_string):
    parsed_url = urlparse(url_string)
    if parsed_url.netloc.endswith('bing4.com') and parsed_url.path == '/th':
        query = dict(parse_qsl(parsed_url.query))
        return "https://www.bing.com/th?id=" + query.get('id')
    return url_string


def _get_url(query, language, offset, time_range):
    if time_range in time_range_dict:
        search_path = search_string_with_time.format(
            query=urlencode({'q': query, 'setmkt': language}),
            offset=offset,
            interval=time_range_dict[time_range])
    else:
        # e.g. setmkt=de-de&setlang=de
        search_path = search_string.format(
            query=urlencode({'q': query, 'setmkt': language}),
            offset=offset)
    return base_url + search_path


# do search-request
def request(query, params):
    if params['time_range'] and params['time_range'] not in time_range_dict:
        return params

    offset = (params['pageno'] - 1) * 10 + 1

    if params['language'] == 'all':
        language = 'en-US'
    else:
        language = match_language(params['language'], supported_languages, language_aliases)

    params['url'] = _get_url(query, language, offset, params['time_range'])

    return params


# get response from search-request
def response(resp):
    results = []

    rss = etree.fromstring(resp.content)

    ns = rss.nsmap

    # parse results
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
        thumbnail = eval_xpath_getindex(item, XPath('./News:Image/text()', namespaces=ns), 0, default=None)
        if thumbnail is not None:
            thumbnail = image_url_cleanup(thumbnail)

        # append result
        if thumbnail is not None:
            results.append({'url': url,
                            'title': title,
                            'publishedDate': publishedDate,
                            'content': content,
                            'img_src': thumbnail})
        else:
            results.append({'url': url,
                            'title': title,
                            'publishedDate': publishedDate,
                            'content': content})

    # return results
    return results
