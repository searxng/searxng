# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
Dailymotion (Videos)
~~~~~~~~~~~~~~~~~~~~

.. _REST GET: https://developers.dailymotion.com/tools/
.. _Global API Parameters: https://developers.dailymotion.com/api/#global-parameters
.. _Video filters API: https://developers.dailymotion.com/api/#video-filters
.. _Fields selection: https://developers.dailymotion.com/api/#fields-selection

"""

from typing import TYPE_CHECKING

from datetime import datetime, timedelta
from urllib.parse import urlencode
import time
import babel

from searx.network import get, raise_for_httperror  # see https://github.com/searxng/searxng/issues/762
from searx.utils import html_to_text
from searx.exceptions import SearxEngineAPIException
from searx.locales import region_tag, language_tag
from searx.enginelib.traits import EngineTraits

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

traits: EngineTraits

# about
about = {
    "website": 'https://www.dailymotion.com',
    "wikidata_id": 'Q769222',
    "official_api_documentation": 'https://www.dailymotion.com/developer',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['videos']
paging = True
number_of_results = 10

time_range_support = True
time_delta_dict = {
    "day": timedelta(days=1),
    "week": timedelta(days=7),
    "month": timedelta(days=31),
    "year": timedelta(days=365),
}

safesearch = True
safesearch_params = {
    2: {'is_created_for_kids': 'true'},
    1: {'is_created_for_kids': 'true'},
    0: {},
}
"""True if this video is "Created for Kids" / intends to target an audience
under the age of 16 (``is_created_for_kids`` in `Video filters API`_ )
"""

family_filter_map = {
    2: 'true',
    1: 'true',
    0: 'false',
}
"""By default, the family filter is turned on. Setting this parameter to
``false`` will stop filtering-out explicit content from searches and global
contexts (``family_filter`` in `Global API Parameters`_ ).
"""

result_fields = [
    'allow_embed',
    'description',
    'title',
    'created_time',
    'duration',
    'url',
    'thumbnail_360_url',
    'id',
]
"""`Fields selection`_, by default, a few fields are returned. To request more
specific fields, the ``fields`` parameter is used with the list of fields
SearXNG needs in the response to build a video result list.
"""

search_url = 'https://api.dailymotion.com/videos?'
"""URL to retrieve a list of videos.

- `REST GET`_
- `Global API Parameters`_
- `Video filters API`_
"""

iframe_src = "https://www.dailymotion.com/embed/video/{video_id}"
"""URL template to embed video in SearXNG's result list."""


def request(query, params):

    if not query:
        return False

    eng_region: str = traits.get_region(params['searxng_locale'], 'en_US')  # type: ignore
    eng_lang = traits.get_language(params['searxng_locale'], 'en')

    args = {
        'search': query,
        'family_filter': family_filter_map.get(params['safesearch'], 'false'),
        'thumbnail_ratio': 'original',  # original|widescreen|square
        # https://developers.dailymotion.com/api/#video-filters
        'languages': eng_lang,
        'page': params['pageno'],
        'password_protected': 'false',
        'private': 'false',
        'sort': 'relevance',
        'limit': number_of_results,
        'fields': ','.join(result_fields),
    }

    args.update(safesearch_params.get(params['safesearch'], {}))

    # Don't add localization and country arguments if the user does select a
    # language (:de, :en, ..)

    if len(params['searxng_locale'].split('-')) > 1:
        # https://developers.dailymotion.com/api/#global-parameters
        args['localization'] = eng_region
        args['country'] = eng_region.split('_')[1]
        # Insufficient rights for the `ams_country' parameter of route `GET /videos'
        # 'ams_country': eng_region.split('_')[1],

    time_delta = time_delta_dict.get(params["time_range"])
    if time_delta:
        created_after = datetime.now() - time_delta
        args['created_after'] = datetime.timestamp(created_after)

    query_str = urlencode(args)
    params['url'] = search_url + query_str

    return params


# get response from search-request
def response(resp):
    results = []

    search_res = resp.json()

    # check for an API error
    if 'error' in search_res:
        raise SearxEngineAPIException(search_res['error'].get('message'))

    raise_for_httperror(resp)

    # parse results
    for res in search_res.get('list', []):

        title = res['title']
        url = res['url']

        content = html_to_text(res['description'])
        if len(content) > 300:
            content = content[:300] + '...'

        publishedDate = datetime.fromtimestamp(res['created_time'], None)

        length = time.gmtime(res.get('duration'))
        if length.tm_hour:
            length = time.strftime("%H:%M:%S", length)
        else:
            length = time.strftime("%M:%S", length)

        thumbnail = res['thumbnail_360_url']
        thumbnail = thumbnail.replace("http://", "https://")

        item = {
            'template': 'videos.html',
            'url': url,
            'title': title,
            'content': content,
            'publishedDate': publishedDate,
            'length': length,
            'thumbnail': thumbnail,
        }

        # HINT: no mater what the value is, without API token videos can't shown
        # embedded
        if res['allow_embed']:
            item['iframe_src'] = iframe_src.format(video_id=res['id'])

        results.append(item)

    # return results
    return results


def fetch_traits(engine_traits: EngineTraits):
    """Fetch locales & languages from dailymotion.

    Locales fetched from `api/locales <https://api.dailymotion.com/locales>`_.
    There are duplications in the locale codes returned from Dailymotion which
    can be ignored::

      en_EN --> en_GB, en_US
      ar_AA --> ar_EG, ar_AE, ar_SA

    The language list `api/languages <https://api.dailymotion.com/languages>`_
    contains over 7000 *languages* codes (see PR1071_).  We use only those
    language codes that are used in the locales.

    .. _PR1071: https://github.com/searxng/searxng/pull/1071

    """

    resp = get('https://api.dailymotion.com/locales')
    if not resp.ok:  # type: ignore
        print("ERROR: response from dailymotion/locales is not OK.")

    for item in resp.json()['list']:  # type: ignore
        eng_tag = item['locale']
        if eng_tag in ('en_EN', 'ar_AA'):
            continue
        try:
            sxng_tag = region_tag(babel.Locale.parse(eng_tag))
        except babel.UnknownLocaleError:
            print("ERROR: item unknown --> %s" % item)
            continue

        conflict = engine_traits.regions.get(sxng_tag)
        if conflict:
            if conflict != eng_tag:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, eng_tag))
            continue
        engine_traits.regions[sxng_tag] = eng_tag

    locale_lang_list = [x.split('_')[0] for x in engine_traits.regions.values()]

    resp = get('https://api.dailymotion.com/languages')
    if not resp.ok:  # type: ignore
        print("ERROR: response from dailymotion/languages is not OK.")

    for item in resp.json()['list']:  # type: ignore
        eng_tag = item['code']
        if eng_tag in locale_lang_list:
            sxng_tag = language_tag(babel.Locale.parse(eng_tag))
            engine_traits.languages[sxng_tag] = eng_tag
