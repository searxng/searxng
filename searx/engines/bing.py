# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Bing (Web)

- https://github.com/searx/searx/issues/2019#issuecomment-648227442
"""
# pylint: disable=too-many-branches

import re
from urllib.parse import urlencode, urlparse, parse_qs
from lxml import html
from searx.utils import eval_xpath, extract_text, eval_xpath_list, match_language, eval_xpath_getindex
from searx.network import multi_requests, Request

from searx.enginelib.traits import EngineTraits

traits: EngineTraits

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
time_range_support = False
safesearch = False
send_accept_language_header = True
supported_languages_url = 'https://www.bing.com/account/general'
language_aliases = {}

# search-url
base_url = 'https://www.bing.com/'

# initial query:     https://www.bing.com/search?q=foo&search=&form=QBLH
inital_query = 'search?{query}&search=&form=QBLH'

# following queries: https://www.bing.com/search?q=foo&search=&first=11&FORM=PERE
page_query = 'search?{query}&search=&first={offset}&FORM=PERE'


def _get_offset_from_pageno(pageno):
    return (pageno - 1) * 10 + 1


def request(query, params):

    offset = _get_offset_from_pageno(params.get('pageno', 1))

    # logger.debug("params['pageno'] --> %s", params.get('pageno'))
    # logger.debug("          offset --> %s", offset)

    search_string = page_query
    if offset == 1:
        search_string = inital_query

    if params['language'] == 'all':
        lang = 'EN'
    else:
        lang = match_language(params['language'], supported_languages, language_aliases)

    query = 'language:{} {}'.format(lang.split('-')[0].upper(), query)

    search_path = search_string.format(query=urlencode({'q': query}), offset=offset)

    if offset > 1:
        referer = base_url + inital_query.format(query=urlencode({'q': query}))
        params['headers']['Referer'] = referer
        logger.debug("headers.Referer --> %s", referer)

    params['url'] = base_url + search_path
    params['headers']['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    return params


def response(resp):
    results = []
    result_len = 0

    dom = html.fromstring(resp.text)

    # parse results again if nothing is found yet

    url_to_resolve = []
    url_to_resolve_index = []
    i = 0
    for result in eval_xpath_list(dom, '//ol[@id="b_results"]/li[contains(@class, "b_algo")]'):

        link = eval_xpath_getindex(result, './/h2/a', 0, None)
        if link is None:
            continue
        url = link.attrib.get('href')
        title = extract_text(link)

        # Make sure that the element is free of <a href> links and <span class='algoSlug_icon'>
        content = eval_xpath(result, '(.//p)[1]')
        for p in content:
            for e in p.xpath('.//a'):
                e.getparent().remove(e)
            for e in p.xpath('.//span[@class="algoSlug_icon"]'):
                e.getparent().remove(e)
        content = extract_text(content)

        # get the real URL either using the URL shown to user or following the Bing URL
        if url.startswith('https://www.bing.com/ck/a?'):
            url_cite = extract_text(eval_xpath(result, './/div[@class="b_attribution"]/cite'))
            # Bing can shorten the URL either at the end or in the middle of the string
            if (
                url_cite.startswith('https://')
                and '…' not in url_cite
                and '...' not in url_cite
                and '›' not in url_cite
            ):
                # no need for an additional HTTP request
                url = url_cite
            else:
                # resolve the URL with an additional HTTP request
                url_to_resolve.append(url.replace('&ntb=1', '&ntb=F'))
                url_to_resolve_index.append(i)
                url = None  # remove the result if the HTTP Bing redirect raise an exception

        # append result
        results.append({'url': url, 'title': title, 'content': content})
        # increment result pointer for the next iteration in this loop
        i += 1

    # resolve all Bing redirections in parallel
    request_list = [
        Request.get(u, allow_redirects=False, headers=resp.search_params['headers']) for u in url_to_resolve
    ]
    response_list = multi_requests(request_list)
    for i, redirect_response in enumerate(response_list):
        if not isinstance(redirect_response, Exception):
            results[url_to_resolve_index[i]]['url'] = redirect_response.headers['location']

    # get number_of_results
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
    lang_links = eval_xpath(dom, '//div[@id="language-section"]//li')

    for _li in lang_links:

        href = eval_xpath(_li, './/@href')[0]
        (_scheme, _netloc, _path, _params, query, _fragment) = urlparse(href)
        query = parse_qs(query, keep_blank_values=True)

        # fmt: off
        setlang = query.get('setlang', [None, ])[0]
        # example: 'mn-Cyrl-MN' --> '['mn', 'Cyrl-MN']
        lang, nation = (setlang.split('-', maxsplit=1) + [None,])[:2]  # fmt: skip
        # fmt: on

        tag = lang + '-' + nation if nation else lang
        lang_tags.add(tag)

    return list(lang_tags)


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages and regions from bing."""

    # pylint: disable=import-outside-toplevel, disable=too-many-branches,
    # pylint: disable=too-many-locals, too-many-statements

    engine_traits.data_type = 'supported_languages'  # deprecated

    import babel
    import babel.languages
    from searx import network
    from searx.locales import get_offical_locales, language_tag, region_tag
    from searx.utils import gen_useragent

    headers = {
        'User-Agent': gen_useragent(),
        'Accept-Language': "en-US,en;q=0.5",  # bing needs to set the English language
    }
    resp = network.get('https://www.bing.com/account/general', headers=headers)

    if not resp.ok:
        print("ERROR: response from peertube is not OK.")

    dom = html.fromstring(resp.text)

    # Selector to get items from "Display language"

    lang_map = {
        'prs': 'fa',  # Persian
        'pt_BR': 'pt',  # Portuguese (Brasil)
        'pt_PT': 'pt',  # Portuguese (Portugal)
        'ca-ES-VALENCIA': 'ca',  # Catalan (Spain, Valencian)
    }

    unknow_langs = [
        'quc',  # K'iche'
        'nso',  # Sesotho sa Leboa
        'tn',  # Setswana
    ]

    for div in eval_xpath(dom, '//div[@id="limit-languages"]//input/..'):

        eng_lang = eval_xpath(div, './/input/@value')[0]
        if eng_lang in unknow_langs:
            continue

        eng_lang = lang_map.get(eng_lang, eng_lang)
        label = extract_text(eval_xpath(div, './/label'))

        # The 'language:xx' query string in the request function (above) does
        # only support the language codes from the "Display languages" list.
        # Examples of items from the "Display languages" not sopported in the
        # query string: zh_Hans --> zh / sr_latn --> sr
        #
        # eng_lang = eng_lang.split('_')[0]

        try:
            sxng_tag = language_tag(babel.Locale.parse(eng_lang.replace('-', '_'), sep='_'))
        except babel.UnknownLocaleError:
            print("ERROR: %s (%s) is unknown by babel" % (label, eng_lang))
            continue

        conflict = engine_traits.languages.get(sxng_tag)
        if conflict:
            if conflict != eng_lang:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, eng_lang))
            continue
        engine_traits.languages[sxng_tag] = eng_lang

    engine_traits.languages['zh'] = 'zh_Hans'

    # regiones

    for a in eval_xpath(dom, '//div[@id="region-section-content"]//li/a'):
        href = eval_xpath(a, './/@href')[0]
        # lang_name = extract_text(a)
        query = urlparse(href)[4]
        query = parse_qs(query, keep_blank_values=True)
        cc = query.get('cc')[0]  # pylint:disable=invalid-name
        if cc == 'clear':
            continue

        # Assert babel supports this locales
        sxng_locales = get_offical_locales(cc.upper(), engine_traits.languages.keys())

        if not sxng_locales:
            # print("ERROR: can't map from bing country %s (%s) to a babel region." % (a.text_content().strip(), cc))
            continue

        for sxng_locale in sxng_locales:
            engine_traits.regions[region_tag(sxng_locale)] = cc
