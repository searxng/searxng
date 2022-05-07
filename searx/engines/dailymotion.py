# SPDX-License-Identifier: AGPL-3.0-or-later
"""Dailymotion (Videos)

"""

from typing import Set
from datetime import datetime, timedelta
from urllib.parse import urlencode
import time
import babel

from searx.exceptions import SearxEngineAPIException
from searx.network import raise_for_httperror
from searx.utils import html_to_text

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
safesearch_params = {2: '&is_created_for_kids=true', 1: '&is_created_for_kids=true', 0: ''}

# search-url
# - https://developers.dailymotion.com/tools/
# - https://www.dailymotion.com/doc/api/obj-video.html

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
search_url = (
    'https://api.dailymotion.com/videos?'
    'fields={fields}&password_protected={password_protected}&private={private}&sort={sort}&limit={limit}'
).format(
    fields=','.join(result_fields),
    password_protected='false',
    private='false',
    sort='relevance',
    limit=number_of_results,
)
iframe_src = "https://www.dailymotion.com/embed/video/{video_id}"

# The request query filters by 'languages' & 'country', therefore instead of
# fetching only languages we need to fetch locales.
supported_languages_url = 'https://api.dailymotion.com/locales'
supported_languages_iso639: Set[str] = set()


def init(_engine_settings):
    global supported_languages_iso639
    supported_languages_iso639 = set([language.split('_')[0] for language in supported_languages])


def request(query, params):

    if not query:
        return False

    language = params['language']
    if language == 'all':
        language = 'en-US'
    locale = babel.Locale.parse(language, sep='-')

    language_iso639 = locale.language
    if locale.language not in supported_languages_iso639:
        language_iso639 = 'en'

    query_args = {
        'search': query,
        'languages': language_iso639,
        'page': params['pageno'],
    }

    if locale.territory:
        localization = locale.language + '_' + locale.territory
        if localization in supported_languages:
            query_args['country'] = locale.territory

    time_delta = time_delta_dict.get(params["time_range"])
    if time_delta:
        created_after = datetime.now() - time_delta
        query_args['created_after'] = datetime.timestamp(created_after)

    query_str = urlencode(query_args)
    params['url'] = search_url + '&' + query_str + safesearch_params.get(params['safesearch'], '')
    params['raise_for_httperror'] = False

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


# get supported languages from their site
def _fetch_supported_languages(resp):
    response_json = resp.json()
    return [item['locale'] for item in response_json['list']]
