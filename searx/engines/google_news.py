# SPDX-License-Identifier: AGPL-3.0-or-later
"""This is the implementation of the Google News engine.

Google News has a different region handling compared to Google WEB.

- the ``ceid`` argument has to be set (:py:obj:`ceid_list`)
- the hl_ argument has to be set correctly (and different to Google WEB)
- the gl_ argument is mandatory

If one of this argument is not set correctly, the request is redirected to
CONSENT dialog::

  https://consent.google.com/m?continue=

The google news API ignores some parameters from the common :ref:`google API`:

- num_ : the number of search results is ignored / there is no paging all
  results for a query term are in the first response.
- save_ : is ignored / Google-News results are always *SafeSearch*

.. _hl: https://developers.google.com/custom-search/docs/xml_results#hlsp
.. _gl: https://developers.google.com/custom-search/docs/xml_results#glsp
.. _num: https://developers.google.com/custom-search/docs/xml_results#numsp
.. _save: https://developers.google.com/custom-search/docs/xml_results#safesp
"""

import re
import json
import base64
from urllib.parse import urlencode
from lxml import html
import babel

from searx import locales, get_setting
from searx.utils import (
    eval_xpath,
    eval_xpath_list,
    eval_xpath_getindex,
    extract_text,
)
from searx.webutils import new_hmac

from searx.engines.google import fetch_traits as _fetch_traits  # pylint: disable=unused-import
from searx.engines.google import (
    get_google_info,
    detect_google_sorry,
)
from searx.enginelib.traits import EngineTraits

# about
about = {
    "website": 'https://news.google.com',
    "wikidata_id": 'Q12020',
    "official_api_documentation": 'https://developers.google.com/custom-search',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['news']
paging = False
time_range_support = False

# Google-News results are always *SafeSearch*. Option 'safesearch' is set to
# False here.
#
#  safesearch : results are identical for safesearch=0 and safesearch=2
safesearch = True


def request(query, params):
    """Google-News search request"""

    sxng_locale = params.get('searxng_locale', 'en-US')
    ceid = locales.get_engine_locale(sxng_locale, traits.custom['ceid'], default='US:en')
    google_info = get_google_info(params, traits)
    google_info['subdomain'] = 'news.google.com'  # google news has only one domain

    ceid_region, ceid_lang = ceid.split(':')
    ceid_lang, ceid_suffix = (
        ceid_lang.split('-')
        + [
            None,
        ]
    )[:2]

    google_info['params']['hl'] = ceid_lang

    if ceid_suffix and ceid_suffix not in ['Hans', 'Hant']:

        if ceid_region.lower() == ceid_lang:
            google_info['params']['hl'] = ceid_lang + '-' + ceid_region
        else:
            google_info['params']['hl'] = ceid_lang + '-' + ceid_suffix

    elif ceid_region.lower() != ceid_lang:

        if ceid_region in ['AT', 'BE', 'CH', 'IL', 'SA', 'IN', 'BD', 'PT']:
            google_info['params']['hl'] = ceid_lang
        else:
            google_info['params']['hl'] = ceid_lang + '-' + ceid_region

    google_info['params']['lr'] = 'lang_' + ceid_lang.split('-')[0]
    google_info['params']['gl'] = ceid_region

    query_url = (
        'https://'
        + google_info['subdomain']
        + "/search?"
        + urlencode(
            {
                'q': query,
                **google_info['params'],
            }
        )
        # ceid includes a ':' character which must not be urlencoded
        + ('&ceid=%s' % ceid)
    )

    params['url'] = query_url
    params['cookies'] = google_info['cookies']
    params['headers'].update(google_info['headers'])
    # Use a fixed modern browser UA to ensure consistent HTML structure and avoid blocking
    params['headers']['User-Agent'] = (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    return params


def response(resp):
    """Get response from google's search request"""
    results = []
    detect_google_sorry(resp)

    # convert the text to dom
    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, '//div[contains(@class, "IFHyqb")]'):

        # The link to the article is in a tag with class "JtKRv"
        # However, the real URL is often encoded in the "jslog" attribute of a sibling tag with class "WwrzSb"
        href = eval_xpath_getindex(result, './/a[contains(@class, "JtKRv")]/@href', 0, default=None)
        if not href:
            continue

        url = href
        if href.startswith('./'):
            url = 'https://news.google.com' + href[1:]

        # Try to extract the real URL from jslog
        jslog = eval_xpath_getindex(result, './/a[contains(@class, "WwrzSb")]/@jslog', 0, default=None)
        if jslog:
            try:
                # jslog format is usually: "95014; 5:<base64>; track:click,vis"
                # We want the second part (index 1) after splitting by ";"
                parts = jslog.split(';')
                if len(parts) > 1:
                    b64_data = parts[1].split(':')[-1].strip()
                    # Pad base64 if necessary
                    b64_data += '=' * (-len(b64_data) % 4)
                    decoded_data = json.loads(base64.b64decode(b64_data).decode('utf-8'))
                    # The URL is typically the last element in the decoded array
                    if isinstance(decoded_data, list) and len(decoded_data) > 0 and isinstance(decoded_data[-1], str):
                        if decoded_data[-1].startswith('http'):
                            url = decoded_data[-1]
            except Exception:  # pylint: disable=broad-except
                pass

        title = extract_text(eval_xpath(result, './/a[contains(@class, "JtKRv")]'))

        # The pub_date is mostly a string like 'yesterday', not a real
        # timezone date or time.  Therefore we can't use publishedDate.
        pub_date = extract_text(eval_xpath(result, './/time'))
        pub_origin = extract_text(eval_xpath(result, './/div[contains(@class, "vr1PYe")]'))

        content = ' / '.join([x for x in [pub_origin, pub_date] if x])

        # The image URL is often in an <img> tag with class "Quavad"
        thumbnail = eval_xpath_getindex(result, './/img[contains(@class, "Quavad")]/@src', 0, default=None)
        if not thumbnail:
            # Fallback to any image that isn't a favicon
            thumbnail = eval_xpath_getindex(result, './/img[not(contains(@src, "favicon"))]/@src', 0, default=None)

        if thumbnail and thumbnail.startswith('/'):
            thumbnail = 'https://news.google.com' + thumbnail

        # Force proxy for Google News thumbnails to avoid Referer/CORP blocks
        # This is agnostic and uses the standard Google-provided thumbnails
        if thumbnail and 'news.google.com/api/attachments' in thumbnail:
            h = new_hmac(get_setting('server.secret_key'), thumbnail.encode())
            thumbnail = '/image_proxy?' + urlencode(dict(url=thumbnail.encode(), h=h))

        results.append(
            {
                'url': url,
                'title': title,
                'content': content,
                'thumbnail': thumbnail,
            }
        )

    # return results
    return results


ceid_list = [
    'AE:ar',
    'AR:es-419',
    'AT:de',
    'AU:en',
    'BD:bn',
    'BE:fr',
    'BE:nl',
    'BG:bg',
    'BR:pt-419',
    'BW:en',
    'CA:en',
    'CA:fr',
    'CH:de',
    'CH:fr',
    'CL:es-419',
    'CN:zh-Hans',
    'CO:es-419',
    'CU:es-419',
    'CZ:cs',
    'DE:de',
    'EG:ar',
    'ES:es',
    'ET:en',
    'FR:fr',
    'GB:en',
    'GH:en',
    'GR:el',
    'HK:zh-Hant',
    'HU:hu',
    'ID:en',
    'ID:id',
    'IE:en',
    'IL:en',
    'IL:he',
    'IN:bn',
    'IN:en',
    'IN:hi',
    'IN:ml',
    'IN:mr',
    'IN:ta',
    'IN:te',
    'IT:it',
    'JP:ja',
    'KE:en',
    'KR:ko',
    'LB:ar',
    'LT:lt',
    'LV:en',
    'LV:lv',
    'MA:fr',
    'MX:es-419',
    'MY:en',
    'NA:en',
    'NG:en',
    'NL:nl',
    'NO:no',
    'NZ:en',
    'PE:es-419',
    'PE:es',
    'PH:en',
    'PK:en',
    'PL:pl',
    'PT:pt-150',
    'RO:ro',
    'RS:sr',
    'RU:ru',
    'SA:ar',
    'SE:sv',
    'SG:en',
    'SI:sl',
    'SK:sk',
    'SN:fr',
    'TH:th',
    'TR:tr',
    'TW:zh-Hant',
    'TZ:en',
    'UA:ru',
    'UA:uk',
    'UG:en',
    'US:en',
    'US:es-419',
    'VE:es-419',
    'VN:vi',
    'ZA:en',
    'ZW:en',
]
"""List of region/language combinations supported by Google News.  Values of the
``ceid`` argument of the Google News REST API."""


_skip_values = [
    'ET:en',  # english (ethiopia)
    'ID:en',  # english (indonesia)
    'LV:en',  # english (latvia)
]

_ceid_locale_map = {'NO:no': 'nb-NO'}


def fetch_traits(engine_traits: EngineTraits):
    _fetch_traits(engine_traits, add_domains=False)

    engine_traits.custom['ceid'] = {}

    for ceid in ceid_list:
        if ceid in _skip_values:
            continue

        region, lang = ceid.split(':')
        x = lang.split('-')
        if len(x) > 1:
            if x[1] not in ['Hant', 'Hans']:
                lang = x[0]

        sxng_locale = _ceid_locale_map.get(ceid, lang + '-' + region)
        try:
            locale = babel.Locale.parse(sxng_locale, sep='-')
        except babel.UnknownLocaleError:
            print("ERROR: %s -> %s is unknown by babel" % (ceid, sxng_locale))
            continue

        engine_traits.custom['ceid'][locales.region_tag(locale)] = ceid
