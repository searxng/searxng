# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Bing (Images)

"""

from json import loads
from urllib.parse import urlencode
from lxml import html
import babel

from searx.engines.bing import (  # pylint: disable=unused-import
    _fetch_supported_languages,
    supported_languages_url,
)

# about
about = {
    "website": 'https://www.bing.com/images',
    "wikidata_id": 'Q182496',
    "official_api_documentation": 'https://www.microsoft.com/en-us/bing/apis/bing-image-search-api',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['images', 'web']
paging = True
supported_languages_url = 'https://www.bing.com/account/general'
number_of_results = 28

time_range_support = True
time_range_string = '&qft=+filterui:age-lt{interval}'
time_range_dict = {'day': '1440', 'week': '10080', 'month': '43200', 'year': '525600'}

safesearch = True
safesearch_types = {2: 'STRICT', 1: 'DEMOTE', 0: 'OFF'}

# search-url
base_url = 'https://www.bing.com/'

# https://www.bing.com/images/search?q=london&FORM=HDRSC2

inital_query = (
    # fmt: off
    'images/search'
    '?{query}'
    '&count={count}'
    '&tsc=ImageHoverTitle'
    # fmt: on
)

page_query = (
    # fmt: off
    'images/async'
    '?{query}'
    '&count={count}'
    '&first={first}'
    '&tsc=ImageHoverTitle'
    # fmt: on
)

# do search-request
def request(query, params):

    language = params['language']
    if language == 'all':
        language = 'en-US'
    locale = babel.Locale.parse(language, sep='-')

    # query and paging

    bing_language = ''
    if locale.language in supported_languages:
        bing_language = 'language:%s ' % locale.language
    query_str = urlencode({'q': bing_language + query})

    if params['pageno'] == 1:
        search_path = inital_query.format(
            query=query_str, count=number_of_results
        )
    else:
        offset = ((params['pageno'] - 1) * number_of_results)
        search_path = page_query.format(
            query=query_str, count=number_of_results, first=offset
        )

    params['url'] = base_url + search_path

    # safesearch

    # bing-imgae results are SafeSearch by defautl, setting the '&adlt_set='
    # parameter seems not enogh to change the default.  I assume there is some
    # age verification by a cookie and/or session ID is needed to disable the
    # SafeSearch
    params['url'] += '&adlt_set=%s' % safesearch_types.get(params['safesearch'], 'off').lower()

    # cookies

    # On bing-video users can select a SafeSearch level what is saved in a
    # cookies, trying to set this coockie here seems not to work, may be the
    # cookie needs more values (e.g. a session ID or something like this where a
    # age validation is noted)

    # SRCHHPGUSR = [
    #     'SRCHLANG=%s' % locale.language,
    #     'ADLT=%s' % safesearch_types.get(params['safesearch'], 'OFF')
    # ]
    # params['cookies']['SRCHHPGUSR'] = '&'.join(SRCHHPGUSR) + ';'
    # logger.debug("cookies SRCHHPGUSR=%s", params['cookies']['SRCHHPGUSR'])

    # time range

    time_range = time_range_dict.get(params['time_range'])
    if time_range:
        params['url'] += time_range_string.format(interval=time_range)

    # language & locale

    ac_lang = locale.language
    if locale.territory:
        ac_lang = "%s-%s,%s;q=0.5" % (locale.language, locale.territory, locale.language)
    logger.debug("headers.Accept-Language --> %s", ac_lang)
    params['headers']['Accept-Language'] = ac_lang
    params['headers']['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'

    return params


# get response from search-request
def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    # parse results
    for result in dom.xpath('//div[@class="imgpt"]'):
        img_format = result.xpath('./div[contains(@class, "img_info")]/span/text()')[0]
        # Microsoft seems to experiment with this code so don't make the path too specific,
        # just catch the text section for the first anchor in img_info assuming this to be
        # the originating site.
        source = result.xpath('./div[contains(@class, "img_info")]//a/text()')[0]

        m = loads(result.xpath('./a/@m')[0])

        # strip 'Unicode private use area' highlighting, they render to Tux
        # the Linux penguin and a standing diamond on my machine...
        title = m.get('t', '').replace('\ue000', '').replace('\ue001', '')
        results.append(
            {
                'template': 'images.html',
                'url': m['purl'],
                'thumbnail_src': m['turl'],
                'img_src': m['murl'],
                'content': '',
                'title': title,
                'source': source,
                'img_format': img_format,
            }
        )

    return results
