# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This module implements functions needed for the autocompleter.

"""
# pylint: disable=use-dict-literal

import json
from urllib.parse import urlencode

import lxml
from httpx import HTTPError

from searx import settings
from searx.engines import (
    engines,
    google,
)
from searx.network import get as http_get
from searx.exceptions import SearxEngineResponseException


def get(*args, **kwargs):
    if 'timeout' not in kwargs:
        kwargs['timeout'] = settings['outgoing']['request_timeout']
    kwargs['raise_for_httperror'] = True
    return http_get(*args, **kwargs)


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
    if resp.ok:
        json_txt = resp.text[resp.text.find('[') : resp.text.find(']', -3) + 1]
        data = json.loads(json_txt)
        for item in data[0]:
            results.append(lxml.html.fromstring(item[0]).text_content())
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


def startpage(query, sxng_locale):
    """Autocomplete from Startpage. Supports Startpage's languages"""
    lui = engines['startpage'].traits.get_language(sxng_locale, 'english')
    url = 'https://startpage.com/suggestions?{query}'
    resp = get(url.format(query=urlencode({'q': query, 'segment': 'startpage.udog', 'lui': lui})))
    data = resp.json()
    return [e['text'] for e in data.get('suggestions', []) if 'text' in e]


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
    wiki_netloc = eng_traits.custom['wiki_netloc'].get(wiki_lang, 'en.wikipedia.org')

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
    'dbpedia': dbpedia,
    'duckduckgo': duckduckgo,
    'google': google_complete,
    'seznam': seznam,
    'startpage': startpage,
    'swisscows': swisscows,
    'qwant': qwant,
    'wikipedia': wikipedia,
    'brave': brave,
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
