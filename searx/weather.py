# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implementations used for weather conditions and forecast."""
# pylint: disable=too-few-public-methods

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

# msgspec: note that if using PEP 563 “postponed evaluation of annotations”
# (e.g. from __future__ import annotations) only the following spellings will
# work: https://jcristharif.com/msgspec/structs.html#class-variables
from typing import ClassVar
import typing as t

import base64
import datetime
import zoneinfo

from urllib.parse import quote_plus

import babel
import babel.numbers
import babel.dates
import babel.languages
import flask_babel  # pyright: ignore[reportMissingTypeStubs]
import msgspec

from searx import network
from searx.cache import ExpireCache, ExpireCacheCfg
from searx.extended_types import sxng_request
from searx.wikidata_units import convert_to_si, convert_from_si

WEATHER_DATA_CACHE: ExpireCache | None = None
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


def symbol_url(condition: "WeatherConditionType") -> str | None:
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


class GeoLocation(msgspec.Struct, kw_only=True):
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

    @property
    def zoneinfo(self) -> zoneinfo.ZoneInfo:
        return zoneinfo.ZoneInfo(self.timezone)

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
    def by_query(cls, search_term: str) -> "GeoLocation":
        """Factory method to get a GeoLocation object by a search term.  If no
        location can be determined for the search term, a :py:obj:`ValueError`
        is thrown.
        """

        ctx = "weather_geolocation_by_query"
        cache = get_WEATHER_DATA_CACHE()
        # {'name': 'Berlin', 'latitude': 52.52437, 'longitude': 13.41053,
        #  'elevation': 74.0, 'country_code': 'DE', 'timezone': 'Europe/Berlin'}
        geo_props = cache.get(search_term, ctx=ctx)

        if not geo_props:
            geo_props = cls._query_open_meteo(search_term=search_term)
            cache.set(key=search_term, value=geo_props, expire=None, ctx=ctx)

        return cls(**geo_props)  # type: ignore

    @classmethod
    def _query_open_meteo(cls, search_term: str) -> dict[str, str]:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={quote_plus(search_term)}"
        resp = network.get(url, timeout=3)
        if resp.status_code != 200:
            raise ValueError(f"unknown geo location: '{search_term}'")
        results = resp.json().get("results")
        if not results:
            raise ValueError(f"unknown geo location: '{search_term}'")
        location = results[0]
        return {field_name: location[field_name] for field_name in cls.__struct_fields__}


DateTimeFormats = t.Literal["full", "long", "medium", "short"]
DateTimeLocaleTypes = t.Literal["UI"]


class DateTime(msgspec.Struct):
    """Class to represent date & time.  Essentially, it is a wrapper that
    conveniently combines :py:obj:`datetime.datetime` and
    :py:obj:`babel.dates.format_datetime`.  A conversion of time zones is not
    provided (in the current version).

    The localized string representation can be obtained via the
    :py:obj:`DateTime.l10n` and :py:obj:`DateTime.l10n_date` methods, where the
    ``locale`` parameter defaults to the search language.  Alternatively, a
    :py:obj:`GeoLocation` or a :py:obj:`babel.Locale` instance can be passed
    directly. If the UI language is to be used, the string ``UI`` can be passed
    as the value for the ``locale``.
    """

    datetime: datetime.datetime

    def __str__(self):
        return self.l10n()

    def l10n(
        self,
        fmt: DateTimeFormats | str = "medium",
        locale: DateTimeLocaleTypes | babel.Locale | GeoLocation | None = None,
    ) -> str:
        """Localized representation of date & time."""
        if isinstance(locale, str) and locale == "UI":
            locale = flask_babel.get_locale()
        elif isinstance(locale, GeoLocation):
            locale = locale.locale()
        elif locale is None:
            locale = babel.Locale.parse(_get_sxng_locale_tag(), sep='-')
        return babel.dates.format_datetime(self.datetime, format=fmt, locale=locale)

    def l10n_date(
        self,
        fmt: DateTimeFormats | str = "medium",
        locale: DateTimeLocaleTypes | babel.Locale | GeoLocation | None = None,
    ) -> str:
        """Localized representation of date."""

        if isinstance(locale, str) and locale == "UI":
            locale = flask_babel.get_locale()
        elif isinstance(locale, GeoLocation):
            locale = locale.locale()
        elif locale is None:
            locale = babel.Locale.parse(_get_sxng_locale_tag(), sep='-')
        return babel.dates.format_date(self.datetime, format=fmt, locale=locale)


TemperatureUnit: t.TypeAlias = t.Literal["°C", "°F", "K"]
TEMPERATURE_UNITS: t.Final[tuple[TemperatureUnit]] = t.get_args(TemperatureUnit)


class Temperature(msgspec.Struct, kw_only=True):
    """Class for converting temperature units and for string representation of
    measured values."""

    val: float
    unit: TemperatureUnit

    si_name: ClassVar[str] = "Q11579"
    UNITS: ClassVar[tuple[TemperatureUnit]] = TEMPERATURE_UNITS

    def __post_init__(self):
        if self.unit not in self.UNITS:
            raise ValueError(f"invalid unit: {self.unit}")

    def __str__(self):
        return self.l10n()

    def value(self, unit: TemperatureUnit) -> float:
        if unit == self.unit:
            return self.val
        si_val = convert_to_si(si_name=self.si_name, symbol=self.unit, value=self.val)
        return convert_from_si(si_name=self.si_name, symbol=unit, value=si_val)

    def l10n(
        self,
        unit: TemperatureUnit | None = None,
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


PressureUnit: t.TypeAlias = t.Literal["Pa", "hPa", "cm Hg", "bar"]
PRESSURE_UNITS: t.Final[tuple[PressureUnit]] = t.get_args(PressureUnit)


class Pressure(msgspec.Struct, kw_only=True):
    """Class for converting pressure units and for string representation of
    measured values."""

    val: float
    unit: PressureUnit

    si_name: ClassVar[str] = "Q44395"
    UNITS: ClassVar[tuple[PressureUnit]] = PRESSURE_UNITS

    def __post_init__(self):
        if self.unit not in self.UNITS:
            raise ValueError(f"invalid unit: {self.unit}")

    def __str__(self):
        return self.l10n()

    def value(self, unit: PressureUnit) -> float:
        if unit == self.unit:
            return self.val
        si_val = convert_to_si(si_name=self.si_name, symbol=self.unit, value=self.val)
        return convert_from_si(si_name=self.si_name, symbol=unit, value=si_val)

    def l10n(
        self,
        unit: PressureUnit | None = None,
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


WindSpeedUnit: t.TypeAlias = t.Literal["m/s", "km/h", "kn", "mph", "mi/h", "Bft"]
WIND_SPEED_UNITS: t.Final[tuple[WindSpeedUnit]] = t.get_args(WindSpeedUnit)


class WindSpeed(msgspec.Struct, kw_only=True):
    """Class for converting speed or velocity units and for string
    representation of measured values.

    .. hint::

       Working with unit ``Bft`` (:py:obj:`searx.wikidata_units.Beaufort`) will
       throw a :py:obj:`ValueError` for egative values or values greater 16 Bft
       (55.6 m/s)
    """

    val: float
    unit: WindSpeedUnit

    si_name: ClassVar[str] = "Q182429"
    UNITS: ClassVar[tuple[WindSpeedUnit]] = WIND_SPEED_UNITS

    def __post_init__(self):
        if self.unit not in self.UNITS:
            raise ValueError(f"invalid unit: {self.unit}")

    def __str__(self):
        return self.l10n()

    def value(self, unit: WindSpeedUnit) -> float:
        if unit == self.unit:
            return self.val
        si_val = convert_to_si(si_name=self.si_name, symbol=self.unit, value=self.val)
        return convert_from_si(si_name=self.si_name, symbol=unit, value=si_val)

    def l10n(
        self,
        unit: WindSpeedUnit | None = None,
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


RelativeHumidityUnit: t.TypeAlias = t.Literal["%"]
RELATIVE_HUMIDITY_UNITS: t.Final[tuple[RelativeHumidityUnit]] = t.get_args(RelativeHumidityUnit)


class RelativeHumidity(msgspec.Struct):
    """Amount of relative humidity in the air. The unit is ``%``"""

    val: float

    # there exists only one unit (%) --> set "%" as the final value (constant)
    unit: ClassVar[RelativeHumidityUnit] = "%"
    UNITS: ClassVar[tuple[RelativeHumidityUnit]] = RELATIVE_HUMIDITY_UNITS

    def __post_init__(self):
        if self.unit not in self.UNITS:
            raise ValueError(f"invalid unit: {self.unit}")

    def __str__(self):
        return self.l10n()

    def value(self) -> float:
        return self.val

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


CompassPoint: t.TypeAlias = t.Literal[
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
]
"""Compass point type definition"""
COMPASS_POINTS: t.Final[tuple[CompassPoint]] = t.get_args(CompassPoint)

CompassUnit: t.TypeAlias = t.Literal["°", "Point"]
COMPASS_UNITS: t.Final[tuple[CompassUnit]] = t.get_args(CompassUnit)


class Compass(msgspec.Struct):
    """Class for converting compass points and azimuth values (360°)"""

    val: "float | int | CompassPoint"
    unit: CompassUnit = "°"
    UNITS: ClassVar[tuple[CompassUnit]] = COMPASS_UNITS

    TURN: ClassVar[float] = 360.0
    """Full turn (360°)"""

    POINTS: ClassVar[tuple[CompassPoint]] = COMPASS_POINTS
    """Compass points."""

    RANGE: ClassVar[float] = TURN / len(POINTS)
    """Angle sector of a compass point"""

    def __post_init__(self):
        if isinstance(self.val, str):
            if self.val not in self.POINTS:
                raise ValueError(f"Invalid compass point: {self.val}")
            self.val = self.POINTS.index(self.val) * self.RANGE

        self.val = self.val % self.TURN
        self.unit = "°"

    def __str__(self):
        return self.l10n()

    def value(self, unit: CompassUnit):
        if unit == "Point" and isinstance(self.val, float):
            return self.point(self.val)
        if unit == "°":
            return self.val
        raise ValueError(f"unknown unit: {unit}")

    @classmethod
    def point(cls, azimuth: float | int) -> CompassPoint:
        """Returns the compass point to an azimuth value."""
        azimuth = azimuth % cls.TURN
        # The angle sector of a compass point starts 1/2 sector range before
        # and after compass point (example: "N" goes from -11.25° to +11.25°)
        azimuth = azimuth - cls.RANGE / 2
        idx = int(azimuth // cls.RANGE)
        return cls.POINTS[idx]

    def l10n(
        self,
        unit: CompassUnit = "Point",
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


WeatherConditionType = t.Literal[
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
    for c in t.get_args(WeatherConditionType):
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
