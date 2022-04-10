# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Bing (Web)

- https://github.com/searx/searx/issues/2019#issuecomment-648227442
"""

import re
from urllib.parse import urlencode, urlparse, parse_qs
from lxml import html
import babel
from searx.utils import eval_xpath, extract_text

about = {
    "website": 'https://www.bing.com',
    "wikidata_id": 'Q182496',
    "official_api_documentation": 'https://www.microsoft.com/en-us/bing/apis/bing-web-search-api',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['general', 'web']
paging = True
supported_languages_url = 'https://www.bing.com/account/general'
language_aliases = {}

time_range_support = True
time_range_dict = {'day': 'ex1:"ez1"', 'week': 'ex1:"ez2"', 'month': 'ex1:"ez3"'}

safesearch = True
safesearch_types = {2: 'STRICT', 1: 'DEMOTE', 0: 'OFF'}  # cookie: ADLT=STRICT

# search-url
base_url = 'https://www.bing.com/'

# initial query:     https://www.bing.com/search?q=foo&search=&form=QBLH
inital_query = 'search?{query}&search=&form=QBLH'

# following queries: https://www.bing.com/search?q=foo&search=&first=11&FORM=PERE
page_query = 'search?{query}&search=&first={offset}&FORM=PERE'


def _get_offset_from_pageno(pageno):
    return (pageno - 1) * 10 + 1


def request(query, params):
    """Assemble a bing request.

    Bing tries to guess user's language and territory from the HTTP
    Accept-Language.  Optional the user can select a language by adding a
    language tag to the search term.  By example if the user searches for the
    word 'foo' in articles written in english::

      language:en foo

    Bing supports only language tags, the user can't add a territory
    (e.g. 'en-US') or a script (e.g. 'zh- Hans') to the selected language.

    """
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
        search_path = inital_query.format(query=query_str)
    else:
        offset = _get_offset_from_pageno(params.get('pageno', 1))
        search_path = page_query.format(query=query_str, offset=offset)
        referer = base_url + inital_query.format(query=query_str)
        params['headers']['Referer'] = referer
        logger.debug("headers.Referer --> %s", referer)

    params['url'] = base_url + search_path

    # cookies

    # On bing users can disable SafeSearch but this does not have an effect in
    # the bing search results (except you switch to bing-videos or bing-images)

    # SRCHHPGUSR = [
    #     # 'SRCHLANG=%s' % locale.language,
    #     'ADLT=%s' % safesearch_types.get(params['safesearch'], 'OFF')
    # ]
    # params['cookies']['SRCHHPGUSR'] = '&'.join(SRCHHPGUSR) + ';'
    # logger.debug("cookies SRCHHPGUSR=%s", params['cookies']['SRCHHPGUSR'])

    # time range

    time_range = time_range_dict.get(params['time_range'])
    if time_range:
        params['url'] += "&filters=" + time_range

    # language & locale

    # language of the UI ...
    # if locale.language in supported_languages:
    #     params['url'] += '&setlang=%s' % locale.language

    ac_lang = locale.language
    if locale.territory:
        ac_lang = "%s-%s,%s;q=0.5" % (locale.language, locale.territory, locale.language)
    logger.debug("headers.Accept-Language --> %s", ac_lang)
    params['headers']['Accept-Language'] = ac_lang
    params['headers']['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'

    return params


def response(resp):

    results = []
    result_len = 0

    dom = html.fromstring(resp.text)

    for result in eval_xpath(dom, '//div[@class="sa_cc"]'):

        # IMO //div[@class="sa_cc"] does no longer match
        logger.debug('found //div[@class="sa_cc"] --> %s', result)

        link = eval_xpath(result, './/h3/a')[0]
        url = link.attrib.get('href')
        title = extract_text(link)
        content = extract_text(eval_xpath(result, './/p'))

        # append result
        results.append({'url': url, 'title': title, 'content': content})

    # parse results again if nothing is found yet
    for result in eval_xpath(dom, '//li[@class="b_algo"]'):

        link = eval_xpath(result, './/h2/a')[0]
        url = link.attrib.get('href')
        title = extract_text(link)
        content = extract_text(eval_xpath(result, './/p'))

        # append result
        results.append({'url': url, 'title': title, 'content': content})

    try:
        result_len_container = "".join(eval_xpath(dom, '//span[@class="sb_count"]//text()'))
        if "-" in result_len_container:

            # Remove the part "from-to" for paginated request ...
            result_len_container = result_len_container[result_len_container.find("-") * 2 + 2 :]

        result_len_container = re.sub('[^0-9]', '', result_len_container)

        if len(result_len_container) > 0:
            result_len = int(result_len_container)

    except Exception as e:  # pylint: disable=broad-except
        logger.debug('result error :\n%s', e)

    if result_len and _get_offset_from_pageno(resp.search_params.get("pageno", 0)) > result_len:
        return []

    results.append({'number_of_results': result_len})
    return results


# get supported languages from their site
def _fetch_supported_languages(resp):

    lang_tags = set()

    dom = html.fromstring(resp.text)

    # Selector to get items from "Display language"
    ui_lang_links = eval_xpath(dom, '//div[@id="language-section"]//li')

    for _li in ui_lang_links:

        href = eval_xpath(_li, './/@href')[0]
        (_scheme, _netloc, _path, _params, query, _fragment) = urlparse(href)
        query = parse_qs(query, keep_blank_values=True)

        # The 'language:xx' query string in the request function (above) does
        # only support the 2 letter language codes from the "Display languages"
        # list.  Examples of items from the "Display languages" not sopported in
        # the query string:
        #    'mn-Cyrl-MN', 'chr-cher', 'zh-Hans', ha-latn, 'ca-es-valencia'

        setlang = query.get('setlang', [None, ])[0]
        lang = setlang.split('-')[0]
        lang_tags.add(lang)

    return list(lang_tags)
