# SPDX-License-Identifier: AGPL-3.0-or-later
"""
DuckDuckGo WEB
~~~~~~~~~~~~~~
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import re
from urllib.parse import quote_plus
import json
import babel
import lxml.html

from searx import (
    locales,
    redislib,
    external_bang,
)
from searx.utils import (
    eval_xpath,
    extr,
    extract_text,
)
from searx.network import get  # see https://github.com/searxng/searxng/issues/762
from searx import redisdb
from searx.enginelib.traits import EngineTraits
from searx.exceptions import SearxEngineCaptchaException
from searx.result_types import EngineResults

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

traits: EngineTraits

about = {
    "website": 'https://lite.duckduckgo.com/lite/',
    "wikidata_id": 'Q12805',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

send_accept_language_header = True
"""DuckDuckGo-Lite tries to guess user's preferred language from the HTTP
``Accept-Language``.  Optional the user can select a region filter (but not a
language).
"""

# engine dependent config
categories = ['general', 'web']
paging = True
time_range_support = True
safesearch = True  # user can't select but the results are filtered

url = "https://html.duckduckgo.com/html"

time_range_dict = {'day': 'd', 'week': 'w', 'month': 'm', 'year': 'y'}
form_data = {'v': 'l', 'api': 'd.js', 'o': 'json'}
__CACHE = []


def _cache_key(query: str, region: str):
    return 'SearXNG_ddg_web_vqd' + redislib.secret_hash(f"{query}//{region}")


def cache_vqd(query: str, region: str, value: str):
    """Caches a ``vqd`` value from a query."""
    c = redisdb.client()
    if c:
        logger.debug("VALKEY cache vqd value: %s (%s)", value, region)
        c.set(_cache_key(query, region), value, ex=600)

    else:
        logger.debug("MEM cache vqd value: %s (%s)", value, region)
        if len(__CACHE) > 100:  # cache vqd from last 100 queries
            __CACHE.pop(0)
        __CACHE.append((_cache_key(query, region), value))


def get_vqd(query: str, region: str, force_request: bool = False):
    """Returns the ``vqd`` that fits to the *query*.

    :param query: The query term
    :param region: DDG's region code
    :param force_request: force a request to get a vqd value from DDG

    TL;DR; the ``vqd`` value is needed to pass DDG's bot protection and is used
    by all request to DDG:

    - DuckDuckGo Lite: ``https://lite.duckduckgo.com/lite`` (POST form data)
    - DuckDuckGo Web: ``https://links.duckduckgo.com/d.js?q=...&vqd=...``
    - DuckDuckGo Images: ``https://duckduckgo.com/i.js??q=...&vqd=...``
    - DuckDuckGo Videos: ``https://duckduckgo.com/v.js??q=...&vqd=...``
    - DuckDuckGo News: ``https://duckduckgo.com/news.js??q=...&vqd=...``

    DDG's bot detection is sensitive to the ``vqd`` value.  For some search terms
    (such as extremely long search terms that are often sent by bots), no ``vqd``
    value can be determined.

    If SearXNG cannot determine a ``vqd`` value, then no request should go out
    to DDG.

    .. attention::

       A request with a wrong ``vqd`` value leads to DDG temporarily putting
       SearXNG's IP on a block list.

    Requests from IPs in this block list run into timeouts.  Not sure, but it
    seems the block list is a sliding window: to get my IP rid from the bot list
    I had to cool down my IP for 1h (send no requests from that IP to DDG).
    """
    key = _cache_key(query, region)

    c = redisdb.client()
    if c:
        value = c.get(key)
        if value or value == b'':
            value = value.decode('utf-8')  # type: ignore
            logger.debug("re-use CACHED vqd value: %s", value)
            return value

    for k, value in __CACHE:
        if k == key:
            logger.debug("MEM re-use CACHED vqd value: %s", value)
            return value

    if force_request:
        resp = get(f'https://duckduckgo.com/?q={quote_plus(query)}')
        if resp.status_code == 200:  # type: ignore
            value = extr(resp.text, 'vqd="', '"')  # type: ignore
            if value:
                logger.debug("vqd value from DDG request: %s", value)
                cache_vqd(query, region, value)
                return value

    return None


def get_ddg_lang(eng_traits: EngineTraits, sxng_locale, default='en_US'):
    """Get DuckDuckGo's language identifier from SearXNG's locale.

    DuckDuckGo defines its languages by region codes (see
    :py:obj:`fetch_traits`).

    To get region and language of a DDG service use:

    .. code: python

       eng_region = traits.get_region(params['searxng_locale'], traits.all_locale)
       eng_lang = get_ddg_lang(traits, params['searxng_locale'])

    It might confuse, but the ``l`` value of the cookie is what SearXNG calls
    the *region*:

    .. code:: python

        # !ddi paris :es-AR --> {'ad': 'es_AR', 'ah': 'ar-es', 'l': 'ar-es'}
        params['cookies']['ad'] = eng_lang
        params['cookies']['ah'] = eng_region
        params['cookies']['l'] = eng_region

    .. hint::

       `DDG-lite <https://lite.duckduckgo.com/lite>`__ and the *no Javascript*
       page https://html.duckduckgo.com/html do not offer a language selection
       to the user, only a region can be selected by the user (``eng_region``
       from the example above).  DDG-lite and *no Javascript* store the selected
       region in a cookie::

         params['cookies']['kl'] = eng_region  # 'ar-es'

    """
    return eng_traits.custom['lang_region'].get(  # type: ignore
        sxng_locale, eng_traits.get_language(sxng_locale, default)
    )


ddg_reg_map = {
    'tw-tzh': 'zh_TW',
    'hk-tzh': 'zh_HK',
    'ct-ca': 'skip',  # ct-ca and es-ca both map to ca_ES
    'es-ca': 'ca_ES',
    'id-en': 'id_ID',
    'no-no': 'nb_NO',
    'jp-jp': 'ja_JP',
    'kr-kr': 'ko_KR',
    'xa-ar': 'ar_SA',
    'sl-sl': 'sl_SI',
    'th-en': 'th_TH',
    'vn-en': 'vi_VN',
}

ddg_lang_map = {
    # use ar --> ar_EG (Egypt's arabic)
    "ar_DZ": 'lang_region',
    "ar_JO": 'lang_region',
    "ar_SA": 'lang_region',
    # use bn --> bn_BD
    'bn_IN': 'lang_region',
    # use de --> de_DE
    'de_CH': 'lang_region',
    # use en --> en_US,
    'en_AU': 'lang_region',
    'en_CA': 'lang_region',
    'en_GB': 'lang_region',
    # Esperanto
    'eo_XX': 'eo',
    # use es --> es_ES,
    'es_AR': 'lang_region',
    'es_CL': 'lang_region',
    'es_CO': 'lang_region',
    'es_CR': 'lang_region',
    'es_EC': 'lang_region',
    'es_MX': 'lang_region',
    'es_PE': 'lang_region',
    'es_UY': 'lang_region',
    'es_VE': 'lang_region',
    # use fr --> rf_FR
    'fr_CA': 'lang_region',
    'fr_CH': 'lang_region',
    'fr_BE': 'lang_region',
    # use nl --> nl_NL
    'nl_BE': 'lang_region',
    # use pt --> pt_PT
    'pt_BR': 'lang_region',
    # skip these languages
    'od_IN': 'skip',
    'io_XX': 'skip',
    'tokipona_XX': 'skip',
}


def quote_ddg_bangs(query):
    # quote ddg bangs
    query_parts = []

    # for val in re.split(r'(\s+)', query):
    for val in re.split(r'(\s+)', query):
        if not val.strip():
            continue
        if val.startswith('!') and external_bang.get_node(external_bang.EXTERNAL_BANGS, val[1:]):
            val = f"'{val}'"
        query_parts.append(val)
    return ' '.join(query_parts)


def request(query, params):

    query = quote_ddg_bangs(query)

    if len(query) >= 500:
        # DDG does not accept queries with more than 499 chars
        params["url"] = None
        return

    # Advanced search syntax ends in CAPTCHA
    # https://duckduckgo.com/duckduckgo-help-pages/results/syntax/
    query = " ".join(
        [
            x.removeprefix("site:").removeprefix("intitle:").removeprefix("inurl:").removeprefix("filetype:")
            for x in query.split()
        ]
    )
    eng_region: str = traits.get_region(params['searxng_locale'], traits.all_locale)  # type: ignore
    if eng_region == "wt-wt":
        # https://html.duckduckgo.com/html sets an empty value for "all".
        eng_region = ""

    params['data']['kl'] = eng_region
    params['cookies']['kl'] = eng_region

    # eng_lang = get_ddg_lang(traits, params['searxng_locale'])

    params['url'] = url
    params['method'] = 'POST'
    params['data']['q'] = query

    # The API is not documented, so we do some reverse engineering and emulate
    # what https://html.duckduckgo.com/html does when you press "next Page" link
    # again and again ..

    params['headers']['Content-Type'] = 'application/x-www-form-urlencoded'

    params['headers']['Sec-Fetch-Dest'] = "document"
    params['headers']['Sec-Fetch-Mode'] = "navigate"  # at least this one is used by ddg's bot detection
    params['headers']['Sec-Fetch-Site'] = "same-origin"
    params['headers']['Sec-Fetch-User'] = "?1"

    # Form of the initial search page does have empty values in the form
    if params['pageno'] == 1:

        params['data']['b'] = ""

    params['data']['df'] = ''
    if params['time_range'] in time_range_dict:

        params['data']['df'] = time_range_dict[params['time_range']]
        params['cookies']['df'] = time_range_dict[params['time_range']]

    if params['pageno'] == 2:

        # second page does have an offset of 20
        offset = (params['pageno'] - 1) * 20
        params['data']['s'] = offset
        params['data']['dc'] = offset + 1

    elif params['pageno'] > 2:

        # third and following pages do have an offset of 20 + n*50
        offset = 20 + (params['pageno'] - 2) * 50
        params['data']['s'] = offset
        params['data']['dc'] = offset + 1

    if params['pageno'] > 1:

        # initial page does not have these additional data in the input form
        params['data']['o'] = form_data.get('o', 'json')
        params['data']['api'] = form_data.get('api', 'd.js')
        params['data']['nextParams'] = form_data.get('nextParams', '')
        params['data']['v'] = form_data.get('v', 'l')
        params['headers']['Referer'] = url

        vqd = get_vqd(query, eng_region, force_request=False)

        # Certain conditions must be met in order to call up one of the
        # following pages ...

        if vqd:
            params['data']['vqd'] = vqd  # follow up pages / requests needs a vqd argument
        else:
            # Don't try to call follow up pages without a vqd value.  DDG
            # recognizes this as a request from a bot.  This lowers the
            # reputation of the SearXNG IP and DDG starts to activate CAPTCHAs.
            params["url"] = None
            return

        if params['searxng_locale'].startswith("zh"):
            # Some locales (at least China) do not have a "next page" button and ddg
            # will return a HTTP/2 403 Forbidden for a request of such a page.
            params["url"] = None
            return

    logger.debug("param data: %s", params['data'])
    logger.debug("param cookies: %s", params['cookies'])


def is_ddg_captcha(dom):
    """In case of CAPTCHA ddg response its own *not a Robot* dialog and is not
    redirected to a CAPTCHA page."""

    return bool(eval_xpath(dom, "//form[@id='challenge-form']"))


def response(resp) -> EngineResults:
    results = EngineResults()

    if resp.status_code == 303:
        return results

    doc = lxml.html.fromstring(resp.text)

    if is_ddg_captcha(doc):
        # set suspend time to zero is OK --> ddg does not block the IP
        raise SearxEngineCaptchaException(suspended_time=0, message=f"CAPTCHA ({resp.search_params['data'].get('kl')})")

    form = eval_xpath(doc, '//input[@name="vqd"]/..')
    if len(form):
        # some locales (at least China) does not have a "next page" button
        form = form[0]
        form_vqd = eval_xpath(form, '//input[@name="vqd"]/@value')[0]

        cache_vqd(resp.search_params['data']['q'], resp.search_params['data']['kl'], form_vqd)

    # just select "web-result" and ignore results of class "result--ad result--ad--small"
    for div_result in eval_xpath(doc, '//div[@id="links"]/div[contains(@class, "web-result")]'):

        item = {}
        title = eval_xpath(div_result, './/h2/a')
        if not title:
            # this is the "No results." item in the result list
            continue
        item["title"] = extract_text(title)
        item["url"] = eval_xpath(div_result, './/h2/a/@href')[0]
        item["content"] = extract_text(eval_xpath(div_result, './/a[contains(@class, "result__snippet")]')[0])

        results.append(item)

    zero_click_info_xpath = '//div[@id="zero_click_abstract"]'
    zero_click = extract_text(eval_xpath(doc, zero_click_info_xpath)).strip()  # type: ignore

    if zero_click and (
        "Your IP address is" not in zero_click
        and "Your user agent:" not in zero_click
        and "URL Decoded:" not in zero_click
    ):
        results.add(
            results.types.Answer(
                answer=zero_click,
                url=extract_text(eval_xpath(doc, '//div[@id="zero_click_abstract"]/a/@href')),
            )
        )

    return results


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages & regions from DuckDuckGo.

    SearXNG's ``all`` locale maps DuckDuckGo's "Alle regions" (``wt-wt``).
    DuckDuckGo's language "Browsers preferred language" (``wt_WT``) makes no
    sense in a SearXNG request since SearXNG's ``all`` will not add a
    ``Accept-Language`` HTTP header.  The value in ``engine_traits.all_locale``
    is ``wt-wt`` (the region).

    Beside regions DuckDuckGo also defines its languages by region codes.  By
    example these are the english languages in DuckDuckGo:

    - en_US
    - en_AU
    - en_CA
    - en_GB

    The function :py:obj:`get_ddg_lang` evaluates DuckDuckGo's language from
    SearXNG's locale.

    """
    # pylint: disable=too-many-branches, too-many-statements, disable=import-outside-toplevel
    from searx.utils import js_variable_to_python

    # fetch regions

    engine_traits.all_locale = 'wt-wt'

    # updated from u661.js to u.7669f071a13a7daa57cb / should be updated automatically?
    resp = get('https://duckduckgo.com/dist/util/u.7669f071a13a7daa57cb.js')

    if not resp.ok:  # type: ignore
        print("ERROR: response from DuckDuckGo is not OK.")

    js_code = extr(resp.text, 'regions:', ',snippetLengths')  # type: ignore

    regions = json.loads(js_code)
    for eng_tag, name in regions.items():

        if eng_tag == 'wt-wt':
            engine_traits.all_locale = 'wt-wt'
            continue

        region = ddg_reg_map.get(eng_tag)
        if region == 'skip':
            continue

        if not region:
            eng_territory, eng_lang = eng_tag.split('-')
            region = eng_lang + '_' + eng_territory.upper()

        try:
            sxng_tag = locales.region_tag(babel.Locale.parse(region))
        except babel.UnknownLocaleError:
            print("ERROR: %s (%s) -> %s is unknown by babel" % (name, eng_tag, region))
            continue

        conflict = engine_traits.regions.get(sxng_tag)
        if conflict:
            if conflict != eng_tag:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, eng_tag))
            continue
        engine_traits.regions[sxng_tag] = eng_tag

    # fetch languages

    engine_traits.custom['lang_region'] = {}

    js_code = extr(resp.text, 'languages:', ',regions')  # type: ignore

    languages = js_variable_to_python(js_code)
    for eng_lang, name in languages.items():

        if eng_lang == 'wt_WT':
            continue

        babel_tag = ddg_lang_map.get(eng_lang, eng_lang)
        if babel_tag == 'skip':
            continue

        try:

            if babel_tag == 'lang_region':
                sxng_tag = locales.region_tag(babel.Locale.parse(eng_lang))
                engine_traits.custom['lang_region'][sxng_tag] = eng_lang
                continue

            sxng_tag = locales.language_tag(babel.Locale.parse(babel_tag))

        except babel.UnknownLocaleError:
            print("ERROR: language %s (%s) is unknown by babel" % (name, eng_lang))
            continue

        conflict = engine_traits.languages.get(sxng_tag)
        if conflict:
            if conflict != eng_lang:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, eng_lang))
            continue
        engine_traits.languages[sxng_tag] = eng_lang
