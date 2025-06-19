# SPDX-License-Identifier: AGPL-3.0-or-later
"""Yahoo Search (Web)

Languages are supported by mapping the language to a domain.  If domain is not
found in :py:obj:`lang2domain` URL ``<lang>.search.yahoo.com`` is used.

"""

from typing import TYPE_CHECKING
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

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

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

time_range_dict = {'day': 'd', 'week': 'w', 'month': 'm'}
safesearch_dict = {0: 'p', 1: 'i', 2: 'r'}

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
    "zh": "zh_chs",  # Chinese (Simplified)
    "zh_Hans": "zh_chs",
    'zh-CN': "zh_chs",
    "zh_Hant": "zh_cht",  # Chinese (Traditional)
    "zh-HK": "zh_cht",
    'zh-TW': "zh_cht",
}


def build_sb_cookie(cookie_params):
    """Build sB cookie parameter from provided parameters.

    :param cookie_params: Dictionary of cookie parameters
    :type cookie_params: dict
    :returns: Formatted cookie string
    :rtype: str

    Example:
        >>> cookie_params = {'v': '1', 'vm': 'p', 'fl': '1', 'vl': 'lang_fr'}
        >>> build_sb_cookie(cookie_params)
        'v=1&vm=p&fl=1&vl=lang_fr'
    """

    cookie_parts = []
    for key, value in cookie_params.items():
        cookie_parts.append(f"{key}={value}")

    return "&".join(cookie_parts)


def request(query, params):
    """Build Yahoo search request."""

    lang, region = (params["language"].split("-") + [None])[:2]
    lang = yahoo_languages.get(lang, "any")

    # Build URL parameters
    # - p (str): Search query string
    # - btf (str): Time filter, maps to values like 'd' (day), 'w' (week), 'm' (month)
    # - iscqry (str): Empty string, necessary for results to appear properly on first page
    # - b (int): Search offset for pagination
    # - pz (str): Amount of results expected for the page
    url_params = {'p': query}

    btf = time_range_dict.get(params['time_range'])
    if btf:
        url_params['btf'] = btf

    if params['pageno'] == 1:
        url_params['iscqry'] = ''
    elif params['pageno'] >= 2:
        url_params['b'] = params['pageno'] * 7 + 1  #  8, 15, 21, etc.
        url_params['pz'] = 7
        url_params['bct'] = 0
        url_params['xargs'] = 0

    # Build sB cookie (for filters)
    # - vm (str): SafeSearch filter, maps to values like 'p' (None), 'i' (Moderate), 'r' (Strict)
    # - fl (bool): Indicates if a search language is used or not
    # - vl (str): The search language to use (e.g. lang_fr)
    sbcookie_params = {
        'v': 1,
        'vm': safesearch_dict[params['safesearch']],
        'fl': 1,
        'vl': f'lang_{lang}',
        'pn': 10,
        'rw': 'new',
        'userset': 1,
    }
    params['cookies']['sB'] = build_sb_cookie(sbcookie_params)

    # Search region/language
    domain = region2domain.get(region)
    if not domain:
        domain = lang2domain.get(lang, f'{lang}.search.yahoo.com')
    logger.debug(f'domain selected: {domain}')
    logger.debug(f'cookies: {params["cookies"]}')

    params['url'] = f'https://{domain}/search?{urlencode(url_params)}'
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
