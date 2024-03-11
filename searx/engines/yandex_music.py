# SPDX-License-Identifier: AGPL-3.0-or-later
"""Yandex Music

.. _Countries where Yandex.Music is available: https://yandex.com/support/music/access.html

.. hint::

   Access to music is limited to a few countries: `Countries where Yandex.Music
   is available`_

"""

from urllib.parse import urlencode

# about
about = {
    "website": 'https://music.yandex.ru',
    "wikidata_id": 'Q4537983',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['music']
paging = True

# search-url
url = 'https://music.yandex.ru'
search_url = url + '/handlers/music-search.jsx'


# do search-request
def request(query, params):
    args = {'text': query, 'page': params['pageno'] - 1}
    params['url'] = search_url + '?' + urlencode(args)

    return params


# get response from search-request
def response(resp):
    results = []
    search_res = resp.json()

    # parse results
    for result in search_res.get('tracks', {}).get('items', []):
        if result['type'] == 'music':
            track_id = result['id']
            album_id = result['albums'][0]['id']

            # append result
            results.append(
                {
                    'url': f'{url}/album/{album_id}/track/{track_id}',
                    'title': result['title'],
                    'content': f"[{result['albums'][0]['title']}] {result['artists'][0]['name']} - {result['title']}",
                    'iframe_src': f'{url}/iframe/track/{track_id}/{album_id}',
                }
            )

    return results
