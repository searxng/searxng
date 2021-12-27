# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Photon (Map)
"""

from json import loads
from urllib.parse import urlencode
from searx.utils import searx_useragent

# about
about = {
    "website": 'https://photon.komoot.io',
    "wikidata_id": None,
    "official_api_documentation": 'https://photon.komoot.io/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['map']
paging = False
number_of_results = 10

# search-url
base_url = 'https://photon.komoot.io/'
search_string = 'api/?{query}&limit={limit}'
result_base_url = 'https://openstreetmap.org/{osm_type}/{osm_id}'

# list of supported languages
supported_languages = ['de', 'en', 'fr', 'it']


# do search-request
def request(query, params):
    params['url'] = base_url + search_string.format(query=urlencode({'q': query}), limit=number_of_results)

    if params['language'] != 'all':
        language = params['language'].split('_')[0]
        if language in supported_languages:
            params['url'] = params['url'] + "&lang=" + language

    # using searx User-Agent
    params['headers']['User-Agent'] = searx_useragent()

    return params


# get response from search-request
def response(resp):
    results = []
    json = loads(resp.text)

    # parse results
    for r in json.get('features', {}):

        properties = r.get('properties')

        if not properties:
            continue

        # get title
        title = properties.get('name')

        # get osm-type
        if properties.get('osm_type') == 'N':
            osm_type = 'node'
        elif properties.get('osm_type') == 'W':
            osm_type = 'way'
        elif properties.get('osm_type') == 'R':
            osm_type = 'relation'
        else:
            # continue if invalide osm-type
            continue

        url = result_base_url.format(osm_type=osm_type, osm_id=properties.get('osm_id'))

        osm = {'type': osm_type, 'id': properties.get('osm_id')}

        geojson = r.get('geometry')

        if properties.get('extent'):
            boundingbox = [
                properties.get('extent')[3],
                properties.get('extent')[1],
                properties.get('extent')[0],
                properties.get('extent')[2],
            ]
        else:
            # TODO: better boundingbox calculation
            boundingbox = [
                geojson['coordinates'][1],
                geojson['coordinates'][1],
                geojson['coordinates'][0],
                geojson['coordinates'][0],
            ]

        # address calculation
        address = {}

        # get name
        if (
            properties.get('osm_key') == 'amenity'
            or properties.get('osm_key') == 'shop'
            or properties.get('osm_key') == 'tourism'
            or properties.get('osm_key') == 'leisure'
        ):
            address = {'name': properties.get('name')}

        # add rest of adressdata, if something is already found
        if address.get('name'):
            address.update(
                {
                    'house_number': properties.get('housenumber'),
                    'road': properties.get('street'),
                    'locality': properties.get(
                        'city', properties.get('town', properties.get('village'))  # noqa
                    ),  # noqa
                    'postcode': properties.get('postcode'),
                    'country': properties.get('country'),
                }
            )
        else:
            address = None

        # append result
        results.append(
            {
                'template': 'map.html',
                'title': title,
                'content': '',
                'longitude': geojson['coordinates'][0],
                'latitude': geojson['coordinates'][1],
                'boundingbox': boundingbox,
                'geojson': geojson,
                'address': address,
                'osm': osm,
                'url': url,
            }
        )

    # return results
    return results
