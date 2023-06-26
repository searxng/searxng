# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This is the implementation of the Google WEB engine.  Some of this
implementations (manly the :py:obj:`get_google_info`) are shared by other
engines:

- :ref:`google images engine`
- :ref:`google news engine`
- :ref:`google videos engine`
- :ref:`google scholar engine`
- :ref:`google autocomplete`

"""

from typing import TYPE_CHECKING

import re
from urllib.parse import urlencode
from lxml import html
import babel
import babel.core
import babel.languages

from searx.utils import extract_text, eval_xpath, eval_xpath_list, eval_xpath_getindex
from searx.locales import language_tag, region_tag, get_offical_locales
from searx.network import get  # see https://github.com/searxng/searxng/issues/762
from searx.exceptions import SearxEngineCaptchaException
from searx.enginelib.traits import EngineTraits

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

traits: EngineTraits


# about
about = {
    "website": 'https://www.google.com',
    "wikidata_id": 'Q9366',
    "official_api_documentation": 'https://developers.google.com/custom-search/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['general', 'web']
paging = True
time_range_support = True
safesearch = True

time_range_dict = {'day': 'd', 'week': 'w', 'month': 'm', 'year': 'y'}

# Filter results. 0: None, 1: Moderate, 2: Strict
filter_mapping = {0: 'off', 1: 'medium', 2: 'high'}

# specific xpath variables
# ------------------------

results_xpath = './/div[contains(@jscontroller, "SC7lYd")]'
title_xpath = './/a/h3[1]'
href_xpath = './/a[h3]/@href'
content_xpath = './/div[@data-sncf]'

# Suggestions are links placed in a *card-section*, we extract only the text
# from the links not the links itself.
suggestion_xpath = '//div[contains(@class, "EIaa9b")]//a'

# UI_ASYNC = 'use_ac:true,_fmt:html' # returns a HTTP 500 when user search for
#                                    # celebrities like '!google natasha allegri'
#                                    # or '!google chris evans'
UI_ASYNC = 'use_ac:true,_fmt:prog'
"""Format of the response from UI's async request."""


def get_google_info(params, eng_traits):
    """Composing various (language) properties for the google engines (:ref:`google
    API`).

    This function is called by the various google engines (:ref:`google web
    engine`, :ref:`google images engine`, :ref:`google news engine` and
    :ref:`google videos engine`).

    :param dict param: Request parameters of the engine.  At least
        a ``searxng_locale`` key should be in the dictionary.

    :param eng_traits: Engine's traits fetched from google preferences
        (:py:obj:`searx.enginelib.traits.EngineTraits`)

    :rtype: dict
    :returns:
        Py-Dictionary with the key/value pairs:

        language:
            The language code that is used by google (e.g. ``lang_en`` or
            ``lang_zh-TW``)

        country:
            The country code that is used by google (e.g. ``US`` or ``TW``)

        locale:
            A instance of :py:obj:`babel.core.Locale` build from the
            ``searxng_locale`` value.

        subdomain:
            Google subdomain :py:obj:`google_domains` that fits to the country
            code.

        params:
            Py-Dictionary with additional request arguments (can be passed to
            :py:func:`urllib.parse.urlencode`).

            - ``hl`` parameter: specifies the interface language of user interface.
            - ``lr`` parameter: restricts search results to documents written in
              a particular language.
            - ``cr`` parameter: restricts search results to documents
              originating in a particular country.
            - ``ie`` parameter: sets the character encoding scheme that should
              be used to interpret the query string ('utf8').
            - ``oe`` parameter: sets the character encoding scheme that should
              be used to decode the XML result ('utf8').

        headers:
            Py-Dictionary with additional HTTP headers (can be passed to
            request's headers)

            - ``Accept: '*/*``

    """

    ret_val = {
        'language': None,
        'country': None,
        'subdomain': None,
        'params': {},
        'headers': {},
        'cookies': {},
        'locale': None,
    }

    sxng_locale = params.get('searxng_locale', 'all')
    try:
        locale = babel.Locale.parse(sxng_locale, sep='-')
    except babel.core.UnknownLocaleError:
        locale = None

    eng_lang = eng_traits.get_language(sxng_locale, 'lang_en')
    lang_code = eng_lang.split('_')[-1]  # lang_zh-TW --> zh-TW / lang_en --> en
    country = eng_traits.get_region(sxng_locale, eng_traits.all_locale)

    # Test zh_hans & zh_hant --> in the topmost links in the result list of list
    # TW and HK you should a find wiktionary.org zh_hant link.  In the result
    # list of zh-CN should not be no hant link instead you should find
    # zh.m.wikipedia.org/zh somewhere in the top.

    # '!go 日 :zh-TW' --> https://zh.m.wiktionary.org/zh-hant/%E6%97%A5
    # '!go 日 :zh-CN' --> https://zh.m.wikipedia.org/zh/%E6%97%A5

    ret_val['language'] = eng_lang
    ret_val['country'] = country
    ret_val['locale'] = locale
    ret_val['subdomain'] = eng_traits.custom['supported_domains'].get(country.upper(), 'www.google.com')

    # hl parameter:
    #   The hl parameter specifies the interface language (host language) of
    #   your user interface. To improve the performance and the quality of your
    #   search results, you are strongly encouraged to set this parameter
    #   explicitly.
    #   https://developers.google.com/custom-search/docs/xml_results#hlsp
    # The Interface Language:
    #   https://developers.google.com/custom-search/docs/xml_results_appendices#interfaceLanguages

    # https://github.com/searxng/searxng/issues/2515#issuecomment-1607150817
    ret_val['params']['hl'] = f'{lang_code}-{country}'

    # lr parameter:
    #   The lr (language restrict) parameter restricts search results to
    #   documents written in a particular language.
    #   https://developers.google.com/custom-search/docs/xml_results#lrsp
    #   Language Collection Values:
    #   https://developers.google.com/custom-search/docs/xml_results_appendices#languageCollections
    #
    # To select 'all' languages an empty 'lr' value is used.
    #
    # Different to other google services, Google Schloar supports to select more
    # than one language. The languages are seperated by a pipe '|' (logical OR).
    # By example: &lr=lang_zh-TW%7Clang_de selects articles written in
    # traditional chinese OR german language.

    ret_val['params']['lr'] = eng_lang
    if sxng_locale == 'all':
        ret_val['params']['lr'] = ''

    # cr parameter:
    #   The cr parameter restricts search results to documents originating in a
    #   particular country.
    #   https://developers.google.com/custom-search/docs/xml_results#crsp

    ret_val['params']['cr'] = 'country' + country
    if sxng_locale == 'all':
        ret_val['params']['cr'] = ''

    # gl parameter: (mandatory by Geeogle News)
    #   The gl parameter value is a two-letter country code. For WebSearch
    #   results, the gl parameter boosts search results whose country of origin
    #   matches the parameter value. See the Country Codes section for a list of
    #   valid values.
    #   Specifying a gl parameter value in WebSearch requests should improve the
    #   relevance of results. This is particularly true for international
    #   customers and, even more specifically, for customers in English-speaking
    #   countries other than the United States.
    #   https://developers.google.com/custom-search/docs/xml_results#glsp

    # https://github.com/searxng/searxng/issues/2515#issuecomment-1606294635
    # ret_val['params']['gl'] = country

    # ie parameter:
    #   The ie parameter sets the character encoding scheme that should be used
    #   to interpret the query string. The default ie value is latin1.
    #   https://developers.google.com/custom-search/docs/xml_results#iesp

    ret_val['params']['ie'] = 'utf8'

    # oe parameter:
    #   The oe parameter sets the character encoding scheme that should be used
    #   to decode the XML result. The default oe value is latin1.
    #   https://developers.google.com/custom-search/docs/xml_results#oesp

    ret_val['params']['oe'] = 'utf8'

    # num parameter:
    #   The num parameter identifies the number of search results to return.
    #   The default num value is 10, and the maximum value is 20. If you request
    #   more than 20 results, only 20 results will be returned.
    #   https://developers.google.com/custom-search/docs/xml_results#numsp

    # HINT: seems to have no effect (tested in google WEB & Images)
    # ret_val['params']['num'] = 20

    # HTTP headers

    ret_val['headers']['Accept'] = '*/*'

    # Cookies

    # - https://github.com/searxng/searxng/pull/1679#issuecomment-1235432746
    # - https://github.com/searxng/searxng/issues/1555
    ret_val['cookies']['CONSENT'] = "YES+"

    return ret_val


def detect_google_sorry(resp):
    if resp.url.host == 'sorry.google.com' or resp.url.path.startswith('/sorry'):
        raise SearxEngineCaptchaException()


def request(query, params):
    """Google search request"""
    # pylint: disable=line-too-long
    offset = (params['pageno'] - 1) * 10
    google_info = get_google_info(params, traits)

    # https://www.google.de/search?q=corona&hl=de&lr=lang_de&start=0&tbs=qdr%3Ad&safe=medium
    query_url = (
        'https://'
        + google_info['subdomain']
        + '/search'
        + "?"
        + urlencode(
            {
                'q': query,
                **google_info['params'],
                'filter': '0',
                'start': offset,
                # 'vet': '12ahUKEwik3ZbIzfn7AhXMX_EDHbUDBh0QxK8CegQIARAC..i',
                # 'ved': '2ahUKEwik3ZbIzfn7AhXMX_EDHbUDBh0Q_skCegQIARAG',
                # 'cs' : 1,
                # 'sa': 'N',
                # 'yv': 3,
                # 'prmd': 'vin',
                # 'ei': 'GASaY6TxOcy_xc8PtYeY6AE',
                # 'sa': 'N',
                # 'sstk': 'AcOHfVkD7sWCSAheZi-0tx_09XDO55gTWY0JNq3_V26cNN-c8lfD45aZYPI8s_Bqp8s57AHz5pxchDtAGCA_cikAWSjy9kw3kgg'
                # formally known as use_mobile_ui
                'asearch': 'arc',
                'async': UI_ASYNC,
            }
        )
    )

    if params['time_range'] in time_range_dict:
        query_url += '&' + urlencode({'tbs': 'qdr:' + time_range_dict[params['time_range']]})
    if params['safesearch']:
        query_url += '&' + urlencode({'safe': filter_mapping[params['safesearch']]})
    params['url'] = query_url

    params['cookies'] = google_info['cookies']
    params['headers'].update(google_info['headers'])
    return params


# =26;[3,"dimg_ZNMiZPCqE4apxc8P3a2tuAQ_137"]a87;data:image/jpeg;base64,/9j/4AAQSkZJRgABA
# ...6T+9Nl4cnD+gr9OK8I56/tX3l86nWYw//2Q==26;
RE_DATA_IMAGE = re.compile(r'"(dimg_[^"]*)"[^;]*;(data:image[^;]*;[^;]*);')


def _parse_data_images(dom):
    data_image_map = {}
    for img_id, data_image in RE_DATA_IMAGE.findall(dom.text_content()):
        end_pos = data_image.rfind('=')
        if end_pos > 0:
            data_image = data_image[: end_pos + 1]
        data_image_map[img_id] = data_image
    logger.debug('data:image objects --> %s', list(data_image_map.keys()))
    return data_image_map


def response(resp):
    """Get response from google's search request"""
    # pylint: disable=too-many-branches, too-many-statements
    detect_google_sorry(resp)

    results = []

    # convert the text to dom
    dom = html.fromstring(resp.text)
    data_image_map = _parse_data_images(dom)

    # results --> answer
    answer_list = eval_xpath(dom, '//div[contains(@class, "LGOjhe")]')
    if answer_list:
        answer_list = [_.xpath("normalize-space()") for _ in answer_list]
        results.append({'answer': ' '.join(answer_list)})
    else:
        logger.debug("did not find 'answer'")

    # parse results

    for result in eval_xpath_list(dom, results_xpath):  # pylint: disable=too-many-nested-blocks

        try:
            title_tag = eval_xpath_getindex(result, title_xpath, 0, default=None)
            if title_tag is None:
                # this not one of the common google results *section*
                logger.debug('ignoring item from the result_xpath list: missing title')
                continue
            title = extract_text(title_tag)

            url = eval_xpath_getindex(result, href_xpath, 0, None)
            if url is None:
                logger.debug('ignoring item from the result_xpath list: missing url of title "%s"', title)
                continue

            content_nodes = eval_xpath(result, content_xpath)
            content = extract_text(content_nodes)

            if not content:
                logger.debug('ignoring item from the result_xpath list: missing content of title "%s"', title)
                continue

            img_src = content_nodes[0].xpath('.//img/@src')
            if img_src:
                img_src = img_src[0]
                if img_src.startswith('data:image'):
                    img_id = content_nodes[0].xpath('.//img/@id')
                    if img_id:
                        img_src = data_image_map.get(img_id[0])
            else:
                img_src = None

            results.append({'url': url, 'title': title, 'content': content, 'img_src': img_src})

        except Exception as e:  # pylint: disable=broad-except
            logger.error(e, exc_info=True)
            continue

    # parse suggestion
    for suggestion in eval_xpath_list(dom, suggestion_xpath):
        # append suggestion
        results.append({'suggestion': extract_text(suggestion)})

    # return results
    return results


# get supported languages from their site


skip_countries = [
    # official language of google-country not in google-languages
    'AL',  # Albanien (sq)
    'AZ',  # Aserbaidschan  (az)
    'BD',  # Bangladesch (bn)
    'BN',  # Brunei Darussalam (ms)
    'BT',  # Bhutan (dz)
    'ET',  # Äthiopien (am)
    'GE',  # Georgien (ka, os)
    'GL',  # Grönland (kl)
    'KH',  # Kambodscha (km)
    'LA',  # Laos (lo)
    'LK',  # Sri Lanka (si, ta)
    'ME',  # Montenegro (sr)
    'MK',  # Nordmazedonien (mk, sq)
    'MM',  # Myanmar (my)
    'MN',  # Mongolei (mn)
    'MV',  # Malediven (dv) // dv_MV is unknown by babel
    'MY',  # Malaysia (ms)
    'NP',  # Nepal (ne)
    'TJ',  # Tadschikistan (tg)
    'TM',  # Turkmenistan (tk)
    'UZ',  # Usbekistan (uz)
]


def fetch_traits(engine_traits: EngineTraits, add_domains: bool = True):
    """Fetch languages from Google."""
    # pylint: disable=import-outside-toplevel, too-many-branches

    engine_traits.custom['supported_domains'] = {}

    resp = get('https://www.google.com/preferences')
    if not resp.ok:  # type: ignore
        raise RuntimeError("Response from Google's preferences is not OK.")

    dom = html.fromstring(resp.text)  # type: ignore

    # supported language codes

    lang_map = {'no': 'nb'}
    for x in eval_xpath_list(dom, '//*[@id="langSec"]//input[@name="lr"]'):

        eng_lang = x.get("value").split('_')[-1]
        try:
            locale = babel.Locale.parse(lang_map.get(eng_lang, eng_lang), sep='-')
        except babel.UnknownLocaleError:
            print("ERROR: %s -> %s is unknown by babel" % (x.get("data-name"), eng_lang))
            continue
        sxng_lang = language_tag(locale)

        conflict = engine_traits.languages.get(sxng_lang)
        if conflict:
            if conflict != eng_lang:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_lang, conflict, eng_lang))
            continue
        engine_traits.languages[sxng_lang] = 'lang_' + eng_lang

    # alias languages
    engine_traits.languages['zh'] = 'lang_zh-CN'

    # supported region codes

    for x in eval_xpath_list(dom, '//*[@name="region"]/..//input[@name="region"]'):
        eng_country = x.get("value")

        if eng_country in skip_countries:
            continue
        if eng_country == 'ZZ':
            engine_traits.all_locale = 'ZZ'
            continue

        sxng_locales = get_offical_locales(eng_country, engine_traits.languages.keys(), regional=True)

        if not sxng_locales:
            print("ERROR: can't map from google country %s (%s) to a babel region." % (x.get('data-name'), eng_country))
            continue

        for sxng_locale in sxng_locales:
            engine_traits.regions[region_tag(sxng_locale)] = eng_country

    # alias regions
    engine_traits.regions['zh-CN'] = 'HK'

    # supported domains

    if add_domains:
        resp = get('https://www.google.com/supported_domains')
        if not resp.ok:  # type: ignore
            raise RuntimeError("Response from https://www.google.com/supported_domains is not OK.")

        for domain in resp.text.split():  # type: ignore
            domain = domain.strip()
            if not domain or domain in [
                '.google.com',
            ]:
                continue
            region = domain.split('.')[-1].upper()
            engine_traits.custom['supported_domains'][region] = 'www' + domain  # type: ignore
            if region == 'HK':
                # There is no google.cn, we use .com.hk for zh-CN
                engine_traits.custom['supported_domains']['CN'] = 'www' + domain  # type: ignore
