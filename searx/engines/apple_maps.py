# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Apple Maps"""

from json import loads
from time import time
from urllib.parse import urlencode

from searx.network import get as http_get

about = {
    "website": 'https://www.apple.com/maps/',
    "wikidata_id": 'Q276101',
    "official_api_documentation": None,
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

token = {'value': '', 'last_updated': None}

categories = ['map']
paging = False

search_url = "https://api.apple-mapkit.com/v1/search?{query}&mkjsVersion=5.72.53"


def obtain_token():
    update_time = time() - (time() % 1800)
    try:
        # use duckduckgo's mapkit token
        token_response = http_get('https://duckduckgo.com/local.js?get_mk_token=1', timeout=2.0)
        actual_token = http_get(
            'https://cdn.apple-mapkit.com/ma/bootstrap?apiVersion=2&mkjsVersion=5.72.53&poi=1',
            timeout=2.0,
            headers={'Authorization': 'Bearer ' + token_response.text},
        )
        token['value'] = loads(actual_token.text)['authInfo']['access_token']
        token['last_updated'] = update_time
    # pylint: disable=bare-except
    except:
        pass
    return token


def init(_engine_settings=None):
    obtain_token()


def request(query, params):
    if time() - (token['last_updated'] or 0) > 1800:
        obtain_token()

    params['url'] = search_url.format(query=urlencode({'q': query, 'lang': params['language']}))

    params['headers'] = {'Authorization': 'Bearer ' + token['value']}

    return params


def response(resp):
    results = []

    resp_json = loads(resp.text)

    for result in resp_json['results']:
        box = result['displayMapRegion']

        results.append(
            {
                'template': 'map.html',
                'title': result['name'],
                'latitude': result['center']['lat'],
                'longitude': result['center']['lng'],
                'url': result['placecardUrl'],
                'boundingbox': [box['southLat'], box['northLat'], box['westLng'], box['eastLng']],
                'geojson': {'type': 'Point', 'coordinates': [result['center']['lng'], result['center']['lat']]},
                'address': {
                    'name': result['name'],
                    'house_number': result.get('subThoroughfare', {}),
                    'road': result.get('thoroughfare', {}),
                    'locality': result.get('locality', {}),
                    'postcode': result.get('postCode', {}),
                    'country': result.get('country', {}),
                },
            }
        )

    return results
