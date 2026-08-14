# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-class-docstring
"""Fetch property names from :origin:`searx/engines/wikidata.py` engine."""

import typing as t

from dateutil.parser import isoparse
from babel.dates import format_datetime, format_date, format_time, get_datetime_format

from searx.external_urls import get_earth_coordinates_url, get_external_url
from searx.data import WikiDataPropertiesType, WikiDataUnitType
from searx.wikidata import send_wikidata_query

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


class WDAttribute:
    def __init__(self, name: str):
        self.name: str = name

    def get_select(self):
        return "(group_concat(distinct ?{name};separator=', ') as ?{name}s)".replace("{name}", self.name)

    def get_label(self, language: str):
        return get_label_for_entity(self.name, language)

    def get_where(self):
        return "OPTIONAL { ?item wdt:{name} ?{name} . }".replace("{name}", self.name)

    def get_wikibase_label(self) -> str:
        return ""

    def get_group_by(self) -> str:
        return ""

    def get_str(self, result: dict[str, t.Any], language: str) -> str | None:  # pylint: disable=unused-argument
        return result.get(self.name + "s")

    def __repr__(self):
        return "<" + str(type(self).__name__) + ":" + self.name + ">"


class WDAmountAttribute(WDAttribute):
    def get_select(self) -> str:
        return "?{name} ?{name}Unit".replace("{name}", self.name)

    def get_where(self):
        return """  OPTIONAL { ?item p:{name} ?{name}Node .
    ?{name}Node rdf:type wikibase:BestRank ; ps:{name} ?{name} .
    OPTIONAL { ?{name}Node psv:{name}/wikibase:quantityUnit ?{name}Unit. } }""".replace(
            '{name}', self.name
        )

    def get_group_by(self) -> str:
        return self.get_select()

    def get_str(self, result: dict[str, t.Any], language: str) -> str | None:
        value: str | None = result.get(self.name)
        unit: str | None = result.get(self.name + "Unit")
        if unit is not None:
            unit = unit.replace("http://www.wikidata.org/entity/", "")
            return str(value) + " " + get_label_for_entity(unit, language)
        return value


class WDArticle(WDAttribute):
    def __init__(self, language: str, kwargs: dict[str, t.Any] | None = None):
        super().__init__("wikipedia")
        self.language: str = language
        self.kwargs: dict[str, t.Any] = kwargs or {}

    def get_label(self, language: str):
        # language parameter is ignored
        return "Wikipedia ({language})".replace("{language}", self.language)

    def get_select(self):
        return "?article{language} ?articleName{language}".replace("{language}", self.language)

    def get_where(self):
        return """OPTIONAL { ?article{language} schema:about ?item ;
             schema:inLanguage "{language}" ;
             schema:isPartOf <https://{language}.wikipedia.org/> ;
             schema:name ?articleName{language} . }""".replace(
            '{language}', self.language
        )

    def get_group_by(self):
        return self.get_select()

    def get_str(self, result: dict[str, t.Any], language: str) -> str | None:
        key = "article{language}".replace("{language}", self.language)
        return result.get(key)


class WDLabelAttribute(WDAttribute):
    def get_select(self):
        return "(group_concat(distinct ?{name}Label;separator=', ') as ?{name}Labels)".replace("{name}", self.name)

    def get_where(self):
        return "OPTIONAL { ?item wdt:{name} ?{name} . }".replace("{name}", self.name)

    def get_wikibase_label(self) -> str:
        return "?{name} rdfs:label ?{name}Label .".replace("{name}", self.name)

    def get_str(self, result: dict[str, t.Any], language: str) -> str | None:
        return result.get(self.name + "Labels")


class WDURLAttribute(WDAttribute):
    HTTP_WIKIMEDIA_IMAGE: str = "http://commons.wikimedia.org/wiki/Special:FilePath/"

    def __init__(
        self,
        name: str,
        url_id: str | None = None,
        url_path_prefix: str | None = None,
        kwargs: dict[str, t.Any] | None = None,
    ):
        """
        :param url_id: ID matching one key in ``external_urls.json`` for
            converting IDs to full URLs.

        :param url_path_prefix: Path prefix if the values are of format
            ``account@domain``.  If provided, value are rewritten to
            ``https://<domain><url_path_prefix><account>``.  For example::

              WDURLAttribute('P4033', url_path_prefix='/@')

            Adds Property `P4033 <https://www.wikidata.org/wiki/Property:P4033>`_
            to the wikidata query.  This field might return for example
            ``libreoffice@fosstodon.org`` and the URL built from this is then:

            - account: ``libreoffice``
            - domain: ``fosstodon.org``
            - result url: https://fosstodon.org/@libreoffice
        """

        super().__init__(name)
        self.url_id: str | None = url_id
        self.url_path_prefix: str | None = url_path_prefix
        self.kwargs: dict[str, t.Any] = kwargs or {}

    def get_str(self, result: dict[str, t.Any], language: str) -> str | None:
        value: str | None = result.get(self.name + "s")
        if not value:
            return None

        value = value.split(",")[0]
        if self.url_id:
            url_id = self.url_id
            if value.startswith(WDURLAttribute.HTTP_WIKIMEDIA_IMAGE):
                value = value[len(WDURLAttribute.HTTP_WIKIMEDIA_IMAGE) :]
                url_id = "wikimedia_image"
            return get_external_url(url_id, value)

        if self.url_path_prefix:
            [account, domain] = [x.strip("@ ") for x in value.rsplit("@", 1)]
            return f"https://{domain}{self.url_path_prefix}{account}"

        return value


class WDGeoAttribute(WDAttribute):
    def get_label(self, language: str):
        return "OpenStreetMap"

    def get_select(self):
        return "?{name}Lat ?{name}Long".replace("{name}", self.name)

    def get_where(self):
        return """OPTIONAL { ?item p:{name}/psv:{name} [
    wikibase:geoLatitude ?{name}Lat ;
    wikibase:geoLongitude ?{name}Long ] }""".replace(
            '{name}', self.name
        )

    def get_group_by(self):
        return self.get_select()

    def get_str(self, result: dict[str, t.Any], language: str) -> str | None:
        latitude: str | None = result.get(self.name + "Lat")
        longitude: str | None = result.get(self.name + "Long")
        if latitude and longitude:
            return latitude + " " + longitude
        return None

    def get_geo_url(self, result: dict[str, t.Any], osm_zoom: int = 19) -> str | None:
        latitude: str | None = result.get(self.name + "Lat")
        longitude: str | None = result.get(self.name + "Long")
        if latitude and longitude:
            return get_earth_coordinates_url(latitude, longitude, osm_zoom)
        return None


class WDImageAttribute(WDURLAttribute):
    def __init__(self, name: str, url_id: str | None = None, priority: int = 100):
        super().__init__(name, url_id)
        self.priority: int = priority


class WDDateAttribute(WDAttribute):
    def get_select(self):
        return "?{name} ?{name}timePrecision ?{name}timeZone ?{name}timeCalendar".replace("{name}", self.name)

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

    def format_8(self, value: str, locale: str) -> str:  # pylint: disable=unused-argument
        # precision: less than a year
        return value

    def format_9(self, value: str, locale: str) -> str:
        year = int(value)
        # precision: year
        if year < 1584:
            if year < 0:
                return str(year - 1)
            return str(year)
        timestamp = isoparse(value)
        return format_date(timestamp, format="yyyy", locale=locale)

    def format_10(self, value: str, locale: str) -> str:
        # precision: month
        timestamp = isoparse(value)
        return format_date(timestamp, format="MMMM y", locale=locale)

    def format_11(self, value: str, locale: str) -> str:
        # precision: day
        timestamp = isoparse(value)
        return format_date(timestamp, format="full", locale=locale)

    def format_13(self, value: str, locale: str) -> str:
        timestamp = isoparse(value)
        # precision: minute
        return (
            get_datetime_format("medium", locale=locale)
            .replace("'", "")
            .replace("{0}", format_time(timestamp, "full", tzinfo=None, locale=locale))
            .replace("{1}", format_date(timestamp, "short", locale=locale))
        )

    def format_14(self, value: str, locale: str) -> str:
        # precision: second.
        return format_datetime(isoparse(value), format="full", locale=locale)

    DATE_FORMAT: dict[str, tuple[str, int]] = {
        "0": ("format_8", 1000000000),
        "1": ("format_8", 100000000),
        "2": ("format_8", 10000000),
        "3": ("format_8", 1000000),
        "4": ("format_8", 100000),
        "5": ("format_8", 10000),
        "6": ("format_8", 1000),
        "7": ("format_8", 100),
        "8": ("format_8", 10),
        "9": ("format_9", 1),  # year
        "10": ("format_10", 1),  # month
        "11": ("format_11", 0),  # day
        "12": ("format_13", 0),  # hour (not supported by babel, display minute)
        "13": ("format_13", 0),  # minute
        "14": ("format_14", 0),  # second
    }

    def get_str(self, result: dict[str, t.Any], language: str) -> str | None:
        value: str | None = result.get(self.name)
        if value == "" or value is None:
            return None
        _p: str = result.get(self.name + "timePrecision") or "1"
        date_format = WDDateAttribute.DATE_FORMAT.get(_p)
        if date_format is not None:
            format_method = getattr(self, date_format[0])
            precision: int = date_format[1]
            try:
                if precision >= 1:
                    _t = value.split("-")
                    if value.startswith("-"):
                        value = "-" + _t[1]
                    else:
                        value = _t[0]
                return format_method(value, language)
            except Exception:  # pylint: disable=broad-except
                return value
        return value


WDAttrType = (
    WDAttribute
    | WDAmountAttribute
    | WDArticle
    | WDLabelAttribute
    | WDURLAttribute
    | WDGeoAttribute
    | WDImageAttribute
    | WDDateAttribute
)
WDAttrList = list[WDAttrType]

_WIKIDATA_PROPERTIES_OVERRIDE: WikiDataPropertiesType = {
    "P434": "MusicBrainz",
    "P435": "MusicBrainz",
    "P436": "MusicBrainz",
    "P966": "MusicBrainz",
    "P345": "IMDb",
    "P2397": "YouTube",
    "P1651": "YouTube",
    "P2002": "Twitter",
    "P2013": "Facebook",
    "P2003": "Instagram",
    "P4033": "Mastodon",
    "P11947": "Lemmy",
    "P12622": "PeerTube",
}
"""Custom hardcoded property names for some Wikidata IDs. Only used if the
name Wikidata assigned isn't user-friendly."""


def fetch_properties(units: dict[str, WikiDataUnitType]) -> WikiDataPropertiesType:
    properties = _WIKIDATA_PROPERTIES_OVERRIDE

    # WIKIDATA_PROPERTIES : add unit symbols
    for k, v in units.items():
        properties[k] = v["symbol"]

    # WIKIDATA_PROPERTIES : add property labels
    wikidata_property_names: list[str] = []
    for attribute in get_attributes("en"):
        if type(attribute) in (WDAttribute, WDAmountAttribute, WDURLAttribute, WDDateAttribute, WDLabelAttribute):
            if attribute.name not in properties:
                wikidata_property_names.append("wd:" + attribute.name)

        query = QUERY_PROPERTY_NAMES.replace("%ATTRIBUTES%", " ".join(wikidata_property_names))
        kwargs: dict[str, t.Any] = {"timeout": 60}
        json_response = send_wikidata_query(query, **kwargs)

        for result in json_response.get("results", {}).get("bindings", {}):
            name_field = result.get("name")
            if not name_field:
                continue
            name = name_field["value"]
            lang = name_field["xml:lang"]
            entity_id = result["item"]["value"].replace("http://www.wikidata.org/entity/", "")

            if name:
                prop = properties.get(entity_id) or {}
                prop[lang] = name.capitalize()  # pyright: ignore[reportIndexIssue]
                properties[entity_id] = prop
            else:
                properties[entity_id] = name.capitalize()

    return properties


def get_attributes(language: str):
    # pylint: disable=too-many-statements
    attributes: WDAttrList = []

    def add_value(name: str):
        attributes.append(WDAttribute(name))

    def add_amount(name: str):
        attributes.append(WDAmountAttribute(name))

    def add_label(name: str):
        attributes.append(WDLabelAttribute(name))

    def add_url(name: str, url_id: str | None = None, url_path_prefix: str | None = None, **kwargs: dict[str, t.Any]):
        attributes.append(WDURLAttribute(name, url_id, url_path_prefix, kwargs))

    def add_image(name: str, url_id: str | None = None, priority: int = 1):
        attributes.append(WDImageAttribute(name, url_id, priority))

    def add_date(name: str):
        attributes.append(WDDateAttribute(name))

    # Dates
    for p in [
        "P571",  # inception date
        "P576",  # dissolution date
        "P580",  # start date
        "P582",  # end date
        "P569",  # date of birth
        "P570",  # date of death
        "P619",  # date of spacecraft launch
        "P620",
    ]:  # date of spacecraft landing
        add_date(p)

    for p in [
        "P27",  # country of citizenship
        "P495",  # country of origin
        "P17",  # country
        "P159",
    ]:  # headquarters location
        add_label(p)

    # Places
    for p in [
        "P36",  # capital
        "P35",  # head of state
        "P6",  # head of government
        "P122",  # basic form of government
        "P37",
    ]:  # official language
        add_label(p)

    add_value("P1082")  # population
    add_amount("P2046")  # area
    add_amount("P281")  # postal code
    add_label("P38")  # currency
    add_amount("P2048")  # height (building)

    # Media
    for p in [
        "P400",  # platform (videogames, computing)
        "P50",  # author
        "P170",  # creator
        "P57",  # director
        "P175",  # performer
        "P178",  # developer
        "P162",  # producer
        "P176",  # manufacturer
        "P58",  # screenwriter
        "P272",  # production company
        "P264",  # record label
        "P123",  # publisher
        "P449",  # original network
        "P750",  # distributed by
        "P86",
    ]:  # composer
        add_label(p)

    add_date("P577")  # publication date
    add_label("P136")  # genre (music, film, artistic...)
    add_label("P364")  # original language
    add_value("P212")  # ISBN-13
    add_value("P957")  # ISBN-10
    add_label("P275")  # copyright license
    add_label("P277")  # programming language
    add_value("P348")  # version
    add_label("P840")  # narrative location

    # Languages
    add_value("P1098")  # number of speakers
    add_label("P282")  # writing system
    add_label("P1018")  # language regulatory body
    add_value("P218")  # language code (ISO 639-1)

    # Other
    add_label("P169")  # ceo
    add_label("P112")  # founded by
    add_label("P1454")  # legal form (company, organization)
    add_label("P137")  # operator (service, facility, ...)
    add_label("P1029")  # crew members (tripulation)
    add_label("P225")  # taxon name
    add_value("P274")  # chemical formula
    add_label("P1346")  # winner (sports, contests, ...)
    add_value("P1120")  # number of deaths
    add_value("P498")  # currency code (ISO 4217)

    # URL
    kwargs: dict[str, t.Any] = {"official": True}
    add_url("P856", **kwargs)  # official website
    attributes.append(WDArticle(language))  # wikipedia (user language)
    if not language.startswith("en"):
        attributes.append(WDArticle("en"))  # wikipedia (english)

    add_url("P1324")  # source code repository
    add_url("P1581")  # blog
    add_url("P434", url_id="musicbrainz_artist")
    add_url("P435", url_id="musicbrainz_work")
    add_url("P436", url_id="musicbrainz_release_group")
    add_url("P966", url_id="musicbrainz_label")
    add_url("P345", url_id="imdb_id")
    add_url("P2397", url_id="youtube_channel")
    add_url("P1651", url_id="youtube_video")
    add_url("P2002", url_id="twitter_profile")
    add_url("P2013", url_id="facebook_profile")
    add_url("P2003", url_id="instagram_profile")

    # Fediverse
    add_url("P4033", url_path_prefix="/@")  # Mastodon user
    add_url("P11947", url_path_prefix="/c/")  # Lemmy community
    add_url("P12622", url_path_prefix="/c/")  # PeerTube channel

    # Map
    attributes.append(WDGeoAttribute("P625"))

    # Image
    add_image("P15", priority=1, url_id="wikimedia_image")  # route map
    add_image("P242", priority=2, url_id="wikimedia_image")  # locator map
    add_image("P154", priority=3, url_id="wikimedia_image")  # logo
    add_image("P18", priority=4, url_id="wikimedia_image")  # image
    add_image("P41", priority=5, url_id="wikimedia_image")  # flag
    add_image("P2716", priority=6, url_id="wikimedia_image")  # collage
    add_image("P2910", priority=7, url_id="wikimedia_image")  # icon

    return attributes


def get_label_for_entity(entity_id: str, language: str) -> str:
    # only import properties locally to prevent cyclic import when initializing WIKIDATA_PROPERTIES
    from searx.data import WIKIDATA_PROPERTIES  # pylint: disable=import-outside-toplevel

    property_name = WIKIDATA_PROPERTIES.get(entity_id)
    if property_name is None:
        return entity_id

    if isinstance(property_name, str):
        return property_name

    if name := property_name.get(language):
        return name

    if name := property_name.get(language.split("-")[0]):
        return name

    if name := property_name.get("en"):
        return name

    return entity_id
