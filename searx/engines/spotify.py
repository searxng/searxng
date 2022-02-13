# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Spotify (Music)
"""

from json import loads
from urllib.parse import urlencode
import base64

from searx.network import post as http_post

# about
about = {
    "website": 'https://www.spotify.com',
    "wikidata_id": 'Q689141',
    "official_api_documentation": 'https://developer.spotify.com/web-api/search-item/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['music']
paging = True
api_client_id = None
api_client_secret = None

# search-url
url = 'https://api.spotify.com/'
search_url = url + 'v1/search?{query}&type=track&offset={offset}'

# do search-request
def request(query, params):
    offset = (params['pageno'] - 1) * 20

    params['url'] = search_url.format(query=urlencode({'q': query}), offset=offset)

    r = http_post(
        'https://accounts.spotify.com/api/token',
        data={'grant_type': 'client_credentials'},
        headers={
            'Authorization': 'Basic '
            + base64.b64encode("{}:{}".format(api_client_id, api_client_secret).encode()).decode()
        },
    )
    j = loads(r.text)
    params['headers'] = {'Authorization': 'Bearer {}'.format(j.get('access_token'))}

    return params


# get response from search-request
def response(resp):
    results = []

    search_res = loads(resp.text)

    # parse results
    for result in search_res.get('tracks', {}).get('items', {}):
        if result['type'] == 'track':
            title = result['name']
            url = result['external_urls']['spotify']
            content = '{} - {} - {}'.format(result['artists'][0]['name'], result['album']['name'], result['name'])

            # append result
            results.append(
                {
                    'url': url,
                    'title': title,
                    'iframe_src': "https://embed.spotify.com/?uri=spotify:track:" + result['id'],
                    'content': content,
                }
            )

    # return results
    return results
