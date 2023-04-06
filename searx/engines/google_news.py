# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
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

from typing import TYPE_CHECKING

from urllib.parse import urlencode
import base64
from lxml import html
import babel

from searx import locales
from searx.utils import (
    eval_xpath,
    eval_xpath_list,
    eval_xpath_getindex,
    extract_text,
)

from searx.engines.google import fetch_traits as _fetch_traits  # pylint: disable=unused-import
from searx.engines.google import (
    get_google_info,
    detect_google_sorry,
)
from searx.enginelib.traits import EngineTraits

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

traits: EngineTraits

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
# False here, otherwise checker will report safesearch-errors::
#
#  safesearch : results are identitical for safesearch=0 and safesearch=2
safesearch = True
# send_accept_language_header = True


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
    return params


def response(resp):
    """Get response from google's search request"""
    results = []
    detect_google_sorry(resp)

    # convert the text to dom
    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, '//div[@class="xrnccd"]'):

        # The first <a> tag in the <article> contains the link to the article
        # The href attribute of the <a> tag is a google internal link, we have
        # to decode

        href = eval_xpath_getindex(result, './article/a/@href', 0)
        href = href.split('?')[0]
        href = href.split('/')[-1]
        href = base64.urlsafe_b64decode(href + '====')
        href = href[href.index(b'http') :].split(b'\xd2')[0]
        href = href.decode()

        title = extract_text(eval_xpath(result, './article/h3[1]'))

        # The pub_date is mostly a string like 'yesertday', not a real
        # timezone date or time.  Therefore we can't use publishedDate.
        pub_date = extract_text(eval_xpath(result, './article//time'))
        pub_origin = extract_text(eval_xpath(result, './article//a[@data-n-tid]'))

        content = ' / '.join([x for x in [pub_origin, pub_date] if x])

        # The image URL is located in a preceding sibling <img> tag, e.g.:
        # "https://lh3.googleusercontent.com/DjhQh7DMszk.....z=-p-h100-w100"
        # These URL are long but not personalized (double checked via tor).

        img_src = extract_text(result.xpath('preceding-sibling::a/figure/img/@src'))

        results.append(
            {
                'url': href,
                'title': title,
                'content': content,
                'img_src': img_src,
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
