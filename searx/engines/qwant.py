# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Qwant (Web, News, Images, Videos)

This engine uses the Qwant API (https://api.qwant.com/v3). The API is
undocumented but can be reverse engineered by reading the network log of
https://www.qwant.com/ queries.

This implementation is used by different qwant engines in the settings.yml::

  - name: qwant
    qwant_categ: web
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

"""

from datetime import (
    datetime,
    timedelta,
)
from json import loads
from urllib.parse import urlencode
from flask_babel import gettext
import babel

from searx.exceptions import SearxEngineAPIException
from searx.network import raise_for_httperror
from searx.enginelib.traits import EngineTraits

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
qwant_categ = None  # web|news|inages|videos

safesearch = True
safe_search_map = {0: '&safesearch=0', 1: '&safesearch=1', 2: '&safesearch=2'}

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
url = 'https://api.qwant.com/v3/search/{keyword}?{query}&count={count}&offset={offset}'


def request(query, params):
    """Qwant search request"""

    if not query:
        return None

    count = 10  # web: count must be equal to 10

    if qwant_categ == 'images':
        count = 50
        offset = (params['pageno'] - 1) * count
        # count + offset must be lower than 250
        offset = min(offset, 199)
    else:
        offset = (params['pageno'] - 1) * count
        # count + offset must be lower than 50
        offset = min(offset, 40)

    params['url'] = url.format(
        keyword=qwant_categ,
        query=urlencode({'q': query}),
        offset=offset,
        count=count,
    )

    # add quant's locale
    q_locale = traits.get_region(params["searxng_locale"], default='en_US')
    params['url'] += '&locale=' + q_locale

    # add safesearch option
    params['url'] += safe_search_map.get(params['safesearch'], '')

    params['raise_for_httperror'] = False
    return params


def response(resp):
    """Get response from Qwant's search request"""
    # pylint: disable=too-many-locals, too-many-branches, too-many-statements

    results = []

    # load JSON result
    search_results = loads(resp.text)
    data = search_results.get('data', {})

    # check for an API error
    if search_results.get('status') != 'success':
        msg = ",".join(
            data.get(
                'message',
                [
                    'unknown',
                ],
            )
        )
        raise SearxEngineAPIException('API error::' + msg)

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
