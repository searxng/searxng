# SPDX-License-Identifier: AGPL-3.0-or-later
"""This module implements functions needed for the autocompleter.

"""
# pylint: disable=use-dict-literal

import json
import html
from urllib.parse import urlencode, quote_plus

import lxml.etree
import lxml.html
from httpx import HTTPError

from searx.extended_types import SXNG_Response
from searx import settings
from searx.engines import (
    engines,
    google,
)
from searx.network import get as http_get, post as http_post
from searx.exceptions import SearxEngineResponseException
from searx.utils import extr, gen_useragent


def update_kwargs(**kwargs):
    if 'timeout' not in kwargs:
        kwargs['timeout'] = settings['outgoing']['request_timeout']
    kwargs['raise_for_httperror'] = True


def get(*args, **kwargs) -> SXNG_Response:
    update_kwargs(**kwargs)
    return http_get(*args, **kwargs)


def post(*args, **kwargs) -> SXNG_Response:
    update_kwargs(**kwargs)
    return http_post(*args, **kwargs)


def baidu(query, _lang):
    # baidu search autocompleter
    base_url = "https://www.baidu.com/sugrec?"
    response = get(base_url + urlencode({'ie': 'utf-8', 'json': 1, 'prod': 'pc', 'wd': query}))

    results = []

    if response.ok:
        data = response.json()
        if 'g' in data:
            for item in data['g']:
                results.append(item['q'])
    return results


def brave(query, _lang):
    # brave search autocompleter
    url = 'https://search.brave.com/api/suggest?'
    url += urlencode({'q': query})
    country = 'all'
    # if lang in _brave:
    #    country = lang
    kwargs = {'cookies': {'country': country}}
    resp = get(url, **kwargs)

    results = []

    if resp.ok:
        data = resp.json()
        for item in data[1]:
            results.append(item)
    return results


def dbpedia(query, _lang):
    # dbpedia autocompleter, no HTTPS
    autocomplete_url = 'https://lookup.dbpedia.org/api/search.asmx/KeywordSearch?'

    response = get(autocomplete_url + urlencode(dict(QueryString=query)))

    results = []

    if response.ok:
        dom = lxml.etree.fromstring(response.content)
        results = dom.xpath('//Result/Label//text()')

    return results


def duckduckgo(query, sxng_locale):
    """Autocomplete from DuckDuckGo. Supports DuckDuckGo's languages"""

    traits = engines['duckduckgo'].traits
    args = {
        'q': query,
        'kl': traits.get_region(sxng_locale, traits.all_locale),
    }

    url = 'https://duckduckgo.com/ac/?type=list&' + urlencode(args)
    resp = get(url)

    ret_val = []
    if resp.ok:
        j = resp.json()
        if len(j) > 1:
            ret_val = j[1]
    return ret_val


def google_complete(query, sxng_locale):
    """Autocomplete from Google.  Supports Google's languages and subdomains
    (:py:obj:`searx.engines.google.get_google_info`) by using the async REST
    API::

        https://{subdomain}/complete/search?{args}

    """

    google_info = google.get_google_info({'searxng_locale': sxng_locale}, engines['google'].traits)

    url = 'https://{subdomain}/complete/search?{args}'
    args = urlencode(
        {
            'q': query,
            'client': 'gws-wiz',
            'hl': google_info['params']['hl'],
        }
    )
    results = []
    resp = get(url.format(subdomain=google_info['subdomain'], args=args))
    if resp and resp.ok:
        json_txt = resp.text[resp.text.find('[') : resp.text.find(']', -3) + 1]
        data = json.loads(json_txt)
        for item in data[0]:
            results.append(lxml.html.fromstring(item[0]).text_content())
    return results


def mwmbl(query, _lang):
    """Autocomplete from Mwmbl_."""

    # mwmbl autocompleter
    url = 'https://api.mwmbl.org/search/complete?{query}'

    results = get(url.format(query=urlencode({'q': query}))).json()[1]

    # results starting with `go:` are direct urls and not useful for auto completion
    return [result for result in results if not result.startswith("go: ") and not result.startswith("search: ")]


def naver(query, _lang):
    # Naver search autocompleter
    url = f"https://ac.search.naver.com/nx/ac?{urlencode({'q': query, 'r_format': 'json', 'st': 0})}"
    response = get(url)

    results = []

    if response.ok:
        data = response.json()
        if data.get('items'):
            for item in data['items'][0]:
                results.append(item[0])
    return results


def qihu360search(query, _lang):
    # 360Search search autocompleter
    url = f"https://sug.so.360.cn/suggest?{urlencode({'format': 'json', 'word': query})}"
    response = get(url)

    results = []

    if response.ok:
        data = response.json()
        if 'result' in data:
            for item in data['result']:
                results.append(item['word'])
    return results


def quark(query, _lang):
    # Quark search autocompleter
    url = f"https://sugs.m.sm.cn/web?{urlencode({'q': query})}"
    response = get(url)

    results = []

    if response.ok:
        data = response.json()
        for item in data.get('r', []):
            results.append(item['w'])
    return results


def seznam(query, _lang):
    # seznam search autocompleter
    url = 'https://suggest.seznam.cz/fulltext/cs?{query}'

    resp = get(
        url.format(
            query=urlencode(
                {'phrase': query, 'cursorPosition': len(query), 'format': 'json-2', 'highlight': '1', 'count': '6'}
            )
        )
    )

    if not resp.ok:
        return []

    data = resp.json()
    return [
        ''.join([part.get('text', '') for part in item.get('text', [])])
        for item in data.get('result', [])
        if item.get('itemType', None) == 'ItemType.TEXT'
    ]


def sogou(query, _lang):
    # Sogou search autocompleter
    base_url = "https://sor.html5.qq.com/api/getsug?"
    response = get(base_url + urlencode({'m': 'searxng', 'key': query}))

    if response.ok:
        raw_json = extr(response.text, "[", "]", default="")

        try:
            data = json.loads(f"[{raw_json}]]")
            return data[1]
        except json.JSONDecodeError:
            return []

    return []


def startpage(query, sxng_locale):
    """Autocomplete from Startpage's Firefox extension.
    Supports the languages specified in lang_map.
    """

    lang_map = {
        'da': 'dansk',
        'de': 'deutsch',
        'en': 'english',
        'es': 'espanol',
        'fr': 'francais',
        'nb': 'norsk',
        'nl': 'nederlands',
        'pl': 'polski',
        'pt': 'portugues',
        'sv': 'svenska',
    }

    base_lang = sxng_locale.split('-')[0]
    lui = lang_map.get(base_lang, 'english')

    url_params = {
        'q': query,
        'format': 'opensearch',
        'segment': 'startpage.defaultffx',
        'lui': lui,
    }
    url = f'https://www.startpage.com/suggestions?{urlencode(url_params)}'

    # Needs user agent, returns a 204 otherwise
    h = {'User-Agent': gen_useragent()}

    resp = get(url, headers=h)

    if resp.ok:
        try:
            data = resp.json()

            if len(data) >= 2 and isinstance(data[1], list):
                return data[1]
        except json.JSONDecodeError:
            pass

    return []


def stract(query, _lang):
    # stract autocompleter (beta)
    url = f"https://stract.com/beta/api/autosuggest?q={quote_plus(query)}"

    resp = post(url)

    if not resp.ok:
        return []

    return [html.unescape(suggestion['raw']) for suggestion in resp.json()]


def swisscows(query, _lang):
    # swisscows autocompleter
    url = 'https://swisscows.ch/api/suggest?{query}&itemsCount=5'

    resp = json.loads(get(url.format(query=urlencode({'query': query}))).text)
    return resp


def qwant(query, sxng_locale):
    """Autocomplete from Qwant. Supports Qwant's regions."""
    results = []

    locale = engines['qwant'].traits.get_region(sxng_locale, 'en_US')
    url = 'https://api.qwant.com/v3/suggest?{query}'
    resp = get(url.format(query=urlencode({'q': query, 'locale': locale, 'version': '2'})))

    if resp.ok:
        data = resp.json()
        if data['status'] == 'success':
            for item in data['data']['items']:
                results.append(item['value'])

    return results


def wikipedia(query, sxng_locale):
    """Autocomplete from Wikipedia. Supports Wikipedia's languages (aka netloc)."""
    results = []
    eng_traits = engines['wikipedia'].traits
    wiki_lang = eng_traits.get_language(sxng_locale, 'en')
    wiki_netloc = eng_traits.custom['wiki_netloc'].get(wiki_lang, 'en.wikipedia.org')  # type: ignore

    url = 'https://{wiki_netloc}/w/api.php?{args}'
    args = urlencode(
        {
            'action': 'opensearch',
            'format': 'json',
            'formatversion': '2',
            'search': query,
            'namespace': '0',
            'limit': '10',
        }
    )
    resp = get(url.format(args=args, wiki_netloc=wiki_netloc))
    if resp.ok:
        data = resp.json()
        if len(data) > 1:
            results = data[1]

    return results


def yandex(query, _lang):
    # yandex autocompleter
    url = "https://suggest.yandex.com/suggest-ff.cgi?{0}"

    resp = json.loads(get(url.format(urlencode(dict(part=query)))).text)
    if len(resp) > 1:
        return resp[1]
    return []


backends = {
    '360search': qihu360search,
    'baidu': baidu,
    'brave': brave,
    'dbpedia': dbpedia,
    'duckduckgo': duckduckgo,
    'google': google_complete,
    'mwmbl': mwmbl,
    'naver': naver,
    'quark': quark,
    'qwant': qwant,
    'seznam': seznam,
    'sogou': sogou,
    'startpage': startpage,
    'stract': stract,
    'swisscows': swisscows,
    'wikipedia': wikipedia,
    'yandex': yandex,
}


def search_autocomplete(backend_name, query, sxng_locale):
    backend = backends.get(backend_name)
    if backend is None:
        return []
    try:
        return backend(query, sxng_locale)
    except (HTTPError, SearxEngineResponseException):
        return []
