# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Apple Maps"""

from json import loads
from time import time
from urllib.parse import urlencode

from searx.network import get as http_get
from searx.engines.openstreetmap import get_key_label

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


def request(query, params):
    if time() - (token['last_updated'] or 0) > 1800:
        obtain_token()

    params['url'] = search_url.format(query=urlencode({'q': query, 'lang': params['language']}))

    params['headers'] = {'Authorization': 'Bearer ' + token['value']}

    return params


def response(resp):
    results = []

    resp_json = loads(resp.text)

    user_language = resp.search_params['language']

    for result in resp_json['results']:
        boundingbox = None
        if 'displayMapRegion' in result:
            box = result['displayMapRegion']
            boundingbox = [box['southLat'], box['northLat'], box['westLng'], box['eastLng']]

        links = []
        if 'telephone' in result:
            telephone = result['telephone']
            links.append(
                {
                    'label': get_key_label('phone', user_language),
                    'url': 'tel:' + telephone,
                    'url_label': telephone,
                }
            )
        if result.get('urls'):
            url = result['urls'][0]
            links.append(
                {
                    'label': get_key_label('website', user_language),
                    'url': url,
                    'url_label': url,
                }
            )

        results.append(
            {
                'template': 'map.html',
                'type': result.get('poiCategory'),
                'title': result['name'],
                'links': links,
                'latitude': result['center']['lat'],
                'longitude': result['center']['lng'],
                'url': result['placecardUrl'],
                'boundingbox': boundingbox,
                'geojson': {'type': 'Point', 'coordinates': [result['center']['lng'], result['center']['lat']]},
                'address': {
                    'name': result['name'],
                    'house_number': result.get('subThoroughfare'),
                    'road': result.get('thoroughfare'),
                    'locality': result.get('locality'),
                    'postcode': result.get('postCode'),
                    'country': result.get('country'),
                },
            }
        )

    return results
