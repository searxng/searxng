# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=invalid-name
"""Genius

"""

from urllib.parse import urlencode
from datetime import datetime

# about
about = {
    "website": 'https://genius.com/',
    "wikidata_id": 'Q3419343',
    "official_api_documentation": 'https://docs.genius.com/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['music', 'lyrics']
paging = True
page_size = 5

url = 'https://genius.com/api/'
search_url = url + 'search/{index}?{query}&page={pageno}&per_page={page_size}'
music_player = 'https://genius.com{api_path}/apple_music_player'


def request(query, params):
    params['url'] = search_url.format(
        query=urlencode({'q': query}),
        index='multi',
        page_size=page_size,
        pageno=params['pageno'],
    )
    return params


def parse_lyric(hit):
    content = ''
    highlights = hit['highlights']
    if highlights:
        content = hit['highlights'][0]['value']
    else:
        content = hit['result'].get('title_with_featured', '')

    timestamp = hit['result']['lyrics_updated_at']
    result = {
        'url': hit['result']['url'],
        'title': hit['result']['full_title'],
        'content': content,
        'img_src': hit['result']['song_art_image_thumbnail_url'],
    }
    if timestamp:
        result.update({'publishedDate': datetime.fromtimestamp(timestamp)})
    api_path = hit['result'].get('api_path')
    if api_path:
        # The players are just playing 30sec from the title.  Some of the player
        # will be blocked because of a cross-origin request and some players will
        # link to apple when you press the play button.
        result['iframe_src'] = music_player.format(api_path=api_path)
    return result


def parse_artist(hit):
    result = {
        'url': hit['result']['url'],
        'title': hit['result']['name'],
        'content': '',
        'img_src': hit['result']['image_url'],
    }
    return result


def parse_album(hit):
    res = hit['result']
    content = res.get('name_with_artist', res.get('name', ''))
    x = res.get('release_date_components')
    if x:
        x = x.get('year')
        if x:
            content = "%s / %s" % (x, content)
    return {
        'url': res['url'],
        'title': res['full_title'],
        'img_src': res['cover_art_url'],
        'content': content.strip(),
    }


parse = {'lyric': parse_lyric, 'song': parse_lyric, 'artist': parse_artist, 'album': parse_album}


def response(resp):
    results = []
    for section in resp.json()['response']['sections']:
        for hit in section['hits']:
            func = parse.get(hit['type'])
            if func:
                results.append(func(hit))
    return results
