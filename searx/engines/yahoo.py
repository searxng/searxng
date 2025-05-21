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

region2domain = {
    "CO": "co.search.yahoo.com",  # Colombia
    "TH": "th.search.yahoo.com",  # Thailand
    "VE": "ve.search.yahoo.com",  # Venezuela
    "CL": "cl.search.yahoo.com",  # Chile
    "HK": "hk.search.yahoo.com",  # Hong Kong
    "PE": "pe.search.yahoo.com",  # Peru
    "CA": "ca.search.yahoo.com",  # Canada
    "DE": "de.search.yahoo.com",  # Germany
    "FR": "fr.search.yahoo.com",  # France
    "TW": "tw.search.yahoo.com",  # Taiwan
    "GB": "uk.search.yahoo.com",  # United Kingdom
    "UK": "uk.search.yahoo.com",
    "BR": "br.search.yahoo.com",  # Brazil
    "IN": "in.search.yahoo.com",  # India
    "ES": "espanol.search.yahoo.com",  # Espanol
    "PH": "ph.search.yahoo.com",  # Philippines
    "AR": "ar.search.yahoo.com",  # Argentina
    "MX": "mx.search.yahoo.com",  # Mexico
    "SG": "sg.search.yahoo.com",  # Singapore
}
"""Map regions to domain"""

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
    "ar": "ar",  # Arabic
    "bg": "bg",  # Bulgarian
    "cs": "cs",  # Czech
    "da": "da",  # Danish
    "de": "de",  # German
    "el": "el",  # Greek
    "en": "en",  # English
    "es": "es",  # Spanish
    "et": "et",  # Estonian
    "fi": "fi",  # Finnish
    "fr": "fr",  # French
    "he": "he",  # Hebrew
    "hr": "hr",  # Croatian
    "hu": "hu",  # Hungarian
    "it": "it",  # Italian
    "ja": "ja",  # Japanese
    "ko": "ko",  # Korean
    "lt": "lt",  # Lithuanian
    "lv": "lv",  # Latvian
    "nl": "nl",  # Dutch
    "no": "no",  # Norwegian
    "pl": "pl",  # Polish
    "pt": "pt",  # Portuguese
    "ro": "ro",  # Romanian
    "ru": "ru",  # Russian
    "sk": "sk",  # Slovak
    "sl": "sl",  # Slovenian
    "sv": "sv",  # Swedish
    "th": "th",  # Thai
    "tr": "tr",  # Turkish
    "zh": "zh_chs",  # Chinese (Simplified)
    "zh_Hans": "zh_chs",
    'zh-CN': "zh_chs",
    "zh_Hant": "zh_cht",  # Chinese (Traditional)
    "zh-HK": "zh_cht",
    'zh-TW': "zh_cht",
}


def request(query, params):
    """build request"""

    lang, region = (params["language"].split("-") + [None])[:2]
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

    domain = region2domain.get(region)
    if not domain:
        domain = lang2domain.get(lang, '%s.search.yahoo.com' % lang)
    params['url'] = 'https://%s/search?%s' % (domain, args)
    params['domain'] = domain


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

    url_xpath = './/div[contains(@class,"compTitle")]/h3/a/@href'
    title_xpath = './/h3//a/@aria-label'

    domain = resp.search_params['domain']
    if domain == "search.yahoo.com":
        url_xpath = './/div[contains(@class,"compTitle")]/a/@href'
        title_xpath = './/div[contains(@class,"compTitle")]/a/h3/span'

    # parse results
    for result in eval_xpath_list(dom, '//div[contains(@class,"algo-sr")]'):
        url = eval_xpath_getindex(result, url_xpath, 0, default=None)
        if url is None:
            continue
        url = parse_url(url)

        title = eval_xpath_getindex(result, title_xpath, 0, default='')
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
