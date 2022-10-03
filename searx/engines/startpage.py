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

The displayed name in Startpage's settings page depend on the location of the IP
when the 'Accept-Language' HTTP header is unset (in the language update script
we use "en-US,en;q=0.5" to get uniform names independent from the IP).

Each option has a displayed name and a value, either of which may represent the
language name in the native script, the language name in English, an English
transliteration of the native name, the English name of the writing script used
by the language, or occasionally something else entirely.

"""

import re
from time import time

from urllib.parse import urlencode
from unicodedata import normalize, combining
from datetime import datetime, timedelta

from dateutil import parser
from lxml import html
from babel import Locale
from babel.localedata import locale_identifiers

from searx import network
from searx.utils import extract_text, eval_xpath, match_language
from searx.exceptions import (
    SearxEngineResponseException,
    SearxEngineCaptchaException,
)

from searx.enginelib.traits import EngineTraits

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

# engine dependent config
categories = ['general', 'web']
# there is a mechanism to block "bot" search
# (probably the parameter qid), require
# storing of qid's between mulitble search-calls

paging = True
supported_languages_url = 'https://www.startpage.com/do/settings'

# search-url
base_url = 'https://startpage.com/'
search_url = base_url + 'sp/search?'

# specific xpath variables
# ads xpath //div[@id="results"]/div[@id="sponsored"]//div[@class="result"]
# not ads: div[@class="result"] are the direct childs of div[@id="results"]
results_xpath = '//div[@class="w-gl__result__main"]'
link_xpath = './/a[@class="w-gl__result-title result-link"]'
content_xpath = './/p[@class="w-gl__description"]'

# timestamp of the last fetch of 'sc' code
sc_code_ts = 0
sc_code = ''


def raise_captcha(resp):

    if str(resp.url).startswith('https://www.startpage.com/sp/captcha'):
        raise SearxEngineCaptchaException()


def get_sc_code(headers):
    """Get an actual ``sc`` argument from Startpage's home page.

    Startpage puts a ``sc`` argument on every link.  Without this argument
    Startpage considers the request is from a bot.  We do not know what is
    encoded in the value of the ``sc`` argument, but it seems to be a kind of a
    *time-stamp*.  This *time-stamp* is valid for a few hours.

    This function scrap a new *time-stamp* from startpage's home page every hour
    (3000 sec).

    """

    global sc_code_ts, sc_code  # pylint: disable=global-statement

    if time() > (sc_code_ts + 3000):
        logger.debug("query new sc time-stamp ...")

        resp = network.get(base_url, headers=headers)
        raise_captcha(resp)
        dom = html.fromstring(resp.text)

        try:
            # <input type="hidden" name="sc" value="...">
            sc_code = eval_xpath(dom, '//input[@name="sc"]/@value')[0]
        except IndexError as exc:
            # suspend startpage API --> https://github.com/searxng/searxng/pull/695
            raise SearxEngineResponseException(
                suspended_time=7 * 24 * 3600, message="PR-695: query new sc time-stamp failed!"
            ) from exc

        sc_code_ts = time()
        logger.debug("new value is: %s", sc_code)

    return sc_code


# do search-request
def request(query, params):

    # pylint: disable=line-too-long
    # The format string from Startpage's FFox add-on [1]::
    #
    #     https://www.startpage.com/do/dsearch?query={searchTerms}&cat=web&pl=ext-ff&language=__MSG_extensionUrlLanguage__&extVersion=1.3.0
    #
    # [1] https://addons.mozilla.org/en-US/firefox/addon/startpage-private-search/

    args = {
        'query': query,
        'page': params['pageno'],
        'cat': 'web',
        # 'pl': 'ext-ff',
        # 'extVersion': '1.3.0',
        # 'abp': "-1",
        'sc': get_sc_code(params['headers']),
    }

    # set language if specified
    if params['language'] != 'all':
        lang_code = match_language(params['language'], supported_languages, fallback=None)
        if lang_code:
            language_name = supported_languages[lang_code]['alias']
            args['language'] = language_name
            args['lui'] = language_name

    params['url'] = search_url + urlencode(args)
    return params


# get response from search-request
def response(resp):
    results = []

    dom = html.fromstring(resp.text)

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
            content = extract_text(eval_xpath(result, content_xpath))
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
                published_date = parser.parse(date_string, dayfirst=True)
            except ValueError:
                pass

        # check if search result starts with something like: "5 days ago ... "
        elif re.match(r"^[0-9]+ days? ago \.\.\. ", content):
            date_pos = content.find('...') + 4
            date_string = content[0 : date_pos - 5]

            # calculate datetime
            published_date = datetime.now() - timedelta(days=int(re.match(r'\d+', date_string).group()))

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


# get supported languages from their site
def _fetch_supported_languages(resp):
    # startpage's language selector is a mess each option has a displayed name
    # and a value, either of which may represent the language name in the native
    # script, the language name in English, an English transliteration of the
    # native name, the English name of the writing script used by the language,
    # or occasionally something else entirely.

    # this cases are so special they need to be hardcoded, a couple of them are misspellings
    language_names = {
        'english_uk': 'en-GB',
        'fantizhengwen': ['zh-TW', 'zh-HK'],
        'hangul': 'ko',
        'malayam': 'ml',
        'norsk': 'nb',
        'sinhalese': 'si',
        'sudanese': 'su',
    }

    # get the English name of every language known by babel
    language_names.update(
        {
            # fmt: off
            name.lower(): lang_code
            # pylint: disable=protected-access
            for lang_code, name in Locale('en')._data['languages'].items()
            # fmt: on
        }
    )

    # get the native name of every language known by babel
    for lang_code in filter(lambda lang_code: lang_code.find('_') == -1, locale_identifiers()):
        native_name = Locale(lang_code).get_language_name().lower()
        # add native name exactly as it is
        language_names[native_name] = lang_code

        # add "normalized" language name (i.e. français becomes francais and español becomes espanol)
        unaccented_name = ''.join(filter(lambda c: not combining(c), normalize('NFKD', native_name)))
        if len(unaccented_name) == len(unaccented_name.encode()):
            # add only if result is ascii (otherwise "normalization" didn't work)
            language_names[unaccented_name] = lang_code

    dom = html.fromstring(resp.text)
    sp_lang_names = []
    for option in dom.xpath('//form[@name="settings"]//select[@name="language"]/option'):
        sp_lang_names.append((option.get('value'), extract_text(option).lower()))

    supported_languages = {}
    for sp_option_value, sp_option_text in sp_lang_names:
        lang_code = language_names.get(sp_option_value) or language_names.get(sp_option_text)
        if isinstance(lang_code, str):
            supported_languages[lang_code] = {'alias': sp_option_value}
        elif isinstance(lang_code, list):
            for _lc in lang_code:
                supported_languages[_lc] = {'alias': sp_option_value}
        else:
            print('Unknown language option in Startpage: {} ({})'.format(sp_option_value, sp_option_text))

    return supported_languages


def fetch_traits(engine_traits: EngineTraits):
    """Fetch :ref:`languages <startpage languages>` and :ref:`regions <startpage
    regions>` from Startpage."""
    # pylint: disable=import-outside-toplevel, too-many-locals, too-many-branches
    # pylint: disable=too-many-statements

    engine_traits.data_type = 'supported_languages'  # deprecated

    import babel
    from searx.utils import gen_useragent
    from searx.locales import region_tag

    headers = {
        'User-Agent': gen_useragent(),
        'Accept-Language': "en-US,en;q=0.5",  # bing needs to set the English language
    }
    resp = network.get('https://www.startpage.com/do/settings', headers=headers)

    if not resp.ok:
        print("ERROR: response from Startpage is not OK.")

    dom = html.fromstring(resp.text)

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

    for lang_code in filter(lambda lang_code: lang_code.find('_') == -1, babel.localedata.locale_identifiers()):
        native_name = babel.Locale(lang_code).get_language_name().lower()
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
        name = extract_text(option).lower()

        sxng_tag = catalog_engine2code.get(eng_tag)
        if sxng_tag is None:
            sxng_tag = catalog_engine2code[name]

        conflict = engine_traits.languages.get(sxng_tag)
        if conflict:
            if conflict != eng_tag:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, eng_tag))
            continue
        engine_traits.languages[sxng_tag] = eng_tag
