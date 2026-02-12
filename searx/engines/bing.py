# SPDX-License-Identifier: AGPL-3.0-or-later
"""This is the implementation of the Bing-WEB engine. Some of this
implementations are shared by other engines:

- :ref:`bing images engine`
- :ref:`bing news engine`
- :ref:`bing videos engine`

On the `preference page`_ Bing offers a lot of languages an regions (see section
LANGUAGE and COUNTRY/REGION).  The Language is the language of the UI, we need
in SearXNG to get the translations of data such as *"published last week"*.

There is a description of the official search-APIs_, unfortunately this is not
the API we can use or that bing itself would use.  You can look up some things
in the API to get a better picture of bing, but the value specifications like
the market codes are usually outdated or at least no longer used by bing itself.

The market codes have been harmonized and are identical for web, video and
images.  The news area has also been harmonized with the other categories.  Only
political adjustments still seem to be made -- for example, there is no news
category for the Chinese market.

.. _preference page: https://www.bing.com/account/general
.. _search-APIs: https://learn.microsoft.com/en-us/bing/search-apis/

"""
# pylint: disable=too-many-branches, invalid-name

import base64
import re
import time
from urllib.parse import parse_qs, urlencode, urlparse
from lxml import html
import babel
import babel.languages

from searx.utils import eval_xpath, extract_text, eval_xpath_list, eval_xpath_getindex
from searx.locales import language_tag, region_tag
from searx.enginelib.traits import EngineTraits
from searx.exceptions import SearxEngineAPIException

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
max_page = 200
"""200 pages maximum (``&first=1991``)"""

time_range_support = True
safesearch = True
"""Bing results are always SFW.  To get NSFW links from bing some age
verification by a cookie is needed / thats not possible in SearXNG.
"""

base_url = 'https://www.bing.com/search'
"""Bing (Web) search URL"""


def _page_offset(pageno):
    return (int(pageno) - 1) * 10 + 1


def set_bing_cookies(params, engine_language, engine_region):
    params['cookies']['_EDGE_CD'] = f'm={engine_region}&u={engine_language}'
    params['cookies']['_EDGE_S'] = f'mkt={engine_region}&ui={engine_language}'
    logger.debug("bing cookies: %s", params['cookies'])


def request(query, params):
    """Assemble a Bing-Web request."""

    engine_region = traits.get_region(params['searxng_locale'], traits.all_locale)  # type: ignore
    engine_language = traits.get_language(params['searxng_locale'], 'en')  # type: ignore
    set_bing_cookies(params, engine_language, engine_region)

    page = params.get('pageno', 1)
    query_params = {
        'q': query,
        # if arg 'pq' is missed, sometimes on page 4 we get results from page 1,
        # don't ask why it is only sometimes / its M$ and they have never been
        # deterministic ;)
        'pq': query,
        # TODO: Figure out how below parameters are populated
        'sc': '0-0',
		"sp": "-1",
		"lq": "0",
		"qs": "n",
		"ghsh": "0",
		"ghacc": "0",
		"ghpl": "",
    }

    # To get correct page, arg first and this arg FORM is needed, the value PERE
    # is on page 2, on page 3 its PERE1 and on page 4 its PERE2 .. and so forth.
    # The 'first' arg should never send on page 1.
    if page > 1:
        query_params['first'] = _page_offset(page)  # see also arg FORM
        if page == 2:
            query_params['FORM'] = 'PERE'
        else:  # page > 2:
            query_params['FORM'] = 'PERE%s' % (page - 2)

    params['url'] = f'{base_url}?{urlencode(query_params)}'

    if params.get('time_range'):
        unix_day = int(time.time() / 86400)
        time_ranges = {'day': '1', 'week': '2', 'month': '3', 'year': f'5_{unix_day-365}_{unix_day}'}
        params['url'] += f'&filters=ex1:"ez{time_ranges[params["time_range"]]}"'

    # in some regions where geoblocking is employed (e.g. China),
    # www.bing.com redirects to the regional version of Bing
    params['allow_redirects'] = True

    return params


def response(resp):
    # pylint: disable=too-many-locals

    results = []
    result_len = 0

    dom = html.fromstring(resp.text)

    # parse results again if nothing is found yet

    for result in eval_xpath_list(dom, '//ol[@id="b_results"]/li[contains(@class, "b_algo")]'):

        link = eval_xpath_getindex(result, './/h2/a', 0, None)
        if link is None:
            continue
        url = link.attrib.get('href')
        title = extract_text(link)

        content = eval_xpath(result, './/p')
        for p in content:
            # Make sure that the element is free of:
            #  <span class="algoSlug_icon" # data-priority="2">Web</span>
            for e in p.xpath('.//span[@class="algoSlug_icon"]'):
                e.getparent().remove(e)
        content = extract_text(content)

        # get the real URL
        if url.startswith('https://www.bing.com/ck/a?'):
            # get the first value of u parameter
            url_query = urlparse(url).query
            parsed_url_query = parse_qs(url_query)
            param_u = parsed_url_query["u"][0]
            # remove "a1" in front
            encoded_url = param_u[2:]
            # add padding
            encoded_url = encoded_url + '=' * (-len(encoded_url) % 4)
            # decode base64 encoded URL
            url = base64.urlsafe_b64decode(encoded_url).decode()

        # append result
        results.append({'url': url, 'title': title, 'content': content})

    # get number_of_results
    if results:
        result_len_container = "".join(eval_xpath(dom, '//span[@class="sb_count"]//text()'))
        if "-" in result_len_container:
            start_str, result_len_container = re.split(r'-\d+', result_len_container)
            start = int(start_str)
        else:
            start = 1

        result_len_container = re.sub('[^0-9]', '', result_len_container)
        if len(result_len_container) > 0:
            result_len = int(result_len_container)

        expected_start = _page_offset(resp.search_params.get("pageno", 1))

        if expected_start != start:
            if expected_start > result_len:
                # Avoid reading more results than available.
                # For example, if there is 100 results from some search and we try to get results from 120 to 130,
                # Bing will send back the results from 0 to 10 and no error.
                # If we compare results count with the first parameter of the request we can avoid this "invalid"
                # results.
                return []

            # Sometimes Bing will send back the first result page instead of the requested page as a rate limiting
            # measure.
            msg = f"Expected results to start at {expected_start}, but got results starting at {start}"
            raise SearxEngineAPIException(msg)

    results.append({'number_of_results': result_len})
    return results


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages and regions from Bing-Web."""
    # pylint: disable=import-outside-toplevel

    from searx.network import get  # see https://github.com/searxng/searxng/issues/762
    from searx.utils import gen_useragent

    headers = {
        "User-Agent": gen_useragent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US;q=0.5,en;q=0.3",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-GPC": "1",
        "Cache-Control": "max-age=0",
    }

    resp = get("https://www.bing.com/account/general", headers=headers)
    if not resp.ok:  # type: ignore
        print("ERROR: response from bing is not OK.")

    dom = html.fromstring(resp.text)  # type: ignore

    # languages

    engine_traits.languages['zh'] = 'zh-hans'

    map_lang = {'prs': 'fa-AF', 'en': 'en-us'}
    bing_ui_lang_map = {
        # HINT: this list probably needs to be supplemented
        'en': 'us',  # en --> en-us
        'da': 'dk',  # da --> da-dk
    }

    for href in eval_xpath(dom, '//div[@id="language-section-content"]//div[@class="languageItem"]/a/@href'):
        eng_lang = parse_qs(urlparse(href).query)['setlang'][0]
        babel_lang = map_lang.get(eng_lang, eng_lang)
        try:
            sxng_tag = language_tag(babel.Locale.parse(babel_lang.replace('-', '_')))
        except babel.UnknownLocaleError:
            print("ERROR: language (%s) is unknown by babel" % (babel_lang))
            continue
        # Language (e.g. 'en' or 'de') from https://www.bing.com/account/general
        # is converted by bing to 'en-us' or 'de-de'.  But only if there is not
        # already a '-' delemitter in the language.  For instance 'pt-PT' -->
        # 'pt-pt' and 'pt-br' --> 'pt-br'
        bing_ui_lang = eng_lang.lower()
        if '-' not in bing_ui_lang:
            bing_ui_lang = bing_ui_lang + '-' + bing_ui_lang_map.get(bing_ui_lang, bing_ui_lang)

        conflict = engine_traits.languages.get(sxng_tag)
        if conflict:
            if conflict != bing_ui_lang:
                print(f"CONFLICT: babel {sxng_tag} --> {conflict}, {bing_ui_lang}")
            continue
        engine_traits.languages[sxng_tag] = bing_ui_lang

    # regions (aka "market codes")

    engine_traits.regions['zh-CN'] = 'zh-cn'

    map_market_codes = {
        'zh-hk': 'en-hk',  # not sure why, but at M$ this is the market code for Hongkong
    }
    for href in eval_xpath(dom, '//div[@id="region-section-content"]//div[@class="regionItem"]/a/@href'):
        cc_tag = parse_qs(urlparse(href).query)['cc'][0]
        if cc_tag == 'clear':
            engine_traits.all_locale = cc_tag
            continue

        # add market codes from official languages of the country ..
        for lang_tag in babel.languages.get_official_languages(cc_tag, de_facto=True):
            if lang_tag not in engine_traits.languages.keys():
                # print("ignore lang: %s <-- %s" % (cc_tag, lang_tag))
                continue
            lang_tag = lang_tag.split('_')[0]  # zh_Hant --> zh
            market_code = f"{lang_tag}-{cc_tag}"  # zh-tw

            market_code = map_market_codes.get(market_code, market_code)
            sxng_tag = region_tag(babel.Locale.parse('%s_%s' % (lang_tag, cc_tag.upper())))
            conflict = engine_traits.regions.get(sxng_tag)
            if conflict:
                if conflict != market_code:
                    print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, market_code))
                    continue
            engine_traits.regions[sxng_tag] = market_code
