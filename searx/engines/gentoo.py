# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Gentoo Wiki
"""

from urllib.parse import urlencode, urljoin
from lxml import html
from searx.utils import extract_text

# about
about = {
    "website": 'https://wiki.gentoo.org/',
    "wikidata_id": 'Q1050637',
    "official_api_documentation": 'https://wiki.gentoo.org/api.php',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['it', 'software wikis']
paging = True
base_url = 'https://wiki.gentoo.org'

# xpath queries
xpath_results = '//ul[@class="mw-search-results"]/li'
xpath_link = './/div[@class="mw-search-result-heading"]/a'


# cut 'en' from 'en-US', 'de' from 'de-CH', and so on
def locale_to_lang_code(locale):
    if locale.find('-') >= 0:
        locale = locale.split('-')[0]
    return locale


# wikis for some languages were moved off from the main site, we need to make
# requests to correct URLs to be able to get results in those languages
lang_urls = {
    'en': {'base': 'https://wiki.gentoo.org', 'search': '/index.php?title=Special:Search&offset={offset}&{query}'},
    'others': {
        'base': 'https://wiki.gentoo.org',
        'search': '/index.php?title=Special:Search&offset={offset}&{query}\
                &profile=translation&languagefilter={language}',
    },
}


# get base & search URLs for selected language
def get_lang_urls(language):
    if language != 'en':
        return lang_urls['others']
    return lang_urls['en']


# Language names to build search requests for
# those languages which are hosted on the main site.
main_langs = {
    'ar': 'العربية',
    'bg': 'Български',
    'cs': 'Česky',
    'da': 'Dansk',
    'el': 'Ελληνικά',
    'es': 'Español',
    'he': 'עברית',
    'hr': 'Hrvatski',
    'hu': 'Magyar',
    'it': 'Italiano',
    'ko': '한국어',
    'lt': 'Lietuviškai',
    'nl': 'Nederlands',
    'pl': 'Polski',
    'pt': 'Português',
    'ru': 'Русский',
    'sl': 'Slovenský',
    'th': 'ไทย',
    'uk': 'Українська',
    'zh': '简体中文',
}
supported_languages = dict(lang_urls, **main_langs)


# do search-request
def request(query, params):
    # translate the locale (e.g. 'en-US') to language code ('en')
    language = locale_to_lang_code(params['language'])

    # if our language is hosted on the main site, we need to add its name
    # to the query in order to narrow the results to that language
    if language in main_langs:
        query += ' (' + main_langs[language] + ')'

    # prepare the request parameters
    query = urlencode({'search': query})
    offset = (params['pageno'] - 1) * 20

    # get request URLs for our language of choice
    urls = get_lang_urls(language)
    search_url = urls['base'] + urls['search']

    params['url'] = search_url.format(query=query, offset=offset, language=language)

    return params


# get response from search-request
def response(resp):
    # get the base URL for the language in which request was made
    language = locale_to_lang_code(resp.search_params['language'])
    base_url = get_lang_urls(language)['base']

    results = []

    dom = html.fromstring(resp.text)

    # parse results
    for result in dom.xpath(xpath_results):
        link = result.xpath(xpath_link)[0]
        href = urljoin(base_url, link.attrib.get('href'))
        title = extract_text(link)

        results.append({'url': href, 'title': title})

    return results
