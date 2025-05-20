# SPDX-License-Identifier: AGPL-3.0-or-later
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
    html_to_text,
)
from searx.enginelib.traits import EngineTraits

traits: EngineTraits

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
# send_accept_language_header = True

time_range_dict = {
    'day': ('1d', 'd'),
    'week': ('1w', 'w'),
    'month': ('1m', 'm'),
}

lang2domain = {
    'zh_chs': 'hk.search.yahoo.com',
    'zh_cht': 'tw.search.yahoo.com',
    'any': 'search.yahoo.com',
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

yahoo_languages = {
    "all": "any",
    "ar": "ar",
    "bg": "bg",
    "cs": "cs",
    "da": "da",
    "de": "de",
    "el": "el",
    "en": "en",
    "es": "es",
    "et": "et",
    "fi": "fi",
    "fr": "fr",
    "he": "he",
    "hr": "hr",
    "hu": "hu",
    "it": "it",
    "ja": "ja",
    "ko": "ko",
    "lt": "lt",
    "lv": "lv",
    "nl": "nl",
    "no": "no",
    "pl": "pl",
    "pt": "pt",
    "ro": "ro",
    "ru": "ru",
    "sk": "sk",
    "sl": "sl",
    "sv": "sv",
    "th": "th",
    "tr": "tr",
    "zh": "zh_chs",
    "zh_Hans": "zh_chs",
    'zh-CN': "zh_chs",
    "zh_Hant": "zh_cht",
    "zh-HK": "zh_cht",
    'zh-TW': "zh_cht",
}


def request(query, params):
    """build request"""

    lang = params["language"].split("-")[0]
    lang = yahoo_languages.get(lang, "any")

    offset = (params['pageno'] - 1) * 7 + 1
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
        url = eval_xpath_getindex(result, './/div[contains(@class,"compTitle")]/a/@href', 0, default=None)
        if url is None:
            continue
        url = parse_url(url)

        title = eval_xpath_getindex(result, './/div[contains(@class,"compTitle")]/a/h3/span', 0, default='')
        title: str = extract_text(title)
        content = eval_xpath_getindex(result, './/div[contains(@class, "compText")]', 0, default='')
        content: str = extract_text(content, allow_none=True)

        # append result
        results.append(
            {
                'url': url,
                # title sometimes contains HTML tags / see
                # https://github.com/searxng/searxng/issues/3790
                'title': " ".join(html_to_text(title).strip().split()),
                'content': " ".join(html_to_text(content).strip().split()),
            }
        )

    for suggestion in eval_xpath_list(dom, '//div[contains(@class, "AlsoTry")]//table//a'):
        # append suggestion
        results.append({'suggestion': extract_text(suggestion)})

    return results
