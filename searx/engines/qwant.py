# SPDX-License-Identifier: AGPL-3.0-or-later
"""This engine uses the Qwant API (https://api.qwant.com/v3) to implement Qwant
-Web, -News, -Images and -Videos.  The API is undocumented but can be reverse
engineered by reading the network log of https://www.qwant.com/ queries.

For Qwant's *web-search* two alternatives are implemented:

- ``web``: uses the :py:obj:`api_url` which returns a JSON structure
- ``web-lite``: uses the :py:obj:`web_lite_url` which returns a HTML page


Configuration
=============

The engine has the following additional settings:

- :py:obj:`qwant_categ`

This implementation is used by different qwant engines in the :ref:`settings.yml
<settings engine>`:

.. code:: yaml

  - name: qwant
    qwant_categ: web-lite  # alternatively use 'web'
    ...
  - name: qwant news
    qwant_categ: news
    ...
  - name: qwant images
    qwant_categ: images
    ...
  - name: qwant videos
    qwant_categ: videos
    ...

Implementations
===============

"""

from datetime import (
    datetime,
    timedelta,
)
from json import loads
from urllib.parse import urlencode
from flask_babel import gettext
import babel
import lxml

from searx.exceptions import SearxEngineAPIException, SearxEngineTooManyRequestsException
from searx.network import raise_for_httperror
from searx.enginelib.traits import EngineTraits

from searx.utils import (
    eval_xpath,
    eval_xpath_list,
    extract_text,
)

traits: EngineTraits

# about
about = {
    "website": 'https://www.qwant.com/',
    "wikidata_id": 'Q14657870',
    "official_api_documentation": None,
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = []
paging = True
max_page = 5
"""5 pages maximum (``&p=5``): Trying to do more just results in an improper
redirect"""

qwant_categ = None
"""One of ``web-lite`` (or ``web``), ``news``, ``images`` or ``videos``"""

safesearch = True
# safe_search_map = {0: '&safesearch=0', 1: '&safesearch=1', 2: '&safesearch=2'}

# fmt: off
qwant_news_locales = [
    'ca_ad', 'ca_es', 'ca_fr', 'co_fr', 'de_at', 'de_ch', 'de_de', 'en_au',
    'en_ca', 'en_gb', 'en_ie', 'en_my', 'en_nz', 'en_us', 'es_ad', 'es_ar',
    'es_cl', 'es_co', 'es_es', 'es_mx', 'es_pe', 'eu_es', 'eu_fr', 'fc_ca',
    'fr_ad', 'fr_be', 'fr_ca', 'fr_ch', 'fr_fr', 'it_ch', 'it_it', 'nl_be',
    'nl_nl', 'pt_ad', 'pt_pt',
]
# fmt: on

# search-url

api_url = 'https://api.qwant.com/v3/search/'
"""URL of Qwant's API (JSON)"""

web_lite_url = 'https://lite.qwant.com/'
"""URL of Qwant-Lite (HTML)"""


def request(query, params):
    """Qwant search request"""

    if not query:
        return None

    q_locale = traits.get_region(params["searxng_locale"], default='en_US')

    url = api_url + f'{qwant_categ}?'
    args = {'q': query}
    params['raise_for_httperror'] = False

    if qwant_categ == 'web-lite':

        url = web_lite_url + '?'
        args['locale'] = q_locale.lower()
        args['l'] = q_locale.split('_')[0]
        args['s'] = params['safesearch']
        args['p'] = params['pageno']

        params['raise_for_httperror'] = True

    elif qwant_categ == 'images':

        args['locale'] = q_locale
        args['safesearch'] = params['safesearch']
        args['count'] = 50
        args['offset'] = (params['pageno'] - 1) * args['count']

    else:  # web, news, videos

        args['locale'] = q_locale
        args['safesearch'] = params['safesearch']
        args['count'] = 10
        args['offset'] = (params['pageno'] - 1) * args['count']

    params['url'] = url + urlencode(args)

    return params


def response(resp):

    if qwant_categ == 'web-lite':
        return parse_web_lite(resp)
    return parse_web_api(resp)


def parse_web_lite(resp):
    """Parse results from Qwant-Lite"""

    results = []
    dom = lxml.html.fromstring(resp.text)

    for item in eval_xpath_list(dom, '//section/article'):
        if eval_xpath(item, "./span[contains(@class, 'tooltip')]"):
            # ignore randomly interspersed advertising adds
            continue
        results.append(
            {
                'url': extract_text(eval_xpath(item, "./span[contains(@class, 'url partner')]")),
                'title': extract_text(eval_xpath(item, './h2/a')),
                'content': extract_text(eval_xpath(item, './p')),
            }
        )

    return results


def parse_web_api(resp):
    """Parse results from Qwant's API"""
    # pylint: disable=too-many-locals, too-many-branches, too-many-statements

    results = []

    # load JSON result
    search_results = loads(resp.text)
    data = search_results.get('data', {})

    # check for an API error
    if search_results.get('status') != 'success':
        error_code = data.get('error_code')
        if error_code == 24:
            raise SearxEngineTooManyRequestsException()
        msg = ",".join(data.get('message', ['unknown']))
        raise SearxEngineAPIException(f"{msg} ({error_code})")

    # raise for other errors
    raise_for_httperror(resp)

    if qwant_categ == 'web':
        # The WEB query contains a list named 'mainline'.  This list can contain
        # different result types (e.g. mainline[0]['type'] returns type of the
        # result items in mainline[0]['items']
        mainline = data.get('result', {}).get('items', {}).get('mainline', {})
    else:
        # Queries on News, Images and Videos do not have a list named 'mainline'
        # in the response.  The result items are directly in the list
        # result['items'].
        mainline = data.get('result', {}).get('items', [])
        mainline = [
            {'type': qwant_categ, 'items': mainline},
        ]

    # return empty array if there are no results
    if not mainline:
        return []

    for row in mainline:
        mainline_type = row.get('type', 'web')
        if mainline_type != qwant_categ:
            continue

        if mainline_type == 'ads':
            # ignore adds
            continue

        mainline_items = row.get('items', [])
        for item in mainline_items:

            title = item.get('title', None)
            res_url = item.get('url', None)

            if mainline_type == 'web':
                content = item['desc']
                results.append(
                    {
                        'title': title,
                        'url': res_url,
                        'content': content,
                    }
                )

            elif mainline_type == 'news':

                pub_date = item['date']
                if pub_date is not None:
                    pub_date = datetime.fromtimestamp(pub_date)
                news_media = item.get('media', [])
                img_src = None
                if news_media:
                    img_src = news_media[0].get('pict', {}).get('url', None)
                results.append(
                    {
                        'title': title,
                        'url': res_url,
                        'publishedDate': pub_date,
                        'img_src': img_src,
                    }
                )

            elif mainline_type == 'images':
                thumbnail = item['thumbnail']
                img_src = item['media']
                results.append(
                    {
                        'title': title,
                        'url': res_url,
                        'template': 'images.html',
                        'thumbnail_src': thumbnail,
                        'img_src': img_src,
                        'resolution': f"{item['width']} x {item['height']}",
                        'img_format': item.get('thumb_type'),
                    }
                )

            elif mainline_type == 'videos':
                # some videos do not have a description: while qwant-video
                # returns an empty string, such video from a qwant-web query
                # miss the 'desc' key.
                d, s, c = item.get('desc'), item.get('source'), item.get('channel')
                content_parts = []
                if d:
                    content_parts.append(d)
                if s:
                    content_parts.append("%s: %s " % (gettext("Source"), s))
                if c:
                    content_parts.append("%s: %s " % (gettext("Channel"), c))
                content = ' // '.join(content_parts)
                length = item['duration']
                if length is not None:
                    length = timedelta(milliseconds=length)
                pub_date = item['date']
                if pub_date is not None:
                    pub_date = datetime.fromtimestamp(pub_date)
                thumbnail = item['thumbnail']
                # from some locations (DE and others?) the s2 link do
                # response a 'Please wait ..' but does not deliver the thumbnail
                thumbnail = thumbnail.replace('https://s2.qwant.com', 'https://s1.qwant.com', 1)
                results.append(
                    {
                        'title': title,
                        'url': res_url,
                        'content': content,
                        'publishedDate': pub_date,
                        'thumbnail': thumbnail,
                        'template': 'videos.html',
                        'length': length,
                    }
                )

    return results


def fetch_traits(engine_traits: EngineTraits):

    # pylint: disable=import-outside-toplevel
    from searx import network
    from searx.locales import region_tag

    resp = network.get(about['website'])
    text = resp.text
    text = text[text.find('INITIAL_PROPS') :]
    text = text[text.find('{') : text.find('</script>')]

    q_initial_props = loads(text)
    q_locales = q_initial_props.get('locales')
    eng_tag_list = set()

    for country, v in q_locales.items():
        for lang in v['langs']:
            _locale = "{lang}_{country}".format(lang=lang, country=country)

            if qwant_categ == 'news' and _locale.lower() not in qwant_news_locales:
                # qwant-news does not support all locales from qwant-web:
                continue

            eng_tag_list.add(_locale)

    for eng_tag in eng_tag_list:
        try:
            sxng_tag = region_tag(babel.Locale.parse(eng_tag, sep='_'))
        except babel.UnknownLocaleError:
            print("ERROR: can't determine babel locale of quant's locale %s" % eng_tag)
            continue

        conflict = engine_traits.regions.get(sxng_tag)
        if conflict:
            if conflict != eng_tag:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, eng_tag))
            continue
        engine_traits.regions[sxng_tag] = eng_tag
