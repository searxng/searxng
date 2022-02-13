# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Youtube (Videos)
"""

from json import loads
from dateutil import parser
from urllib.parse import urlencode
from searx.exceptions import SearxEngineAPIException

# about
about = {
    "website": 'https://www.youtube.com/',
    "wikidata_id": 'Q866',
    "official_api_documentation": 'https://developers.google.com/youtube/v3/docs/search/list?apix=true',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['videos', 'music']
paging = False
api_key = None

# search-url
base_url = 'https://www.googleapis.com/youtube/v3/search'
search_url = base_url + '?part=snippet&{query}&maxResults=20&key={api_key}'
base_youtube_url = 'https://www.youtube.com/watch?v='


# do search-request
def request(query, params):
    params['url'] = search_url.format(query=urlencode({'q': query}), api_key=api_key)

    # add language tag if specified
    if params['language'] != 'all':
        params['url'] += '&relevanceLanguage=' + params['language'].split('-')[0]

    return params


# get response from search-request
def response(resp):
    results = []

    search_results = loads(resp.text)

    if 'error' in search_results and 'message' in search_results['error']:
        raise SearxEngineAPIException(search_results['error']['message'])

    # return empty array if there are no results
    if 'items' not in search_results:
        return []

    # parse results
    for result in search_results['items']:
        videoid = result['id']['videoId']

        title = result['snippet']['title']
        content = ''
        thumbnail = ''

        pubdate = result['snippet']['publishedAt']
        publishedDate = parser.parse(pubdate)

        thumbnail = result['snippet']['thumbnails']['high']['url']

        content = result['snippet']['description']

        url = base_youtube_url + videoid

        # append result
        results.append(
            {
                'url': url,
                'title': title,
                'content': content,
                'template': 'videos.html',
                'publishedDate': publishedDate,
                'iframe_src': "https://www.youtube-nocookie.com/embed/" + videoid,
                'thumbnail': thumbnail,
            }
        )

    # return results
    return results
