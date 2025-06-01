# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implementations used for weather conditions and forecast."""
# pylint: disable=too-few-public-methods
from __future__ import annotations

__all__ = [
    "symbol_url",
    "Temperature",
    "Pressure",
    "WindSpeed",
    "RelativeHumidity",
    "Compass",
    "WeatherConditionType",
    "DateTime",
    "GeoLocation",
]

import typing

import base64
import datetime
import dataclasses

from urllib.parse import quote_plus

import babel
import babel.numbers
import babel.dates
import babel.languages

from searx import network
from searx.cache import ExpireCache, ExpireCacheCfg
from searx.extended_types import sxng_request
from searx.wikidata_units import convert_to_si, convert_from_si

WEATHER_DATA_CACHE: ExpireCache = None  # type: ignore
"""A simple cache for weather data (geo-locations, icons, ..)"""

YR_WEATHER_SYMBOL_URL = "https://raw.githubusercontent.com/nrkno/yr-weather-symbols/refs/heads/master/symbols/outline"


def get_WEATHER_DATA_CACHE():

    global WEATHER_DATA_CACHE  # pylint: disable=global-statement

    if WEATHER_DATA_CACHE is None:
        WEATHER_DATA_CACHE = ExpireCache.build_cache(
            ExpireCacheCfg(
                name="WEATHER_DATA_CACHE",
                MAX_VALUE_LEN=1024 * 200,  # max. 200kB per icon (icons have most often 10-20kB)
                MAXHOLD_TIME=60 * 60 * 24 * 7 * 4,  # 4 weeks
            )
        )
    return WEATHER_DATA_CACHE


def _get_sxng_locale_tag() -> str:
    # The function should return a locale (the sxng-tag: de-DE.en-US, ..) that
    # can later be used to format and convert measured values for the output of
    # weather data to the user.
    #
    # In principle, SearXNG only has two possible parameters for determining
    # the locale: the UI language or the search- language/region.  Since the
    # conversion of weather data and time information is usually
    # region-specific, the UI language is not suitable.
    #
    # It would probably be ideal to use the user's geolocation, but this will
    # probably never be available in SearXNG (privacy critical).
    #
    # Therefore, as long as no "better" parameters are available, this function
    # returns a locale based on the search region.

    # pylint: disable=import-outside-toplevel,disable=cyclic-import
    from searx import query
    from searx.preferences import ClientPref

    query = query.RawTextQuery(sxng_request.form.get("q", ""), [])
    if query.languages and query.languages[0] not in ["all", "auto"]:
        return query.languages[0]

    search_lang = sxng_request.form.get("language")
    if search_lang and search_lang not in ["all", "auto"]:
        return search_lang

    client_pref = ClientPref.from_http_request(sxng_request)
    search_lang = client_pref.locale_tag
    if search_lang and search_lang not in ["all", "auto"]:
        return search_lang
    return "en"


def symbol_url(condition: WeatherConditionType) -> str | None:
    """Returns ``data:`` URL for the weather condition symbol or ``None`` if
    the condition is not of type :py:obj:`WeatherConditionType`.

    If symbol (SVG) is not already in the :py:obj:`WEATHER_DATA_CACHE` its
    fetched from https://github.com/nrkno/yr-weather-symbols
    """
    # Symbols for darkmode/lightmode? .. and day/night symbols? .. for the
    # latter we need a geopoint (critical in sense of privacy)

    fname = YR_WEATHER_SYMBOL_MAP.get(condition)
    if fname is None:
        return None

    ctx = "weather_symbol_url"
    cache = get_WEATHER_DATA_CACHE()
    origin_url = f"{YR_WEATHER_SYMBOL_URL}/{fname}.svg"

    data_url = cache.get(origin_url, ctx=ctx)
    if data_url is not None:
        return data_url

    response = network.get(origin_url, timeout=3)
    if response.status_code == 200:
        mimetype = response.headers['Content-Type']
        data_url = f"data:{mimetype};base64,{str(base64.b64encode(response.content), 'utf-8')}"
        cache.set(key=origin_url, value=data_url, expire=None, ctx=ctx)
    return data_url


@dataclasses.dataclass
class GeoLocation:
    """Minimal implementation of Geocoding."""

    # The type definition was based on the properties from the geocoding API of
    # open-meteo.
    #
    # - https://open-meteo.com/en/docs/geocoding-api
    # - https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    # - https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2

    name: str
    latitude: float  # Geographical WGS84 coordinates of this location
    longitude: float
    elevation: float  # Elevation above mean sea level of this location
    country_code: str  # 2-Character ISO-3166-1 alpha2 country code. E.g. DE for Germany
    timezone: str  # Time zone using time zone database definitions

    def __str__(self):
        return self.name

    def locale(self) -> babel.Locale:

        # by region of the search language
        sxng_tag = _get_sxng_locale_tag()
        if "-" in sxng_tag:
            locale = babel.Locale.parse(_get_sxng_locale_tag(), sep='-')
            return locale

        # by most popular language in the region (country code)
        for lang in babel.languages.get_official_languages(self.country_code):
            try:
                locale = babel.Locale.parse(f"{lang}_{self.country_code}")
                return locale
            except babel.UnknownLocaleError:
                continue

        # No locale could be determined.  This does not actually occur, but if
        # it does, the English language is used by default.  But not region US.
        # US has some units that are only used in US but not in the rest of the
        # world (e.g. °F instead of °C)
        return babel.Locale("en", territory="DE")

    @classmethod
    def by_query(cls, search_term: str) -> GeoLocation:
        """Factory method to get a GeoLocation object by a search term.  If no
        location can be determined for the search term, a :py:obj:`ValueError`
        is thrown.
        """

        ctx = "weather_geolocation_by_query"
        cache = get_WEATHER_DATA_CACHE()
        geo_props = cache.get(search_term, ctx=ctx)

        if not geo_props:
            geo_props = cls._query_open_meteo(search_term=search_term)
            cache.set(key=search_term, value=geo_props, expire=None, ctx=ctx)

        return cls(**geo_props)

    @classmethod
    def _query_open_meteo(cls, search_term: str) -> dict:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={quote_plus(search_term)}"
        resp = network.get(url, timeout=3)
        if resp.status_code != 200:
            raise ValueError(f"unknown geo location: '{search_term}'")
        results = resp.json().get("results")
        if not results:
            raise ValueError(f"unknown geo location: '{search_term}'")
        location = results[0]
        return {field.name: location[field.name] for field in dataclasses.fields(cls)}


DateTimeFormats = typing.Literal["full", "long", "medium", "short"]


class DateTime:
    """Class to represent date & time.  Essentially, it is a wrapper that
    conveniently combines :py:obj:`datetime.datetime` and
    :py:obj:`babel.dates.format_datetime`.  A conversion of time zones is not
    provided (in the current version).
    """

    def __init__(self, time: datetime.datetime):
        self.datetime = time

    def __str__(self):
        return self.l10n()

    def l10n(
        self,
        fmt: DateTimeFormats | str = "medium",
        locale: babel.Locale | GeoLocation | None = None,
    ) -> str:
        """Localized representation of date & time."""
        if isinstance(locale, GeoLocation):
            locale = locale.locale()
        elif locale is None:
            locale = babel.Locale.parse(_get_sxng_locale_tag(), sep='-')
        return babel.dates.format_datetime(self.datetime, format=fmt, locale=locale)


class Temperature:
    """Class for converting temperature units and for string representation of
    measured values."""

    si_name = "Q11579"

    Units = typing.Literal["°C", "°F", "K"]
    """Supported temperature units."""

    units = list(typing.get_args(Units))

    def __init__(self, value: float, unit: Units):
        if unit not in self.units:
            raise ValueError(f"invalid unit: {unit}")
        self.si: float = convert_to_si(  # pylint: disable=invalid-name
            si_name=self.si_name,
            symbol=unit,
            value=value,
        )

    def __str__(self):
        return self.l10n()

    def value(self, unit: Units) -> float:
        return convert_from_si(si_name=self.si_name, symbol=unit, value=self.si)

    def l10n(
        self,
        unit: Units | None = None,
        locale: babel.Locale | GeoLocation | None = None,
        template: str = "{value} {unit}",
        num_pattern: str = "#,##0",
    ) -> str:
        """Localized representation of a measured value.

        If the ``unit`` is not set, an attempt is made to determine a ``unit``
        matching the territory of the ``locale``.  If the locale is not set, an
        attempt is made to determine it from the HTTP request.

        The value is converted into the respective unit before formatting.

        The argument ``num_pattern`` is used to determine the string formatting
        of the numerical value:

        - https://babel.pocoo.org/en/latest/numbers.html#pattern-syntax
        - https://unicode.org/reports/tr35/tr35-numbers.html#Number_Format_Patterns

        The argument ``template`` specifies how the **string formatted** value
        and unit are to be arranged.

        - `Format Specification Mini-Language
          <https://docs.python.org/3/library/string.html#format-specification-mini-language>`.
        """

        if isinstance(locale, GeoLocation):
            locale = locale.locale()
        elif locale is None:
            locale = babel.Locale.parse(_get_sxng_locale_tag(), sep='-')

        if unit is None:  # unit by territory
            unit = "°C"
            if locale.territory in ["US"]:
                unit = "°F"
        val_str = babel.numbers.format_decimal(self.value(unit), locale=locale, format=num_pattern)
        return template.format(value=val_str, unit=unit)


class Pressure:
    """Class for converting pressure units and for string representation of
    measured values."""

    si_name = "Q44395"

    Units = typing.Literal["Pa", "hPa", "cm Hg", "bar"]
    """Supported units."""

    units = list(typing.get_args(Units))

    def __init__(self, value: float, unit: Units):
        if unit not in self.units:
            raise ValueError(f"invalid unit: {unit}")
        # pylint: disable=invalid-name
        self.si: float = convert_to_si(si_name=self.si_name, symbol=unit, value=value)

    def __str__(self):
        return self.l10n()

    def value(self, unit: Units) -> float:
        return convert_from_si(si_name=self.si_name, symbol=unit, value=self.si)

    def l10n(
        self,
        unit: Units | None = None,
        locale: babel.Locale | GeoLocation | None = None,
        template: str = "{value} {unit}",
        num_pattern: str = "#,##0",
    ) -> str:
        if isinstance(locale, GeoLocation):
            locale = locale.locale()
        elif locale is None:
            locale = babel.Locale.parse(_get_sxng_locale_tag(), sep='-')

        if unit is None:  # unit by territory?
            unit = "hPa"

        val_str = babel.numbers.format_decimal(self.value(unit), locale=locale, format=num_pattern)
        return template.format(value=val_str, unit=unit)


class WindSpeed:
    """Class for converting speed or velocity units and for string
    representation of measured values.

    .. hint::

       Working with unit ``Bft`` (:py:obj:`searx.wikidata_units.Beaufort`) will
       throw a :py:obj:`ValueError` for egative values or values greater 16 Bft
       (55.6 m/s)
    """

    si_name = "Q182429"

    Units = typing.Literal["m/s", "km/h", "kn", "mph", "mi/h", "Bft"]
    """Supported units."""

    units = list(typing.get_args(Units))

    def __init__(self, value: float, unit: Units):
        if unit not in self.units:
            raise ValueError(f"invalid unit: {unit}")
        # pylint: disable=invalid-name
        self.si: float = convert_to_si(si_name=self.si_name, symbol=unit, value=value)

    def __str__(self):
        return self.l10n()

    def value(self, unit: Units) -> float:
        return convert_from_si(si_name=self.si_name, symbol=unit, value=self.si)

    def l10n(
        self,
        unit: Units | None = None,
        locale: babel.Locale | GeoLocation | None = None,
        template: str = "{value} {unit}",
        num_pattern: str = "#,##0",
    ) -> str:
        if isinstance(locale, GeoLocation):
            locale = locale.locale()
        elif locale is None:
            locale = babel.Locale.parse(_get_sxng_locale_tag(), sep='-')

        if unit is None:  # unit by territory?
            unit = "m/s"

        val_str = babel.numbers.format_decimal(self.value(unit), locale=locale, format=num_pattern)
        return template.format(value=val_str, unit=unit)


class RelativeHumidity:
    """Amount of relative humidity in the air. The unit is ``%``"""

    Units = typing.Literal["%"]
    """Supported unit."""

    units = list(typing.get_args(Units))

    def __init__(self, humidity: float):
        self.humidity = humidity

    def __str__(self):
        return self.l10n()

    def value(self) -> float:
        return self.humidity

    def l10n(
        self,
        locale: babel.Locale | GeoLocation | None = None,
        template: str = "{value}{unit}",
        num_pattern: str = "#,##0",
    ) -> str:
        if isinstance(locale, GeoLocation):
            locale = locale.locale()
        elif locale is None:
            locale = babel.Locale.parse(_get_sxng_locale_tag(), sep='-')

        unit = "%"
        val_str = babel.numbers.format_decimal(self.value(), locale=locale, format=num_pattern)
        return template.format(value=val_str, unit=unit)


class Compass:
    """Class for converting compass points and azimuth values (360°)"""

    Units = typing.Literal["°", "Point"]

    Point = typing.Literal[
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    """Compass point type definition"""

    TURN = 360.0
    """Full turn (360°)"""

    POINTS = list(typing.get_args(Point))
    """Compass points."""

    RANGE = TURN / len(POINTS)
    """Angle sector of a compass point"""

    def __init__(self, azimuth: float | int | Point):
        if isinstance(azimuth, str):
            if azimuth not in self.POINTS:
                raise ValueError(f"Invalid compass point: {azimuth}")
            azimuth = self.POINTS.index(azimuth) * self.RANGE
        self.azimuth = azimuth % self.TURN

    def __str__(self):
        return self.l10n()

    def value(self, unit: Units):
        if unit == "Point":
            return self.point(self.azimuth)
        if unit == "°":
            return self.azimuth
        raise ValueError(f"unknown unit: {unit}")

    @classmethod
    def point(cls, azimuth: float | int) -> Point:
        """Returns the compass point to an azimuth value."""
        azimuth = azimuth % cls.TURN
        # The angle sector of a compass point starts 1/2 sector range before
        # and after compass point (example: "N" goes from -11.25° to +11.25°)
        azimuth = azimuth - cls.RANGE / 2
        idx = int(azimuth // cls.RANGE)
        return cls.POINTS[idx]

    def l10n(
        self,
        unit: Units = "Point",
        locale: babel.Locale | GeoLocation | None = None,
        template: str = "{value}{unit}",
        num_pattern: str = "#,##0",
    ) -> str:
        if isinstance(locale, GeoLocation):
            locale = locale.locale()
        elif locale is None:
            locale = babel.Locale.parse(_get_sxng_locale_tag(), sep='-')

        if unit == "Point":
            val_str = self.value(unit)
            return template.format(value=val_str, unit="")

        val_str = babel.numbers.format_decimal(self.value(unit), locale=locale, format=num_pattern)
        return template.format(value=val_str, unit=unit)


WeatherConditionType = typing.Literal[
    # The capitalized string goes into to i18n/l10n (en: "Clear sky" -> de: "wolkenloser Himmel")
    "clear sky",
    "partly cloudy",
    "cloudy",
    "fair",
    "fog",
    # rain
    "light rain and thunder",
    "light rain showers and thunder",
    "light rain showers",
    "light rain",
    "rain and thunder",
    "rain showers and thunder",
    "rain showers",
    "rain",
    "heavy rain and thunder",
    "heavy rain showers and thunder",
    "heavy rain showers",
    "heavy rain",
    # sleet
    "light sleet and thunder",
    "light sleet showers and thunder",
    "light sleet showers",
    "light sleet",
    "sleet and thunder",
    "sleet showers and thunder",
    "sleet showers",
    "sleet",
    "heavy sleet and thunder",
    "heavy sleet showers and thunder",
    "heavy sleet showers",
    "heavy sleet",
    # snow
    "light snow and thunder",
    "light snow showers and thunder",
    "light snow showers",
    "light snow",
    "snow and thunder",
    "snow showers and thunder",
    "snow showers",
    "snow",
    "heavy snow and thunder",
    "heavy snow showers and thunder",
    "heavy snow showers",
    "heavy snow",
]
"""Standardized designations for weather conditions.  The designators were
taken from a collaboration between NRK and Norwegian Meteorological Institute
(yr.no_).  `Weather symbols`_ can be assigned to the identifiers
(weathericons_) and they are included in the translation (i18n/l10n
:origin:`searx/searxng.msg`).

.. _yr.no: https://www.yr.no/en
.. _Weather symbols: https://github.com/nrkno/yr-weather-symbols
.. _weathericons: https://github.com/metno/weathericons
"""

YR_WEATHER_SYMBOL_MAP = {
    "clear sky": "01d",  # 01d clearsky_day
    "partly cloudy": "03d",  # 03d partlycloudy_day
    "cloudy": "04",  # 04 cloudy
    "fair": "02d",  # 02d fair_day
    "fog": "15",  # 15 fog
    # rain
    "light rain and thunder": "30",  # 30 lightrainandthunder
    "light rain showers and thunder": "24d",  # 24d lightrainshowersandthunder_day
    "light rain showers": "40d",  # 40d lightrainshowers_day
    "light rain": "46",  # 46 lightrain
    "rain and thunder": "22",  # 22 rainandthunder
    "rain showers and thunder": "06d",  # 06d rainshowersandthunder_day
    "rain showers": "05d",  # 05d rainshowers_day
    "rain": "09",  # 09 rain
    "heavy rain and thunder": "11",  # 11 heavyrainandthunder
    "heavy rain showers and thunder": "25d",  # 25d heavyrainshowersandthunder_day
    "heavy rain showers": "41d",  # 41d heavyrainshowers_day
    "heavy rain": "10",  # 10 heavyrain
    # sleet
    "light sleet and thunder": "31",  # 31 lightsleetandthunder
    "light sleet showers and thunder": "26d",  # 26d lightssleetshowersandthunder_day
    "light sleet showers": "42d",  # 42d lightsleetshowers_day
    "light sleet": "47",  # 47 lightsleet
    "sleet and thunder": "23",  # 23 sleetandthunder
    "sleet showers and thunder": "20d",  # 20d sleetshowersandthunder_day
    "sleet showers": "07d",  # 07d sleetshowers_day
    "sleet": "12",  # 12 sleet
    "heavy sleet and thunder": "32",  # 32 heavysleetandthunder
    "heavy sleet showers and thunder": "27d",  # 27d heavysleetshowersandthunder_day
    "heavy sleet showers": "43d",  # 43d heavysleetshowers_day
    "heavy sleet": "48",  # 48 heavysleet
    # snow
    "light snow and thunder": "33",  # 33 lightsnowandthunder
    "light snow showers and thunder": "28d",  # 28d lightssnowshowersandthunder_day
    "light snow showers": "44d",  # 44d lightsnowshowers_day
    "light snow": "49",  # 49 lightsnow
    "snow and thunder": "14",  # 14 snowandthunder
    "snow showers and thunder": "21d",  # 21d snowshowersandthunder_day
    "snow showers": "08d",  # 08d snowshowers_day
    "snow": "13",  # 13 snow
    "heavy snow and thunder": "34",  # 34 heavysnowandthunder
    "heavy snow showers and thunder": "29d",  # 29d heavysnowshowersandthunder_day
    "heavy snow showers": "45d",  # 45d heavysnowshowers_day
    "heavy snow": "50",  # 50 heavysnow
}
"""Map a :py:obj:`WeatherConditionType` to a `YR weather symbol`_

.. code::

   base_url = "https://raw.githubusercontent.com/nrkno/yr-weather-symbols/refs/heads/master/symbols"
   icon_url = f"{base_url}/outline/{YR_WEATHER_SYMBOL_MAP['sleet showers']}.svg"

.. _YR weather symbol: https://github.com/nrkno/yr-weather-symbols/blob/master/locales/en.json

"""

if __name__ == "__main__":

    # test: fetch all symbols of the type catalog ..
    for c in typing.get_args(WeatherConditionType):
        symbol_url(condition=c)

    _cache = get_WEATHER_DATA_CACHE()
    title = "cached weather condition symbols"
    print(title)
    print("=" * len(title))
    print(_cache.state().report())
    print()
    title = f"properties of {_cache.cfg.name}"
    print(title)
    print("=" * len(title))
    print(str(_cache.properties))  # type: ignore
