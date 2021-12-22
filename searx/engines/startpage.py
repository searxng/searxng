# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Startpage (Web)
"""

from lxml import html
from dateutil import parser
from datetime import datetime, timedelta
import re
from unicodedata import normalize, combining
from babel import Locale
from babel.localedata import locale_identifiers
from searx.utils import extract_text, eval_xpath, match_language

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
search_url = base_url + 'do/search'

# specific xpath variables
# ads xpath //div[@id="results"]/div[@id="sponsored"]//div[@class="result"]
# not ads: div[@class="result"] are the direct childs of div[@id="results"]
results_xpath = '//div[@class="w-gl__result__main"]'
link_xpath = './/a[@class="w-gl__result-title result-link"]'
content_xpath = './/p[@class="w-gl__description"]'


# do search-request
def request(query, params):

    params['url'] = search_url
    params['method'] = 'POST'
    params['data'] = {
        'query': query,
        'page': params['pageno'],
        'cat': 'web',
        'cmd': 'process_search',
        'engine0': 'v1all',
    }

    # set language if specified
    if params['language'] != 'all':
        lang_code = match_language(params['language'], supported_languages, fallback=None)
        if lang_code:
            language_name = supported_languages[lang_code]['alias']
            params['data']['language'] = language_name
            params['data']['lui'] = language_name

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
    # startpage's language selector is a mess
    # each option has a displayed name and a value, either of which may represent the language name
    # in the native script, the language name in English, an English transliteration of the native name,
    # the English name of the writing script used by the language, or occasionally something else entirely.

    # this cases are so special they need to be hardcoded, a couple of them are mispellings
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
    language_names.update({name.lower(): lang_code for lang_code, name in Locale('en')._data['languages'].items()})

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
    for option in dom.xpath('//form[@id="settings-form"]//select[@name="language"]/option'):
        sp_lang_names.append((option.get('value'), extract_text(option).lower()))

    supported_languages = {}
    for sp_option_value, sp_option_text in sp_lang_names:
        lang_code = language_names.get(sp_option_value) or language_names.get(sp_option_text)
        if isinstance(lang_code, str):
            supported_languages[lang_code] = {'alias': sp_option_value}
        elif isinstance(lang_code, list):
            for lc in lang_code:
                supported_languages[lc] = {'alias': sp_option_value}
        else:
            print('Unknown language option in Startpage: {} ({})'.format(sp_option_value, sp_option_text))

    return supported_languages
