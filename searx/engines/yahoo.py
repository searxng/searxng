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

locale_aliases = {
    'zh': 'zh_Hans',
    'zh-HK': 'zh_Hans',
    'zh-CN': 'zh_Hans',  # dead since 2015 / routed to hk.search.yahoo.com
    'zh-TW': 'zh_Hant',
}


def request(query, params):
    """build request"""

    lang = locale_aliases.get(params['language'], None)
    if not lang:
        lang = params['language'].split('-')[0]
    lang = traits.get_language(lang, traits.all_locale)

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


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages from yahoo"""

    # pylint: disable=import-outside-toplevel
    import babel
    from searx import network
    from searx.locales import language_tag

    engine_traits.all_locale = 'any'

    resp = network.get('https://search.yahoo.com/preferences/languages')
    if not resp.ok:
        print("ERROR: response from peertube is not OK.")

    dom = html.fromstring(resp.text)
    offset = len('lang_')

    eng2sxng = {'zh_chs': 'zh_Hans', 'zh_cht': 'zh_Hant'}

    for val in eval_xpath_list(dom, '//div[contains(@class, "lang-item")]/input/@value'):
        eng_tag = val[offset:]

        try:
            sxng_tag = language_tag(babel.Locale.parse(eng2sxng.get(eng_tag, eng_tag)))
        except babel.UnknownLocaleError:
            print('ERROR: unknown language --> %s' % eng_tag)
            continue

        conflict = engine_traits.languages.get(sxng_tag)
        if conflict:
            if conflict != eng_tag:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, eng_tag))
            continue
        engine_traits.languages[sxng_tag] = eng_tag
