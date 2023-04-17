# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This module implements the Wikidata engine.  Some implementations are shared
from :ref:`wikipedia engine`.

"""
# pylint: disable=missing-class-docstring

from typing import TYPE_CHECKING
from hashlib import md5
from urllib.parse import urlencode, unquote
from json import loads

from dateutil.parser import isoparse
from babel.dates import format_datetime, format_date, format_time, get_datetime_format

from searx.data import WIKIDATA_UNITS
from searx.network import post, get
from searx.utils import searx_useragent, get_string_replaces_function
from searx.external_urls import get_external_url, get_earth_coordinates_url, area_to_osm_zoom
from searx.engines.wikipedia import (
    fetch_wikimedia_traits,
    get_wiki_params,
)
from searx.enginelib.traits import EngineTraits

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

traits: EngineTraits

# about
about = {
    "website": 'https://wikidata.org/',
    "wikidata_id": 'Q2013',
    "official_api_documentation": 'https://query.wikidata.org/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# SPARQL
SPARQL_ENDPOINT_URL = 'https://query.wikidata.org/sparql'
SPARQL_EXPLAIN_URL = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql?explain'
WIKIDATA_PROPERTIES = {
    'P434': 'MusicBrainz',
    'P435': 'MusicBrainz',
    'P436': 'MusicBrainz',
    'P966': 'MusicBrainz',
    'P345': 'IMDb',
    'P2397': 'YouTube',
    'P1651': 'YouTube',
    'P2002': 'Twitter',
    'P2013': 'Facebook',
    'P2003': 'Instagram',
}

# SERVICE wikibase:mwapi : https://www.mediawiki.org/wiki/Wikidata_Query_Service/User_Manual/MWAPI
# SERVICE wikibase:label: https://en.wikibooks.org/wiki/SPARQL/SERVICE_-_Label#Manual_Label_SERVICE
# https://en.wikibooks.org/wiki/SPARQL/WIKIDATA_Precision,_Units_and_Coordinates
# https://www.mediawiki.org/wiki/Wikibase/Indexing/RDF_Dump_Format#Data_model
# optimization:
# * https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/query_optimization
# * https://github.com/blazegraph/database/wiki/QueryHints
QUERY_TEMPLATE = """
SELECT ?item ?itemLabel ?itemDescription ?lat ?long %SELECT%
WHERE
{
  SERVICE wikibase:mwapi {
        bd:serviceParam wikibase:endpoint "www.wikidata.org";
        wikibase:api "EntitySearch";
        wikibase:limit 1;
        mwapi:search "%QUERY%";
        mwapi:language "%LANGUAGE%".
        ?item wikibase:apiOutputItem mwapi:item.
  }
  hint:Prior hint:runFirst "true".

  %WHERE%

  SERVICE wikibase:label {
      bd:serviceParam wikibase:language "%LANGUAGE%,en".
      ?item rdfs:label ?itemLabel .
      ?item schema:description ?itemDescription .
      %WIKIBASE_LABELS%
  }

}
GROUP BY ?item ?itemLabel ?itemDescription ?lat ?long %GROUP_BY%
"""

# Get the calendar names and the property names
QUERY_PROPERTY_NAMES = """
SELECT ?item ?name
WHERE {
    {
      SELECT ?item
      WHERE { ?item wdt:P279* wd:Q12132 }
    } UNION {
      VALUES ?item { %ATTRIBUTES% }
    }
    OPTIONAL { ?item rdfs:label ?name. }
}
"""

# see the property "dummy value" of https://www.wikidata.org/wiki/Q2013 (Wikidata)
# hard coded here to avoid to an additional SPARQL request when the server starts
DUMMY_ENTITY_URLS = set(
    "http://www.wikidata.org/entity/" + wid for wid in ("Q4115189", "Q13406268", "Q15397819", "Q17339402")
)


# https://www.w3.org/TR/sparql11-query/#rSTRING_LITERAL1
# https://lists.w3.org/Archives/Public/public-rdf-dawg/2011OctDec/0175.html
sparql_string_escape = get_string_replaces_function(
    # fmt: off
    {
        '\t': '\\\t',
        '\n': '\\\n',
        '\r': '\\\r',
        '\b': '\\\b',
        '\f': '\\\f',
        '\"': '\\\"',
        '\'': '\\\'',
        '\\': '\\\\'
    }
    # fmt: on
)

replace_http_by_https = get_string_replaces_function({'http:': 'https:'})


def get_headers():
    # user agent: https://www.mediawiki.org/wiki/Wikidata_Query_Service/User_Manual#Query_limits
    return {'Accept': 'application/sparql-results+json', 'User-Agent': searx_useragent()}


def get_label_for_entity(entity_id, language):
    name = WIKIDATA_PROPERTIES.get(entity_id)
    if name is None:
        name = WIKIDATA_PROPERTIES.get((entity_id, language))
    if name is None:
        name = WIKIDATA_PROPERTIES.get((entity_id, language.split('-')[0]))
    if name is None:
        name = WIKIDATA_PROPERTIES.get((entity_id, 'en'))
    if name is None:
        name = entity_id
    return name


def send_wikidata_query(query, method='GET'):
    if method == 'GET':
        # query will be cached by wikidata
        http_response = get(SPARQL_ENDPOINT_URL + '?' + urlencode({'query': query}), headers=get_headers())
    else:
        # query won't be cached by wikidata
        http_response = post(SPARQL_ENDPOINT_URL, data={'query': query}, headers=get_headers())
    if http_response.status_code != 200:
        logger.debug('SPARQL endpoint error %s', http_response.content.decode())
    logger.debug('request time %s', str(http_response.elapsed))
    http_response.raise_for_status()
    return loads(http_response.content.decode())


def request(query, params):

    eng_tag, _wiki_netloc = get_wiki_params(params['searxng_locale'], traits)
    query, attributes = get_query(query, eng_tag)
    logger.debug("request --> language %s // len(attributes): %s", eng_tag, len(attributes))

    params['method'] = 'POST'
    params['url'] = SPARQL_ENDPOINT_URL
    params['data'] = {'query': query}
    params['headers'] = get_headers()
    params['language'] = eng_tag
    params['attributes'] = attributes

    return params


def response(resp):

    results = []
    jsonresponse = loads(resp.content.decode())

    language = resp.search_params['language']
    attributes = resp.search_params['attributes']
    logger.debug("request --> language %s // len(attributes): %s", language, len(attributes))

    seen_entities = set()
    for result in jsonresponse.get('results', {}).get('bindings', []):
        attribute_result = {key: value['value'] for key, value in result.items()}
        entity_url = attribute_result['item']
        if entity_url not in seen_entities and entity_url not in DUMMY_ENTITY_URLS:
            seen_entities.add(entity_url)
            results += get_results(attribute_result, attributes, language)
        else:
            logger.debug('The SPARQL request returns duplicate entities: %s', str(attribute_result))

    return results


_IMG_SRC_DEFAULT_URL_PREFIX = "https://commons.wikimedia.org/wiki/Special:FilePath/"
_IMG_SRC_NEW_URL_PREFIX = "https://upload.wikimedia.org/wikipedia/commons/thumb/"


def get_thumbnail(img_src):
    """Get Thumbnail image from wikimedia commons

    Images from commons.wikimedia.org are (HTTP) redirected to
    upload.wikimedia.org.  The redirected URL can be calculated by this
    function.

    - https://stackoverflow.com/a/33691240

    """
    logger.debug('get_thumbnail(): %s', img_src)
    if not img_src is None and _IMG_SRC_DEFAULT_URL_PREFIX in img_src.split()[0]:
        img_src_name = unquote(img_src.replace(_IMG_SRC_DEFAULT_URL_PREFIX, "").split("?", 1)[0].replace("%20", "_"))
        img_src_name_first = img_src_name
        img_src_name_second = img_src_name

        if ".svg" in img_src_name.split()[0]:
            img_src_name_second = img_src_name + ".png"

        img_src_size = img_src.replace(_IMG_SRC_DEFAULT_URL_PREFIX, "").split("?", 1)[1]
        img_src_size = img_src_size[img_src_size.index("=") + 1 : img_src_size.index("&")]
        img_src_name_md5 = md5(img_src_name.encode("utf-8")).hexdigest()
        img_src = (
            _IMG_SRC_NEW_URL_PREFIX
            + img_src_name_md5[0]
            + "/"
            + img_src_name_md5[0:2]
            + "/"
            + img_src_name_first
            + "/"
            + img_src_size
            + "px-"
            + img_src_name_second
        )
        logger.debug('get_thumbnail() redirected: %s', img_src)

    return img_src


def get_results(attribute_result, attributes, language):
    # pylint: disable=too-many-branches
    results = []
    infobox_title = attribute_result.get('itemLabel')
    infobox_id = attribute_result['item']
    infobox_id_lang = None
    infobox_urls = []
    infobox_attributes = []
    infobox_content = attribute_result.get('itemDescription', [])
    img_src = None
    img_src_priority = 0

    for attribute in attributes:
        value = attribute.get_str(attribute_result, language)
        if value is not None and value != '':
            attribute_type = type(attribute)

            if attribute_type in (WDURLAttribute, WDArticle):
                # get_select() method : there is group_concat(distinct ...;separator=", ")
                # split the value here
                for url in value.split(', '):
                    infobox_urls.append({'title': attribute.get_label(language), 'url': url, **attribute.kwargs})
                    # "normal" results (not infobox) include official website and Wikipedia links.
                    if attribute.kwargs.get('official') or attribute_type == WDArticle:
                        results.append({'title': infobox_title, 'url': url, "content": infobox_content})
                    # update the infobox_id with the wikipedia URL
                    # first the local wikipedia URL, and as fallback the english wikipedia URL
                    if attribute_type == WDArticle and (
                        (attribute.language == 'en' and infobox_id_lang is None) or attribute.language != 'en'
                    ):
                        infobox_id_lang = attribute.language
                        infobox_id = url
            elif attribute_type == WDImageAttribute:
                # this attribute is an image.
                # replace the current image only the priority is lower
                # (the infobox contain only one image).
                if attribute.priority > img_src_priority:
                    img_src = get_thumbnail(value)
                    img_src_priority = attribute.priority
            elif attribute_type == WDGeoAttribute:
                # geocoordinate link
                # use the area to get the OSM zoom
                # Note: ignre the unit (must be km² otherwise the calculation is wrong)
                # Should use normalized value p:P2046/psn:P2046/wikibase:quantityAmount
                area = attribute_result.get('P2046')
                osm_zoom = area_to_osm_zoom(area) if area else 19
                url = attribute.get_geo_url(attribute_result, osm_zoom=osm_zoom)
                if url:
                    infobox_urls.append({'title': attribute.get_label(language), 'url': url, 'entity': attribute.name})
            else:
                infobox_attributes.append(
                    {'label': attribute.get_label(language), 'value': value, 'entity': attribute.name}
                )

    if infobox_id:
        infobox_id = replace_http_by_https(infobox_id)

    # add the wikidata URL at the end
    infobox_urls.append({'title': 'Wikidata', 'url': attribute_result['item']})

    if img_src is None and len(infobox_attributes) == 0 and len(infobox_urls) == 1 and len(infobox_content) == 0:
        results.append({'url': infobox_urls[0]['url'], 'title': infobox_title, 'content': infobox_content})
    else:
        results.append(
            {
                'infobox': infobox_title,
                'id': infobox_id,
                'content': infobox_content,
                'img_src': img_src,
                'urls': infobox_urls,
                'attributes': infobox_attributes,
            }
        )
    return results


def get_query(query, language):
    attributes = get_attributes(language)
    select = [a.get_select() for a in attributes]
    where = list(filter(lambda s: len(s) > 0, [a.get_where() for a in attributes]))
    wikibase_label = list(filter(lambda s: len(s) > 0, [a.get_wikibase_label() for a in attributes]))
    group_by = list(filter(lambda s: len(s) > 0, [a.get_group_by() for a in attributes]))
    query = (
        QUERY_TEMPLATE.replace('%QUERY%', sparql_string_escape(query))
        .replace('%SELECT%', ' '.join(select))
        .replace('%WHERE%', '\n  '.join(where))
        .replace('%WIKIBASE_LABELS%', '\n      '.join(wikibase_label))
        .replace('%GROUP_BY%', ' '.join(group_by))
        .replace('%LANGUAGE%', language)
    )
    return query, attributes


def get_attributes(language):
    # pylint: disable=too-many-statements
    attributes = []

    def add_value(name):
        attributes.append(WDAttribute(name))

    def add_amount(name):
        attributes.append(WDAmountAttribute(name))

    def add_label(name):
        attributes.append(WDLabelAttribute(name))

    def add_url(name, url_id=None, **kwargs):
        attributes.append(WDURLAttribute(name, url_id, kwargs))

    def add_image(name, url_id=None, priority=1):
        attributes.append(WDImageAttribute(name, url_id, priority))

    def add_date(name):
        attributes.append(WDDateAttribute(name))

    # Dates
    for p in [
        'P571',  # inception date
        'P576',  # dissolution date
        'P580',  # start date
        'P582',  # end date
        'P569',  # date of birth
        'P570',  # date of death
        'P619',  # date of spacecraft launch
        'P620',
    ]:  # date of spacecraft landing
        add_date(p)

    for p in [
        'P27',  # country of citizenship
        'P495',  # country of origin
        'P17',  # country
        'P159',
    ]:  # headquarters location
        add_label(p)

    # Places
    for p in [
        'P36',  # capital
        'P35',  # head of state
        'P6',  # head of government
        'P122',  # basic form of government
        'P37',
    ]:  # official language
        add_label(p)

    add_value('P1082')  # population
    add_amount('P2046')  # area
    add_amount('P281')  # postal code
    add_label('P38')  # currency
    add_amount('P2048')  # height (building)

    # Media
    for p in [
        'P400',  # platform (videogames, computing)
        'P50',  # author
        'P170',  # creator
        'P57',  # director
        'P175',  # performer
        'P178',  # developer
        'P162',  # producer
        'P176',  # manufacturer
        'P58',  # screenwriter
        'P272',  # production company
        'P264',  # record label
        'P123',  # publisher
        'P449',  # original network
        'P750',  # distributed by
        'P86',
    ]:  # composer
        add_label(p)

    add_date('P577')  # publication date
    add_label('P136')  # genre (music, film, artistic...)
    add_label('P364')  # original language
    add_value('P212')  # ISBN-13
    add_value('P957')  # ISBN-10
    add_label('P275')  # copyright license
    add_label('P277')  # programming language
    add_value('P348')  # version
    add_label('P840')  # narrative location

    # Languages
    add_value('P1098')  # number of speakers
    add_label('P282')  # writing system
    add_label('P1018')  # language regulatory body
    add_value('P218')  # language code (ISO 639-1)

    # Other
    add_label('P169')  # ceo
    add_label('P112')  # founded by
    add_label('P1454')  # legal form (company, organization)
    add_label('P137')  # operator (service, facility, ...)
    add_label('P1029')  # crew members (tripulation)
    add_label('P225')  # taxon name
    add_value('P274')  # chemical formula
    add_label('P1346')  # winner (sports, contests, ...)
    add_value('P1120')  # number of deaths
    add_value('P498')  # currency code (ISO 4217)

    # URL
    add_url('P856', official=True)  # official website
    attributes.append(WDArticle(language))  # wikipedia (user language)
    if not language.startswith('en'):
        attributes.append(WDArticle('en'))  # wikipedia (english)

    add_url('P1324')  # source code repository
    add_url('P1581')  # blog
    add_url('P434', url_id='musicbrainz_artist')
    add_url('P435', url_id='musicbrainz_work')
    add_url('P436', url_id='musicbrainz_release_group')
    add_url('P966', url_id='musicbrainz_label')
    add_url('P345', url_id='imdb_id')
    add_url('P2397', url_id='youtube_channel')
    add_url('P1651', url_id='youtube_video')
    add_url('P2002', url_id='twitter_profile')
    add_url('P2013', url_id='facebook_profile')
    add_url('P2003', url_id='instagram_profile')

    # Map
    attributes.append(WDGeoAttribute('P625'))

    # Image
    add_image('P15', priority=1, url_id='wikimedia_image')  # route map
    add_image('P242', priority=2, url_id='wikimedia_image')  # locator map
    add_image('P154', priority=3, url_id='wikimedia_image')  # logo
    add_image('P18', priority=4, url_id='wikimedia_image')  # image
    add_image('P41', priority=5, url_id='wikimedia_image')  # flag
    add_image('P2716', priority=6, url_id='wikimedia_image')  # collage
    add_image('P2910', priority=7, url_id='wikimedia_image')  # icon

    return attributes


class WDAttribute:
    __slots__ = ('name',)

    def __init__(self, name):
        self.name = name

    def get_select(self):
        return '(group_concat(distinct ?{name};separator=", ") as ?{name}s)'.replace('{name}', self.name)

    def get_label(self, language):
        return get_label_for_entity(self.name, language)

    def get_where(self):
        return "OPTIONAL { ?item wdt:{name} ?{name} . }".replace('{name}', self.name)

    def get_wikibase_label(self):
        return ""

    def get_group_by(self):
        return ""

    def get_str(self, result, language):  # pylint: disable=unused-argument
        return result.get(self.name + 's')

    def __repr__(self):
        return '<' + str(type(self).__name__) + ':' + self.name + '>'


class WDAmountAttribute(WDAttribute):
    def get_select(self):
        return '?{name} ?{name}Unit'.replace('{name}', self.name)

    def get_where(self):
        return """  OPTIONAL { ?item p:{name} ?{name}Node .
    ?{name}Node rdf:type wikibase:BestRank ; ps:{name} ?{name} .
    OPTIONAL { ?{name}Node psv:{name}/wikibase:quantityUnit ?{name}Unit. } }""".replace(
            '{name}', self.name
        )

    def get_group_by(self):
        return self.get_select()

    def get_str(self, result, language):
        value = result.get(self.name)
        unit = result.get(self.name + "Unit")
        if unit is not None:
            unit = unit.replace('http://www.wikidata.org/entity/', '')
            return value + " " + get_label_for_entity(unit, language)
        return value


class WDArticle(WDAttribute):

    __slots__ = 'language', 'kwargs'

    def __init__(self, language, kwargs=None):
        super().__init__('wikipedia')
        self.language = language
        self.kwargs = kwargs or {}

    def get_label(self, language):
        # language parameter is ignored
        return "Wikipedia ({language})".replace('{language}', self.language)

    def get_select(self):
        return "?article{language} ?articleName{language}".replace('{language}', self.language)

    def get_where(self):
        return """OPTIONAL { ?article{language} schema:about ?item ;
             schema:inLanguage "{language}" ;
             schema:isPartOf <https://{language}.wikipedia.org/> ;
             schema:name ?articleName{language} . }""".replace(
            '{language}', self.language
        )

    def get_group_by(self):
        return self.get_select()

    def get_str(self, result, language):
        key = 'article{language}'.replace('{language}', self.language)
        return result.get(key)


class WDLabelAttribute(WDAttribute):
    def get_select(self):
        return '(group_concat(distinct ?{name}Label;separator=", ") as ?{name}Labels)'.replace('{name}', self.name)

    def get_where(self):
        return "OPTIONAL { ?item wdt:{name} ?{name} . }".replace('{name}', self.name)

    def get_wikibase_label(self):
        return "?{name} rdfs:label ?{name}Label .".replace('{name}', self.name)

    def get_str(self, result, language):
        return result.get(self.name + 'Labels')


class WDURLAttribute(WDAttribute):

    HTTP_WIKIMEDIA_IMAGE = 'http://commons.wikimedia.org/wiki/Special:FilePath/'

    __slots__ = 'url_id', 'kwargs'

    def __init__(self, name, url_id=None, kwargs=None):
        super().__init__(name)
        self.url_id = url_id
        self.kwargs = kwargs

    def get_str(self, result, language):
        value = result.get(self.name + 's')
        if self.url_id and value is not None and value != '':
            value = value.split(',')[0]
            url_id = self.url_id
            if value.startswith(WDURLAttribute.HTTP_WIKIMEDIA_IMAGE):
                value = value[len(WDURLAttribute.HTTP_WIKIMEDIA_IMAGE) :]
                url_id = 'wikimedia_image'
            return get_external_url(url_id, value)
        return value


class WDGeoAttribute(WDAttribute):
    def get_label(self, language):
        return "OpenStreetMap"

    def get_select(self):
        return "?{name}Lat ?{name}Long".replace('{name}', self.name)

    def get_where(self):
        return """OPTIONAL { ?item p:{name}/psv:{name} [
    wikibase:geoLatitude ?{name}Lat ;
    wikibase:geoLongitude ?{name}Long ] }""".replace(
            '{name}', self.name
        )

    def get_group_by(self):
        return self.get_select()

    def get_str(self, result, language):
        latitude = result.get(self.name + 'Lat')
        longitude = result.get(self.name + 'Long')
        if latitude and longitude:
            return latitude + ' ' + longitude
        return None

    def get_geo_url(self, result, osm_zoom=19):
        latitude = result.get(self.name + 'Lat')
        longitude = result.get(self.name + 'Long')
        if latitude and longitude:
            return get_earth_coordinates_url(latitude, longitude, osm_zoom)
        return None


class WDImageAttribute(WDURLAttribute):

    __slots__ = ('priority',)

    def __init__(self, name, url_id=None, priority=100):
        super().__init__(name, url_id)
        self.priority = priority


class WDDateAttribute(WDAttribute):
    def get_select(self):
        return '?{name} ?{name}timePrecision ?{name}timeZone ?{name}timeCalendar'.replace('{name}', self.name)

    def get_where(self):
        # To remove duplicate, add
        # FILTER NOT EXISTS { ?item p:{name}/psv:{name}/wikibase:timeValue ?{name}bis FILTER (?{name}bis < ?{name}) }
        # this filter is too slow, so the response function ignore duplicate results
        # (see the seen_entities variable)
        return """OPTIONAL { ?item p:{name}/psv:{name} [
    wikibase:timeValue ?{name} ;
    wikibase:timePrecision ?{name}timePrecision ;
    wikibase:timeTimezone ?{name}timeZone ;
    wikibase:timeCalendarModel ?{name}timeCalendar ] . }
    hint:Prior hint:rangeSafe true;""".replace(
            '{name}', self.name
        )

    def get_group_by(self):
        return self.get_select()

    def format_8(self, value, locale):  # pylint: disable=unused-argument
        # precision: less than a year
        return value

    def format_9(self, value, locale):
        year = int(value)
        # precision: year
        if year < 1584:
            if year < 0:
                return str(year - 1)
            return str(year)
        timestamp = isoparse(value)
        return format_date(timestamp, format='yyyy', locale=locale)

    def format_10(self, value, locale):
        # precision: month
        timestamp = isoparse(value)
        return format_date(timestamp, format='MMMM y', locale=locale)

    def format_11(self, value, locale):
        # precision: day
        timestamp = isoparse(value)
        return format_date(timestamp, format='full', locale=locale)

    def format_13(self, value, locale):
        timestamp = isoparse(value)
        # precision: minute
        return (
            get_datetime_format(format, locale=locale)
            .replace("'", "")
            .replace('{0}', format_time(timestamp, 'full', tzinfo=None, locale=locale))
            .replace('{1}', format_date(timestamp, 'short', locale=locale))
        )

    def format_14(self, value, locale):
        # precision: second.
        return format_datetime(isoparse(value), format='full', locale=locale)

    DATE_FORMAT = {
        '0': ('format_8', 1000000000),
        '1': ('format_8', 100000000),
        '2': ('format_8', 10000000),
        '3': ('format_8', 1000000),
        '4': ('format_8', 100000),
        '5': ('format_8', 10000),
        '6': ('format_8', 1000),
        '7': ('format_8', 100),
        '8': ('format_8', 10),
        '9': ('format_9', 1),  # year
        '10': ('format_10', 1),  # month
        '11': ('format_11', 0),  # day
        '12': ('format_13', 0),  # hour (not supported by babel, display minute)
        '13': ('format_13', 0),  # minute
        '14': ('format_14', 0),  # second
    }

    def get_str(self, result, language):
        value = result.get(self.name)
        if value == '' or value is None:
            return None
        precision = result.get(self.name + 'timePrecision')
        date_format = WDDateAttribute.DATE_FORMAT.get(precision)
        if date_format is not None:
            format_method = getattr(self, date_format[0])
            precision = date_format[1]
            try:
                if precision >= 1:
                    t = value.split('-')
                    if value.startswith('-'):
                        value = '-' + t[1]
                    else:
                        value = t[0]
                return format_method(value, language)
            except Exception:  # pylint: disable=broad-except
                return value
        return value


def debug_explain_wikidata_query(query, method='GET'):
    if method == 'GET':
        http_response = get(SPARQL_EXPLAIN_URL + '&' + urlencode({'query': query}), headers=get_headers())
    else:
        http_response = post(SPARQL_EXPLAIN_URL, data={'query': query}, headers=get_headers())
    http_response.raise_for_status()
    return http_response.content


def init(engine_settings=None):  # pylint: disable=unused-argument
    # WIKIDATA_PROPERTIES : add unit symbols
    WIKIDATA_PROPERTIES.update(WIKIDATA_UNITS)

    # WIKIDATA_PROPERTIES : add property labels
    wikidata_property_names = []
    for attribute in get_attributes('en'):
        if type(attribute) in (WDAttribute, WDAmountAttribute, WDURLAttribute, WDDateAttribute, WDLabelAttribute):
            if attribute.name not in WIKIDATA_PROPERTIES:
                wikidata_property_names.append("wd:" + attribute.name)
    query = QUERY_PROPERTY_NAMES.replace('%ATTRIBUTES%', " ".join(wikidata_property_names))
    jsonresponse = send_wikidata_query(query)
    for result in jsonresponse.get('results', {}).get('bindings', {}):
        name = result['name']['value']
        lang = result['name']['xml:lang']
        entity_id = result['item']['value'].replace('http://www.wikidata.org/entity/', '')
        WIKIDATA_PROPERTIES[(entity_id, lang)] = name.capitalize()


def fetch_traits(engine_traits: EngineTraits):
    """Uses languages evaluated from :py:obj:`wikipedia.fetch_wikimedia_traits
    <searx.engines.wikipedia.fetch_wikimedia_traits>` and removes

    - ``traits.custom['wiki_netloc']``: wikidata does not have net-locations for
      the languages and the list of all

    - ``traits.custom['WIKIPEDIA_LANGUAGES']``: not used in the wikipedia engine

    """

    fetch_wikimedia_traits(engine_traits)
    engine_traits.custom['wiki_netloc'] = {}
    engine_traits.custom['WIKIPEDIA_LANGUAGES'] = []
