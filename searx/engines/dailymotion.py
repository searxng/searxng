# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Dailymotion (Videos)
"""

from json import loads
from datetime import datetime
from urllib.parse import urlencode
from searx.utils import match_language, html_to_text

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

# search-url
# see http://www.dailymotion.com/doc/api/obj-video.html
search_url = 'https://api.dailymotion.com/videos?fields=created_time,title,description,duration,url,thumbnail_360_url,id&sort=relevance&limit=5&page={pageno}&{query}'  # noqa
supported_languages_url = 'https://api.dailymotion.com/languages'


# do search-request
def request(query, params):
    if params['language'] == 'all':
        locale = 'en-US'
    else:
        locale = match_language(params['language'], supported_languages)

    params['url'] = search_url.format(
        query=urlencode({'search': query, 'localization': locale}), pageno=params['pageno']
    )

    return params


# get response from search-request
def response(resp):
    results = []

    search_res = loads(resp.text)

    # return empty array if there are no results
    if 'list' not in search_res:
        return []

    # parse results
    for res in search_res['list']:
        title = res['title']
        url = res['url']
        content = html_to_text(res['description'])
        thumbnail = res['thumbnail_360_url']
        publishedDate = datetime.fromtimestamp(res['created_time'], None)

        # http to https
        thumbnail = thumbnail.replace("http://", "https://")

        results.append(
            {
                'template': 'videos.html',
                'url': url,
                'title': title,
                'content': content,
                'publishedDate': publishedDate,
                'iframe_src': "https://www.dailymotion.com/embed/video/" + res['id'],
                'thumbnail': thumbnail,
            }
        )

    # return results
    return results


# get supported languages from their site
def _fetch_supported_languages(resp):
    supported_languages = {}

    response_json = loads(resp.text)

    for language in response_json['list']:
        supported_languages[language['code']] = {}

        name = language['native_name']
        if name:
            supported_languages[language['code']]['name'] = name
        english_name = language['name']
        if english_name:
            supported_languages[language['code']]['english_name'] = english_name

    return supported_languages
