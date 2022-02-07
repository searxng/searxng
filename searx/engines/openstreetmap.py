# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""OpenStreetMap (Map)

"""

import re
from json import loads
from urllib.parse import urlencode
from functools import partial

from flask_babel import gettext

from searx.data import OSM_KEYS_TAGS, CURRENCIES
from searx.utils import searx_useragent
from searx.external_urls import get_external_url
from searx.engines.wikidata import send_wikidata_query, sparql_string_escape, get_thumbnail

# about
about = {
    "website": 'https://www.openstreetmap.org/',
    "wikidata_id": 'Q936',
    "official_api_documentation": 'http://wiki.openstreetmap.org/wiki/Nominatim',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['map']
paging = False

# search-url
base_url = 'https://nominatim.openstreetmap.org/'
search_string = 'search?{query}&polygon_geojson=1&format=jsonv2&addressdetails=1&extratags=1&dedupe=1'
result_id_url = 'https://openstreetmap.org/{osm_type}/{osm_id}'
result_lat_lon_url = 'https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom={zoom}&layers=M'

route_url = 'https://graphhopper.com/maps/?point={}&point={}&locale=en-US&vehicle=car&weighting=fastest&turn_costs=true&use_miles=false&layer=Omniscale'  # pylint: disable=line-too-long
route_re = re.compile('(?:from )?(.+) to (.+)')

wikidata_image_sparql = """
select ?item ?itemLabel ?image ?sign ?symbol ?website ?wikipediaName
where {
  hint:Query hint:optimizer "None".
  values ?item { %WIKIDATA_IDS% }
  OPTIONAL { ?item wdt:P18|wdt:P8517|wdt:P4291|wdt:P5252|wdt:P3451|wdt:P4640|wdt:P5775|wdt:P2716|wdt:P1801|wdt:P4896 ?image }
  OPTIONAL { ?item wdt:P1766|wdt:P8505|wdt:P8667 ?sign }
  OPTIONAL { ?item wdt:P41|wdt:P94|wdt:P154|wdt:P158|wdt:P2910|wdt:P4004|wdt:P5962|wdt:P8972 ?symbol }
  OPTIONAL { ?item wdt:P856 ?website }
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "%LANGUAGE%,en".
    ?item rdfs:label ?itemLabel .
  }
  OPTIONAL {
    ?wikipediaUrl schema:about ?item;
                  schema:isPartOf/wikibase:wikiGroup "wikipedia";
                  schema:name ?wikipediaName;
                  schema:inLanguage "%LANGUAGE%" .
  }
}
ORDER by ?item
"""


# key value that are link: mapping functions
# 'mapillary': P1947
# but https://github.com/kartaview/openstreetcam.org/issues/60
# but https://taginfo.openstreetmap.org/keys/kartaview ...
def value_to_https_link(value):
    http = 'http://'
    if value.startswith(http):
        value = 'https://' + value[len(http) :]
    return (value, value)


def value_to_website_link(value):
    value = value.split(';')[0]
    return (value, value)


def value_wikipedia_link(value):
    value = value.split(':', 1)
    return ('https://{0}.wikipedia.org/wiki/{1}'.format(*value), '{1} ({0})'.format(*value))


def value_with_prefix(prefix, value):
    return (prefix + value, value)


VALUE_TO_LINK = {
    'website': value_to_website_link,
    'contact:website': value_to_website_link,
    'email': partial(value_with_prefix, 'mailto:'),
    'contact:email': partial(value_with_prefix, 'mailto:'),
    'contact:phone': partial(value_with_prefix, 'tel:'),
    'phone': partial(value_with_prefix, 'tel:'),
    'fax': partial(value_with_prefix, 'fax:'),
    'contact:fax': partial(value_with_prefix, 'fax:'),
    'contact:mastodon': value_to_https_link,
    'facebook': value_to_https_link,
    'contact:facebook': value_to_https_link,
    'contact:foursquare': value_to_https_link,
    'contact:instagram': value_to_https_link,
    'contact:linkedin': value_to_https_link,
    'contact:pinterest': value_to_https_link,
    'contact:telegram': value_to_https_link,
    'contact:tripadvisor': value_to_https_link,
    'contact:twitter': value_to_https_link,
    'contact:yelp': value_to_https_link,
    'contact:youtube': value_to_https_link,
    'contact:webcam': value_to_website_link,
    'wikipedia': value_wikipedia_link,
    'wikidata': partial(value_with_prefix, 'https://wikidata.org/wiki/'),
    'brand:wikidata': partial(value_with_prefix, 'https://wikidata.org/wiki/'),
}
KEY_ORDER = [
    'cuisine',
    'organic',
    'delivery',
    'delivery:covid19',
    'opening_hours',
    'opening_hours:covid19',
    'fee',
    'payment:*',
    'currency:*',
    'outdoor_seating',
    'bench',
    'wheelchair',
    'level',
    'building:levels',
    'bin',
    'public_transport',
    'internet_access:ssid',
]
KEY_RANKS = {k: i for i, k in enumerate(KEY_ORDER)}


def request(query, params):
    """do search-request"""
    params['url'] = base_url + search_string.format(query=urlencode({'q': query}))
    params['route'] = route_re.match(query)
    params['headers']['User-Agent'] = searx_useragent()
    return params


def response(resp):
    """get response from search-request"""
    results = []
    nominatim_json = loads(resp.text)
    user_language = resp.search_params['language']

    if resp.search_params['route']:
        results.append(
            {
                'answer': gettext('Get directions'),
                'url': route_url.format(*resp.search_params['route'].groups()),
            }
        )

    fetch_wikidata(nominatim_json, user_language)

    for result in nominatim_json:
        title, address = get_title_address(result)

        # ignore result without title
        if not title:
            continue

        url, osm, geojson = get_url_osm_geojson(result)
        img_src = get_thumbnail(get_img_src(result))
        links, link_keys = get_links(result, user_language)
        data = get_data(result, user_language, link_keys)

        results.append(
            {
                'template': 'map.html',
                'title': title,
                'address': address,
                'address_label': get_key_label('addr', user_language),
                'url': url,
                'osm': osm,
                'geojson': geojson,
                'img_src': img_src,
                'links': links,
                'data': data,
                'type': get_tag_label(result.get('category'), result.get('type', ''), user_language),
                'type_icon': result.get('icon'),
                'content': '',
                'longitude': result['lon'],
                'latitude': result['lat'],
                'boundingbox': result['boundingbox'],
            }
        )

    return results


def get_wikipedia_image(raw_value):
    if not raw_value:
        return None
    return get_external_url('wikimedia_image', raw_value)


def fetch_wikidata(nominatim_json, user_langage):
    """Update nominatim_json using the result of an unique to wikidata

    For result in nominatim_json:
        If result['extratags']['wikidata'] or r['extratags']['wikidata link']:
            Set result['wikidata'] to { 'image': ..., 'image_sign':..., 'image_symbal':... }
            Set result['extratags']['wikipedia'] if not defined
            Set result['extratags']['contact:website'] if not defined
    """
    wikidata_ids = []
    wd_to_results = {}
    for result in nominatim_json:
        e = result.get("extratags")
        if e:
            # ignore brand:wikidata
            wd_id = e.get("wikidata", e.get("wikidata link"))
            if wd_id and wd_id not in wikidata_ids:
                wikidata_ids.append("wd:" + wd_id)
                wd_to_results.setdefault(wd_id, []).append(result)

    if wikidata_ids:
        user_langage = 'en' if user_langage == 'all' else user_langage
        wikidata_ids_str = " ".join(wikidata_ids)
        query = wikidata_image_sparql.replace('%WIKIDATA_IDS%', sparql_string_escape(wikidata_ids_str)).replace(
            '%LANGUAGE%', sparql_string_escape(user_langage)
        )
        wikidata_json = send_wikidata_query(query)
        for wd_result in wikidata_json.get('results', {}).get('bindings', {}):
            wd_id = wd_result['item']['value'].replace('http://www.wikidata.org/entity/', '')
            for result in wd_to_results.get(wd_id, []):
                result['wikidata'] = {
                    'itemLabel': wd_result['itemLabel']['value'],
                    'image': get_wikipedia_image(wd_result.get('image', {}).get('value')),
                    'image_sign': get_wikipedia_image(wd_result.get('sign', {}).get('value')),
                    'image_symbol': get_wikipedia_image(wd_result.get('symbol', {}).get('value')),
                }
                # overwrite wikipedia link
                wikipedia_name = wd_result.get('wikipediaName', {}).get('value')
                if wikipedia_name:
                    result['extratags']['wikipedia'] = user_langage + ':' + wikipedia_name
                # get website if not already defined
                website = wd_result.get('website', {}).get('value')
                if (
                    website
                    and not result['extratags'].get('contact:website')
                    and not result['extratags'].get('website')
                ):
                    result['extratags']['contact:website'] = website


def get_title_address(result):
    """Return title and address

    title may be None
    """
    address_raw = result.get('address')
    address_name = None
    address = {}

    # get name
    if (
        result['category'] == 'amenity'
        or result['category'] == 'shop'
        or result['category'] == 'tourism'
        or result['category'] == 'leisure'
    ):
        if address_raw.get('address29'):
            # https://github.com/osm-search/Nominatim/issues/1662
            address_name = address_raw.get('address29')
        else:
            address_name = address_raw.get(result['category'])
    elif result['type'] in address_raw:
        address_name = address_raw.get(result['type'])

    # add rest of adressdata, if something is already found
    if address_name:
        title = address_name
        address.update(
            {
                'name': address_name,
                'house_number': address_raw.get('house_number'),
                'road': address_raw.get('road'),
                'locality': address_raw.get(
                    'city', address_raw.get('town', address_raw.get('village'))  # noqa
                ),  # noqa
                'postcode': address_raw.get('postcode'),
                'country': address_raw.get('country'),
                'country_code': address_raw.get('country_code'),
            }
        )
    else:
        title = result.get('display_name')

    return title, address


def get_url_osm_geojson(result):
    """Get url, osm and geojson"""
    osm_type = result.get('osm_type', result.get('type'))
    if 'osm_id' not in result:
        # see https://github.com/osm-search/Nominatim/issues/1521
        # query example: "EC1M 5RF London"
        url = result_lat_lon_url.format(lat=result['lat'], lon=result['lon'], zoom=12)
        osm = {}
    else:
        url = result_id_url.format(osm_type=osm_type, osm_id=result['osm_id'])
        osm = {'type': osm_type, 'id': result['osm_id']}

    geojson = result.get('geojson')
    # if no geojson is found and osm_type is a node, add geojson Point
    if not geojson and osm_type == 'node':
        geojson = {'type': 'Point', 'coordinates': [result['lon'], result['lat']]}

    return url, osm, geojson


def get_img_src(result):
    """Get image URL from either wikidata or r['extratags']"""
    # wikidata
    img_src = None
    if 'wikidata' in result:
        img_src = result['wikidata']['image']
        if not img_src:
            img_src = result['wikidata']['image_symbol']
        if not img_src:
            img_src = result['wikidata']['image_sign']

    # img_src
    if not img_src and result.get('extratags', {}).get('image'):
        img_src = result['extratags']['image']
        del result['extratags']['image']
    if not img_src and result.get('extratags', {}).get('wikimedia_commons'):
        img_src = get_external_url('wikimedia_image', result['extratags']['wikimedia_commons'])
        del result['extratags']['wikimedia_commons']

    return img_src


def get_links(result, user_language):
    """Return links from result['extratags']"""
    links = []
    link_keys = set()
    for k, mapping_function in VALUE_TO_LINK.items():
        raw_value = result['extratags'].get(k)
        if raw_value:
            url, url_label = mapping_function(raw_value)
            if url.startswith('https://wikidata.org'):
                url_label = result.get('wikidata', {}).get('itemLabel') or url_label
            links.append(
                {
                    'label': get_key_label(k, user_language),
                    'url': url,
                    'url_label': url_label,
                }
            )
            link_keys.add(k)
    return links, link_keys


def get_data(result, user_language, ignore_keys):
    """Return key, value of result['extratags']

    Must be call after get_links

    Note: the values are not translated
    """
    data = []
    for k, v in result['extratags'].items():
        if k in ignore_keys:
            continue
        if get_key_rank(k) is None:
            continue
        k_label = get_key_label(k, user_language)
        if k_label:
            data.append(
                {
                    'label': k_label,
                    'key': k,
                    'value': v,
                }
            )
    data.sort(key=lambda entry: (get_key_rank(entry['key']), entry['label']))
    return data


def get_key_rank(k):
    """Get OSM key rank

    The rank defines in which order the key are displayed in the HTML result
    """
    key_rank = KEY_RANKS.get(k)
    if key_rank is None:
        # "payment:*" in KEY_ORDER matches "payment:cash", "payment:debit card", etc...
        key_rank = KEY_RANKS.get(k.split(':')[0] + ':*')
    return key_rank


def get_label(labels, lang):
    """Get label from labels in OSM_KEYS_TAGS

    in OSM_KEYS_TAGS, labels have key == '*'
    """
    tag_label = labels.get(lang.lower())
    if tag_label is None:
        # example: if 'zh-hk' is not found, check 'zh'
        tag_label = labels.get(lang.split('-')[0])
    if tag_label is None and lang != 'en':
        # example: if 'zh' is not found, check 'en'
        tag_label = labels.get('en')
    if tag_label is None and len(labels.values()) > 0:
        # example: if still not found, use the first entry
        tag_label = labels.values()[0]
    return tag_label


def get_tag_label(tag_category, tag_name, lang):
    """Get tag label from OSM_KEYS_TAGS"""
    tag_name = '' if tag_name is None else tag_name
    tag_labels = OSM_KEYS_TAGS['tags'].get(tag_category, {}).get(tag_name, {})
    return get_label(tag_labels, lang)


def get_key_label(key_name, lang):
    """Get key label from OSM_KEYS_TAGS"""
    if key_name.startswith('currency:'):
        # currency:EUR --> get the name from the CURRENCIES variable
        # see https://wiki.openstreetmap.org/wiki/Key%3Acurrency
        # and for exampe https://taginfo.openstreetmap.org/keys/currency:EUR#values
        # but there is also currency=EUR (currently not handled)
        # https://taginfo.openstreetmap.org/keys/currency#values
        currency = key_name.split(':')
        if len(currency) > 1:
            o = CURRENCIES['iso4217'].get(currency)
            if o:
                return get_label(o, lang).lower()
            return currency

    labels = OSM_KEYS_TAGS['keys']
    for k in key_name.split(':') + ['*']:
        labels = labels.get(k)
        if labels is None:
            return None
    return get_label(labels, lang)
