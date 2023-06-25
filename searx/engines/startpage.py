# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Startpage's language & region selectors are a mess ..

.. _startpage regions:

Startpage regions
=================

In the list of regions there are tags we need to map to common region tags::

  pt-BR_BR --> pt_BR
  zh-CN_CN --> zh_Hans_CN
  zh-TW_TW --> zh_Hant_TW
  zh-TW_HK --> zh_Hant_HK
  en-GB_GB --> en_GB

and there is at least one tag with a three letter language tag (ISO 639-2)::

  fil_PH --> fil_PH

The locale code ``no_NO`` from Startpage does not exists and is mapped to
``nb-NO``::

    babel.core.UnknownLocaleError: unknown locale 'no_NO'

For reference see languages-subtag at iana; ``no`` is the macrolanguage [1]_ and
W3C recommends subtag over macrolanguage [2]_.

.. [1] `iana: language-subtag-registry
   <https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry>`_ ::

      type: language
      Subtag: nb
      Description: Norwegian Bokmål
      Added: 2005-10-16
      Suppress-Script: Latn
      Macrolanguage: no

.. [2]
   Use macrolanguages with care.  Some language subtags have a Scope field set to
   macrolanguage, i.e. this primary language subtag encompasses a number of more
   specific primary language subtags in the registry.  ...  As we recommended for
   the collection subtags mentioned above, in most cases you should try to use
   the more specific subtags ... `W3: The primary language subtag
   <https://www.w3.org/International/questions/qa-choosing-language-tags#langsubtag>`_

.. _startpage languages:

Startpage languages
===================

:py:obj:`send_accept_language_header`:
  The displayed name in Startpage's settings page depend on the location of the
  IP when ``Accept-Language`` HTTP header is unset.  In :py:obj:`fetch_traits`
  we use::

    'Accept-Language': "en-US,en;q=0.5",
    ..

  to get uniform names independent from the IP).

.. _startpage categories:

Startpage categories
====================

Startpage's category (for Web-search, News, Videos, ..) is set by
:py:obj:`startpage_categ` in  settings.yml::

  - name: startpage
    engine: startpage
    startpage_categ: web
    ...

.. hint::

   The default category is ``web`` .. and other categories than ``web`` are not
   yet implemented.

"""

from typing import TYPE_CHECKING
from collections import OrderedDict
import re
from unicodedata import normalize, combining
from time import time
from datetime import datetime, timedelta

import dateutil.parser
import lxml.html
import babel

from searx.utils import extract_text, eval_xpath, gen_useragent
from searx.network import get  # see https://github.com/searxng/searxng/issues/762
from searx.exceptions import SearxEngineCaptchaException
from searx.locales import region_tag
from searx.enginelib.traits import EngineTraits

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

traits: EngineTraits

# about
about = {
    "website": 'https://startpage.com',
    "wikidata_id": 'Q2333295',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

startpage_categ = 'web'
"""Startpage's category, visit :ref:`startpage categories`.
"""

send_accept_language_header = True
"""Startpage tries to guess user's language and territory from the HTTP
``Accept-Language``.  Optional the user can select a search-language (can be
different to the UI language) and a region filter.
"""

# engine dependent config
categories = ['general', 'web']
paging = True
time_range_support = True
safesearch = True

time_range_dict = {'day': 'd', 'week': 'w', 'month': 'm', 'year': 'y'}
safesearch_dict = {0: '0', 1: '1', 2: '1'}

# search-url
base_url = 'https://www.startpage.com'
search_url = base_url + '/sp/search'

# specific xpath variables
# ads xpath //div[@id="results"]/div[@id="sponsored"]//div[@class="result"]
# not ads: div[@class="result"] are the direct childs of div[@id="results"]
results_xpath = '//div[@class="w-gl__result__main"]'
link_xpath = './/a[@class="w-gl__result-title result-link"]'
content_xpath = './/p[@class="w-gl__description"]'
search_form_xpath = '//form[@id="search"]'
"""XPath of Startpage's origin search form

.. code: html

    <form action="/sp/search" method="post">
      <input type="text" name="query"  value="" ..>
      <input type="hidden" name="t" value="device">
      <input type="hidden" name="lui" value="english">
      <input type="hidden" name="sc" value="Q7Mt5TRqowKB00">
      <input type="hidden" name="cat" value="web">
      <input type="hidden" class="abp" id="abp-input" name="abp" value="1">
    </form>
"""

# timestamp of the last fetch of 'sc' code
sc_code_ts = 0
sc_code = ''
sc_code_cache_sec = 30
"""Time in seconds the sc-code is cached in memory :py:obj:`get_sc_code`."""


def get_sc_code(searxng_locale, params):
    """Get an actual ``sc`` argument from Startpage's search form (HTML page).

    Startpage puts a ``sc`` argument on every HTML :py:obj:`search form
    <search_form_xpath>`.  Without this argument Startpage considers the request
    is from a bot.  We do not know what is encoded in the value of the ``sc``
    argument, but it seems to be a kind of a *time-stamp*.

    Startpage's search form generates a new sc-code on each request.  This
    function scrap a new sc-code from Startpage's home page every
    :py:obj:`sc_code_cache_sec` seconds.

    """

    global sc_code_ts, sc_code  # pylint: disable=global-statement

    if sc_code and (time() < (sc_code_ts + sc_code_cache_sec)):
        logger.debug("get_sc_code: reuse '%s'", sc_code)
        return sc_code

    headers = {**params['headers']}
    headers['Origin'] = base_url
    headers['Referer'] = base_url + '/'
    # headers['Connection'] = 'keep-alive'
    # headers['Accept-Encoding'] = 'gzip, deflate, br'
    # headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
    # headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0'

    # add Accept-Language header
    if searxng_locale == 'all':
        searxng_locale = 'en-US'
    locale = babel.Locale.parse(searxng_locale, sep='-')

    if send_accept_language_header:
        ac_lang = locale.language
        if locale.territory:
            ac_lang = "%s-%s,%s;q=0.9,*;q=0.5" % (
                locale.language,
                locale.territory,
                locale.language,
            )
        headers['Accept-Language'] = ac_lang

    get_sc_url = base_url + '/?sc=%s' % (sc_code)
    logger.debug("query new sc time-stamp ... %s", get_sc_url)
    logger.debug("headers: %s", headers)
    resp = get(get_sc_url, headers=headers)

    # ?? x = network.get('https://www.startpage.com/sp/cdn/images/filter-chevron.svg', headers=headers)
    # ?? https://www.startpage.com/sp/cdn/images/filter-chevron.svg
    # ?? ping-back URL: https://www.startpage.com/sp/pb?sc=TLsB0oITjZ8F21

    if str(resp.url).startswith('https://www.startpage.com/sp/captcha'):  # type: ignore
        raise SearxEngineCaptchaException(
            message="get_sc_code: got redirected to https://www.startpage.com/sp/captcha",
        )

    dom = lxml.html.fromstring(resp.text)  # type: ignore

    try:
        sc_code = eval_xpath(dom, search_form_xpath + '//input[@name="sc"]/@value')[0]
    except IndexError as exc:
        logger.debug("suspend startpage API --> https://github.com/searxng/searxng/pull/695")
        raise SearxEngineCaptchaException(
            message="get_sc_code: [PR-695] query new sc time-stamp failed! (%s)" % resp.url,  # type: ignore
        ) from exc

    sc_code_ts = time()
    logger.debug("get_sc_code: new value is: %s", sc_code)
    return sc_code


def request(query, params):
    """Assemble a Startpage request.

    To avoid CAPTCHA we need to send a well formed HTTP POST request with a
    cookie.  We need to form a request that is identical to the request build by
    Startpage's search form:

    - in the cookie the **region** is selected
    - in the HTTP POST data the **language** is selected

    Additionally the arguments form Startpage's search form needs to be set in
    HTML POST data / compare ``<input>`` elements: :py:obj:`search_form_xpath`.
    """
    if startpage_categ == 'web':
        return _request_cat_web(query, params)

    logger.error("Startpages's category '%' is not yet implemented.", startpage_categ)
    return params


def _request_cat_web(query, params):

    engine_region = traits.get_region(params['searxng_locale'], 'en-US')
    engine_language = traits.get_language(params['searxng_locale'], 'en')

    # build arguments
    args = {
        'query': query,
        'cat': 'web',
        't': 'device',
        'sc': get_sc_code(params['searxng_locale'], params),  # hint: this func needs HTTP headers,
        'with_date': time_range_dict.get(params['time_range'], ''),
    }

    if engine_language:
        args['language'] = engine_language
        args['lui'] = engine_language

    args['abp'] = '1'
    if params['pageno'] > 1:
        args['page'] = params['pageno']

    # build cookie
    lang_homepage = 'en'
    cookie = OrderedDict()
    cookie['date_time'] = 'world'
    cookie['disable_family_filter'] = safesearch_dict[params['safesearch']]
    cookie['disable_open_in_new_window'] = '0'
    cookie['enable_post_method'] = '1'  # hint: POST
    cookie['enable_proxy_safety_suggest'] = '1'
    cookie['enable_stay_control'] = '1'
    cookie['instant_answers'] = '1'
    cookie['lang_homepage'] = 's/device/%s/' % lang_homepage
    cookie['num_of_results'] = '10'
    cookie['suggestions'] = '1'
    cookie['wt_unit'] = 'celsius'

    if engine_language:
        cookie['language'] = engine_language
        cookie['language_ui'] = engine_language

    if engine_region:
        cookie['search_results_region'] = engine_region

    params['cookies']['preferences'] = 'N1N'.join(["%sEEE%s" % x for x in cookie.items()])
    logger.debug('cookie preferences: %s', params['cookies']['preferences'])

    # POST request
    logger.debug("data: %s", args)
    params['data'] = args
    params['method'] = 'POST'
    params['url'] = search_url
    params['headers']['Origin'] = base_url
    params['headers']['Referer'] = base_url + '/'
    # is the Accept header needed?
    # params['headers']['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'

    return params


# get response from search-request
def response(resp):
    dom = lxml.html.fromstring(resp.text)

    if startpage_categ == 'web':
        return _response_cat_web(dom)

    logger.error("Startpages's category '%' is not yet implemented.", startpage_categ)
    return []


def _response_cat_web(dom):
    results = []

    # parse results
    for result in eval_xpath(dom, results_xpath):
        links = eval_xpath(result, link_xpath)
        if not links:
            continue
        link = links[0]
        url = link.attrib.get('href')

        # block google-ad url's
        if re.match(r"^http(s|)://(www\.)?google\.[a-z]+/aclk.*$", url):
            continue

        # block startpage search url's
        if re.match(r"^http(s|)://(www\.)?startpage\.com/do/search\?.*$", url):
            continue

        title = extract_text(link)

        if eval_xpath(result, content_xpath):
            content: str = extract_text(eval_xpath(result, content_xpath))  # type: ignore
        else:
            content = ''

        published_date = None

        # check if search result starts with something like: "2 Sep 2014 ... "
        if re.match(r"^([1-9]|[1-2][0-9]|3[0-1]) [A-Z][a-z]{2} [0-9]{4} \.\.\. ", content):
            date_pos = content.find('...') + 4
            date_string = content[0 : date_pos - 5]
            # fix content string
            content = content[date_pos:]

            try:
                published_date = dateutil.parser.parse(date_string, dayfirst=True)
            except ValueError:
                pass

        # check if search result starts with something like: "5 days ago ... "
        elif re.match(r"^[0-9]+ days? ago \.\.\. ", content):
            date_pos = content.find('...') + 4
            date_string = content[0 : date_pos - 5]

            # calculate datetime
            published_date = datetime.now() - timedelta(days=int(re.match(r'\d+', date_string).group()))  # type: ignore

            # fix content string
            content = content[date_pos:]

        if published_date:
            # append result
            results.append({'url': url, 'title': title, 'content': content, 'publishedDate': published_date})
        else:
            # append result
            results.append({'url': url, 'title': title, 'content': content})

    # return results
    return results


def fetch_traits(engine_traits: EngineTraits):
    """Fetch :ref:`languages <startpage languages>` and :ref:`regions <startpage
    regions>` from Startpage."""
    # pylint: disable=too-many-branches

    headers = {
        'User-Agent': gen_useragent(),
        'Accept-Language': "en-US,en;q=0.5",  # bing needs to set the English language
    }
    resp = get('https://www.startpage.com/do/settings', headers=headers)

    if not resp.ok:  # type: ignore
        print("ERROR: response from Startpage is not OK.")

    dom = lxml.html.fromstring(resp.text)  # type: ignore

    # regions

    sp_region_names = []
    for option in dom.xpath('//form[@name="settings"]//select[@name="search_results_region"]/option'):
        sp_region_names.append(option.get('value'))

    for eng_tag in sp_region_names:
        if eng_tag == 'all':
            continue
        babel_region_tag = {'no_NO': 'nb_NO'}.get(eng_tag, eng_tag)  # norway

        if '-' in babel_region_tag:
            l, r = babel_region_tag.split('-')
            r = r.split('_')[-1]
            sxng_tag = region_tag(babel.Locale.parse(l + '_' + r, sep='_'))

        else:
            try:
                sxng_tag = region_tag(babel.Locale.parse(babel_region_tag, sep='_'))

            except babel.UnknownLocaleError:
                print("ERROR: can't determine babel locale of startpage's locale %s" % eng_tag)
                continue

        conflict = engine_traits.regions.get(sxng_tag)
        if conflict:
            if conflict != eng_tag:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, eng_tag))
            continue
        engine_traits.regions[sxng_tag] = eng_tag

    # languages

    catalog_engine2code = {name.lower(): lang_code for lang_code, name in babel.Locale('en').languages.items()}

    # get the native name of every language known by babel

    for lang_code in filter(
        lambda lang_code: lang_code.find('_') == -1, babel.localedata.locale_identifiers()  # type: ignore
    ):
        native_name = babel.Locale(lang_code).get_language_name().lower()  # type: ignore
        # add native name exactly as it is
        catalog_engine2code[native_name] = lang_code

        # add "normalized" language name (i.e. français becomes francais and español becomes espanol)
        unaccented_name = ''.join(filter(lambda c: not combining(c), normalize('NFKD', native_name)))
        if len(unaccented_name) == len(unaccented_name.encode()):
            # add only if result is ascii (otherwise "normalization" didn't work)
            catalog_engine2code[unaccented_name] = lang_code

    # values that can't be determined by babel's languages names

    catalog_engine2code.update(
        {
            # traditional chinese used in ..
            'fantizhengwen': 'zh_Hant',
            # Korean alphabet
            'hangul': 'ko',
            # Malayalam is one of 22 scheduled languages of India.
            'malayam': 'ml',
            'norsk': 'nb',
            'sinhalese': 'si',
        }
    )

    skip_eng_tags = {
        'english_uk',  # SearXNG lang 'en' already maps to 'english'
    }

    for option in dom.xpath('//form[@name="settings"]//select[@name="language"]/option'):

        eng_tag = option.get('value')
        if eng_tag in skip_eng_tags:
            continue
        name = extract_text(option).lower()  # type: ignore

        sxng_tag = catalog_engine2code.get(eng_tag)
        if sxng_tag is None:
            sxng_tag = catalog_engine2code[name]

        conflict = engine_traits.languages.get(sxng_tag)
        if conflict:
            if conflict != eng_tag:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, eng_tag))
            continue
        engine_traits.languages[sxng_tag] = eng_tag
