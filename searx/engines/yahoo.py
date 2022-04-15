# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Yahoo Search (Web)

Languages are supported by mapping the language to a domain.  If domain is not
found in :py:obj:`lang2domain` URL ``<lang>.search.yahoo.com`` is used.

"""

from urllib.parse import (
    unquote,
    urlencode,
)
from lxml import html

from searx.utils import (
    eval_xpath_getindex,
    eval_xpath_list,
    extract_text,
    match_language,
)

# about
about = {
    "website": 'https://search.yahoo.com/',
    "wikidata_id": None,
    "official_api_documentation": 'https://developer.yahoo.com/api/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['general', 'web']
paging = True
time_range_support = True
supported_languages_url = 'https://search.yahoo.com/preferences/languages'
"""Supported languages are read from Yahoo preference page."""

time_range_dict = {
    'day': ('1d', 'd'),
    'week': ('1w', 'w'),
    'month': ('1m', 'm'),
}

language_aliases = {
    'zh-HK': 'zh_chs',
    'zh-CN': 'zh_chs',  # dead since 2015 / routed to hk.search.yahoo.com
    'zh-TW': 'zh_cht',
}

lang2domain = {
    'zh_chs': 'hk.search.yahoo.com',
    'zh_cht': 'tw.search.yahoo.com',
    'en': 'search.yahoo.com',
    'bg': 'search.yahoo.com',
    'cs': 'search.yahoo.com',
    'da': 'search.yahoo.com',
    'el': 'search.yahoo.com',
    'et': 'search.yahoo.com',
    'he': 'search.yahoo.com',
    'hr': 'search.yahoo.com',
    'ja': 'search.yahoo.com',
    'ko': 'search.yahoo.com',
    'sk': 'search.yahoo.com',
    'sl': 'search.yahoo.com',
}
"""Map language to domain"""


def _get_language(params):

    lang = language_aliases.get(params['language'])
    if lang is None:
        lang = match_language(params['language'], supported_languages, language_aliases)
    lang = lang.split('-')[0]
    logger.debug("params['language']: %s --> %s", params['language'], lang)
    return lang


def request(query, params):
    """build request"""
    offset = (params['pageno'] - 1) * 7 + 1
    lang = _get_language(params)
    age, btf = time_range_dict.get(params['time_range'], ('', ''))

    args = urlencode(
        {
            'p': query,
            'ei': 'UTF-8',
            'fl': 1,
            'vl': 'lang_' + lang,
            'btf': btf,
            'fr2': 'time',
            'age': age,
            'b': offset,
            'xargs': 0,
        }
    )

    domain = lang2domain.get(lang, '%s.search.yahoo.com' % lang)
    params['url'] = 'https://%s/search?%s' % (domain, args)
    return params


def parse_url(url_string):
    """remove yahoo-specific tracking-url"""

    endings = ['/RS', '/RK']
    endpositions = []
    start = url_string.find('http', url_string.find('/RU=') + 1)

    for ending in endings:
        endpos = url_string.rfind(ending)
        if endpos > -1:
            endpositions.append(endpos)

    if start == 0 or len(endpositions) == 0:
        return url_string

    end = min(endpositions)
    return unquote(url_string[start:end])


def response(resp):
    """parse response"""

    results = []
    dom = html.fromstring(resp.text)

    # parse results
    for result in eval_xpath_list(dom, '//div[contains(@class,"algo-sr")]'):
        url = eval_xpath_getindex(result, './/h3/a/@href', 0, default=None)
        if url is None:
            continue
        url = parse_url(url)

        title = eval_xpath_getindex(result, './/h3/a', 0, default=None)
        if title is None:
            continue
        offset = len(extract_text(title.xpath('span')))
        title = extract_text(title)[offset:]

        content = eval_xpath_getindex(result, './/div[contains(@class, "compText")]', 0, default='')
        content = extract_text(content, allow_none=True)

        # append result
        results.append({'url': url, 'title': title, 'content': content})

    for suggestion in eval_xpath_list(dom, '//div[contains(@class, "AlsoTry")]//table//a'):
        # append suggestion
        results.append({'suggestion': extract_text(suggestion)})

    return results


# get supported languages from their site
def _fetch_supported_languages(resp):
    supported_languages = []
    dom = html.fromstring(resp.text)
    offset = len('lang_')

    for val in eval_xpath_list(dom, '//div[contains(@class, "lang-item")]/input/@value'):
        supported_languages.append(val[offset:])

    return supported_languages
