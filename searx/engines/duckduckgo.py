# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
DuckDuckGo Lite
~~~~~~~~~~~~~~~
"""

from typing import TYPE_CHECKING
import re
from urllib.parse import urlencode
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
    eval_xpath_getindex,
    extract_text,
)
from searx.network import get  # see https://github.com/searxng/searxng/issues/762
from searx import redisdb
from searx.enginelib.traits import EngineTraits
from searx.exceptions import SearxEngineAPIException

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
"""DuckDuckGo-Lite tries to guess user's prefered language from the HTTP
``Accept-Language``.  Optional the user can select a region filter (but not a
language).
"""

# engine dependent config
categories = ['general', 'web']
paging = True
time_range_support = True
safesearch = True  # user can't select but the results are filtered

url = 'https://lite.duckduckgo.com/lite/'
# url_ping = 'https://duckduckgo.com/t/sl_l'

time_range_dict = {'day': 'd', 'week': 'w', 'month': 'm', 'year': 'y'}
form_data = {'v': 'l', 'api': 'd.js', 'o': 'json'}


def cache_vqd(query, value):
    """Caches a ``vqd`` value from a query.

    The vqd value depends on the query string and is needed for the follow up
    pages or the images loaded by a XMLHttpRequest:

    - DuckDuckGo Web: `https://links.duckduckgo.com/d.js?q=...&vqd=...`
    - DuckDuckGo Images: `https://duckduckgo.com/i.js??q=...&vqd=...`

    """
    c = redisdb.client()
    if c:
        logger.debug("cache vqd value: %s", value)
        key = 'SearXNG_ddg_vqd' + redislib.secret_hash(query)
        c.set(key, value, ex=600)


def get_vqd(query, headers):
    """Returns the ``vqd`` that fits to the *query*.  If there is no ``vqd`` cached
    (:py:obj:`cache_vqd`) the query is sent to DDG to get a vqd value from the
    response.

    """
    value = None
    c = redisdb.client()
    if c:
        key = 'SearXNG_ddg_vqd' + redislib.secret_hash(query)
        value = c.get(key)
        if value:
            value = value.decode('utf-8')
            logger.debug("re-use cached vqd value: %s", value)
            return value

    query_url = 'https://duckduckgo.com/?q={query}&atb=v290-5'.format(query=urlencode({'q': query}))
    res = get(query_url, headers=headers)
    content = res.text  # type: ignore
    if content.find('vqd=\"') == -1:
        raise SearxEngineAPIException('Request failed')
    value = content[content.find('vqd=\"') + 5 :]
    value = value[: value.find('\'')]
    logger.debug("new vqd value: %s", value)
    cache_vqd(query, value)
    return value


def get_ddg_lang(eng_traits: EngineTraits, sxng_locale, default='en_US'):
    """Get DuckDuckGo's language identifier from SearXNG's locale.

    DuckDuckGo defines its lanaguages by region codes (see
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

       `DDG-lite <https://lite.duckduckgo.com/lite>`__ does not offer a language
       selection to the user, only a region can be selected by the user
       (``eng_region`` from the example above).  DDG-lite stores the selected
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


def request(query, params):

    # quote ddg bangs
    query_parts = []
    # for val in re.split(r'(\s+)', query):
    for val in re.split(r'(\s+)', query):
        if not val.strip():
            continue
        if val.startswith('!') and external_bang.get_node(external_bang.EXTERNAL_BANGS, val[1:]):
            val = f"'{val}'"
        query_parts.append(val)
    query = ' '.join(query_parts)

    eng_region = traits.get_region(params['searxng_locale'], traits.all_locale)
    # eng_lang = get_ddg_lang(traits, params['searxng_locale'])

    params['url'] = url
    params['method'] = 'POST'
    params['data']['q'] = query

    # The API is not documented, so we do some reverse engineering and emulate
    # what https://lite.duckduckgo.com/lite/ does when you press "next Page"
    # link again and again ..

    params['headers']['Content-Type'] = 'application/x-www-form-urlencoded'
    params['headers']['Referer'] = 'https://google.com/'

    # initial page does not have an offset
    if params['pageno'] == 2:
        # second page does have an offset of 30
        offset = (params['pageno'] - 1) * 30
        params['data']['s'] = offset
        params['data']['dc'] = offset + 1

    elif params['pageno'] > 2:
        # third and following pages do have an offset of 30 + n*50
        offset = 30 + (params['pageno'] - 2) * 50
        params['data']['s'] = offset
        params['data']['dc'] = offset + 1

    # request needs a vqd argument
    params['data']['vqd'] = get_vqd(query, params["headers"])

    # initial page does not have additional data in the input form
    if params['pageno'] > 1:

        params['data']['o'] = form_data.get('o', 'json')
        params['data']['api'] = form_data.get('api', 'd.js')
        params['data']['nextParams'] = form_data.get('nextParams', '')
        params['data']['v'] = form_data.get('v', 'l')

    params['data']['kl'] = eng_region
    params['cookies']['kl'] = eng_region

    params['data']['df'] = ''
    if params['time_range'] in time_range_dict:
        params['data']['df'] = time_range_dict[params['time_range']]
        params['cookies']['df'] = time_range_dict[params['time_range']]

    logger.debug("param data: %s", params['data'])
    logger.debug("param cookies: %s", params['cookies'])
    return params


def response(resp):

    if resp.status_code == 303:
        return []

    results = []
    doc = lxml.html.fromstring(resp.text)

    result_table = eval_xpath(doc, '//html/body/form/div[@class="filters"]/table')

    if len(result_table) == 2:
        # some locales (at least China) does not have a "next page" button and
        # the layout of the HTML tables is different.
        result_table = result_table[1]
    elif not len(result_table) >= 3:
        # no more results
        return []
    else:
        result_table = result_table[2]
        # update form data from response
        form = eval_xpath(doc, '//html/body/form/div[@class="filters"]/table//input/..')
        if len(form):

            form = form[0]
            form_data['v'] = eval_xpath(form, '//input[@name="v"]/@value')[0]
            form_data['api'] = eval_xpath(form, '//input[@name="api"]/@value')[0]
            form_data['o'] = eval_xpath(form, '//input[@name="o"]/@value')[0]
            logger.debug('form_data: %s', form_data)

            value = eval_xpath(form, '//input[@name="vqd"]/@value')[0]
            query = resp.search_params['data']['q']
            cache_vqd(query, value)

    tr_rows = eval_xpath(result_table, './/tr')
    # In the last <tr> is the form of the 'previous/next page' links
    tr_rows = tr_rows[:-1]

    len_tr_rows = len(tr_rows)
    offset = 0

    while len_tr_rows >= offset + 4:

        # assemble table rows we need to scrap
        tr_title = tr_rows[offset]
        tr_content = tr_rows[offset + 1]
        offset += 4

        # ignore sponsored Adds <tr class="result-sponsored">
        if tr_content.get('class') == 'result-sponsored':
            continue

        a_tag = eval_xpath_getindex(tr_title, './/td//a[@class="result-link"]', 0, None)
        if a_tag is None:
            continue

        td_content = eval_xpath_getindex(tr_content, './/td[@class="result-snippet"]', 0, None)
        if td_content is None:
            continue

        results.append(
            {
                'title': a_tag.text_content(),
                'content': extract_text(td_content),
                'url': a_tag.get('href'),
            }
        )

    return results


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages & regions from DuckDuckGo.

    SearXNG's ``all`` locale maps DuckDuckGo's "Alle regions" (``wt-wt``).
    DuckDuckGo's language "Browsers prefered language" (``wt_WT``) makes no
    sense in a SearXNG request since SearXNG's ``all`` will not add a
    ``Accept-Language`` HTTP header.  The value in ``engine_traits.all_locale``
    is ``wt-wt`` (the region).

    Beside regions DuckDuckGo also defines its lanaguages by region codes.  By
    example these are the english languages in DuckDuckGo:

    - en_US
    - en_AU
    - en_CA
    - en_GB

    The function :py:obj:`get_ddg_lang` evaluates DuckDuckGo's language from
    SearXNG's locale.

    """
    # pylint: disable=too-many-branches, too-many-statements
    # fetch regions

    engine_traits.all_locale = 'wt-wt'

    # updated from u588 to u661 / should be updated automatically?
    resp = get('https://duckduckgo.com/util/u661.js')

    if not resp.ok:  # type: ignore
        print("ERROR: response from DuckDuckGo is not OK.")

    pos = resp.text.find('regions:{') + 8  # type: ignore
    js_code = resp.text[pos:]  # type: ignore
    pos = js_code.find('}') + 1
    regions = json.loads(js_code[:pos])

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

    pos = resp.text.find('languages:{') + 10  # type: ignore
    js_code = resp.text[pos:]  # type: ignore
    pos = js_code.find('}') + 1
    js_code = '{"' + js_code[1:pos].replace(':', '":').replace(',', ',"')
    languages = json.loads(js_code)

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
