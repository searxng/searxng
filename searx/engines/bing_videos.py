# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Bing (Videos)

"""

from json import loads
from urllib.parse import urlencode
from lxml import html
import babel

from searx.engines.bing import (  # pylint: disable=unused-import
    _fetch_supported_languages,
    supported_languages_url,
)

about = {
    "website": 'https://www.bing.com/videos',
    "wikidata_id": 'Q4914152',
    "official_api_documentation": 'https://www.microsoft.com/en-us/bing/apis/bing-video-search-api',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['videos', 'web']
paging = True
number_of_results = 28

time_range_support = True
time_range_string = '&qft=+filterui:videoage-lt{interval}'
time_range_dict = {'day': '1440', 'week': '10080', 'month': '43200', 'year': '525600'}

safesearch = True
safesearch_types = {2: 'STRICT', 1: 'DEMOTE', 0: 'OFF'}  # cookie: ADLT=STRICT

base_url = 'https://www.bing.com/'

inital_query = (
    # fmt: off
    'videos/search'
    '?{query}'
    '&count={count}'
    '&scope=video'
    '&FORM=QBLH'
    # fmt: on
)

page_query = (
    # fmt: off
    'videos/search'
    '?{query}'
    '&count={count}'
    '&first={first}'
    '&scope=video'
    '&FORM=QBVR'
    # fmt: on
)

# do search-request
def request(query, params):
    """Results from bing video depend on the HTTP Accept-Language header.  There is
    no option or filter to search videos by language.

    """

    language = params['language']
    if language == 'all':
        language = 'en-US'
    locale = babel.Locale.parse(language, sep='-')

    # query and paging

    query_str = urlencode({'q': query})

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

    # bing-video results are SafeSearch by defautl, setting the '&adlt_set='
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

    for result in dom.xpath('//div[@class="dg_u"]'):
        metadata = loads(result.xpath('.//div[@class="vrhdata"]/@vrhm')[0])
        info = ' - '.join(result.xpath('.//div[@class="mc_vtvc_meta_block"]//span/text()')).strip()
        content = '{0} - {1}'.format(metadata['du'], info)
        thumbnail = '{0}th?id={1}'.format(base_url, metadata['thid'])
        results.append(
            {
                'url': metadata['murl'],
                'thumbnail': thumbnail,
                'title': metadata.get('vt', ''),
                'content': content,
                'template': 'videos.html',
            }
        )

    return results
