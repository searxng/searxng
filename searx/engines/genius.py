# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=invalid-name
"""Genius

"""

from json import loads
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


def request(query, params):
    params['url'] = search_url.format(
        query=urlencode({'q': query}),
        index='multi',
        page_size=page_size,
        pageno=params['pageno'],
    )
    return params


def parse_lyric(hit):
    try:
        content = hit['highlights'][0]['value']
    except Exception as e:  # pylint: disable=broad-except
        logger.error(e, exc_info=True)
        content = ''
    timestamp = hit['result']['lyrics_updated_at']
    result = {
        'url': hit['result']['url'],
        'title': hit['result']['full_title'],
        'content': content,
        'thumbnail': hit['result']['song_art_image_thumbnail_url'],
    }
    if timestamp:
        result.update({'publishedDate': datetime.fromtimestamp(timestamp)})
    return result


def parse_artist(hit):
    result = {
        'url': hit['result']['url'],
        'title': hit['result']['name'],
        'content': '',
        'thumbnail': hit['result']['image_url'],
    }
    return result


def parse_album(hit):
    result = {
        'url': hit['result']['url'],
        'title': hit['result']['full_title'],
        'thumbnail': hit['result']['cover_art_url'],
        'content': '',
    }
    try:
        year = hit['result']['release_date_components']['year']
    except Exception as e:  # pylint: disable=broad-except
        logger.error(e, exc_info=True)
    else:
        if year:
            result.update({'content': 'Released: {}'.format(year)})
    return result


parse = {'lyric': parse_lyric, 'song': parse_lyric, 'artist': parse_artist, 'album': parse_album}


def response(resp):
    results = []
    json = loads(resp.text)
    hits = [hit for section in json['response']['sections'] for hit in section['hits']]
    for hit in hits:
        func = parse.get(hit['type'])
        if func:
            results.append(func(hit))
    return results
