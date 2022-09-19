# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Model of weather and forecast data.  For more information about Climate and
Forecast (CF) visit:

- `NetCDF Climate and Forecast (CF) Metadata Conventions`_
- `Units of measure (CF)`_
- `CF Standard Name Table`_

.. _NetCDF Climate and Forecast (CF) Metadata Conventions:
    https://cfconventions.org/cf-conventions/cf-conventions.html
.. _Units of measure (CF):
    https://github.com/SciTools/cf-units
.. _CF Standard Name Table:
    https://cfconventions.org/Data/cf-standard-names/29/build/cf-standard-name-table.html

.. sidebar:: met.no API

   Example of a get_complete_ request to get weather data of Paris: `api.met.no
   (lat:48.86 lon:2.35)`_

The weather data types :py:obj:`WeatherInstantType`, :py:obj:`WeatherPeriodType`
and :py:obj:`WeatherSummaryType` are based on the types of the WeatherAPI_ from
the `Norwegian Meteorological Institute`_ (aka met.no).

.. _Norwegian Meteorological Institute: https://www.met.no/en
.. _WeatherAPI: https://api.met.no/doc/

.. _`api.met.no (lat:48.86 lon:2.35)`: https://api.met.no/weatherapi/locationforecast/2.0/complete?lat=48.86&lon=2.35
.. _get_complete: https://api.met.no/weatherapi/locationforecast/2.0#!/data/get_complete

.. admonition:: data model is still under construction

   This weather data model is in a very early stage.  Declare inheritance of
   weather data types and assemble a result type for a result item of a
   weather-engine needs far more experience.  We should not finish the model
   before we have more than one weather engine.

   In the mean time the weather return item is described in :ref:`engine weather
   media types`.


TypedDict declarations
----------------------

Declared data types for `dict` types returned by weather engines:

.. inheritance-diagram:: WeatherSummaryType
   :caption: Weather type that sums weather condition for a specific time period.

.. inheritance-diagram:: WeatherInstantType
   :caption: Type of weather data valid for a specific point in time.

.. inheritance-diagram:: WeatherPeriodType
   :caption: Type of weather data valid for a specific time period.

.. inheritance-diagram:: TemperatureType
   :caption: Type of thermodynamic temperature.


Classe definitions
------------------

.. inheritance-diagram:: WeatherSummary
   :caption: class of objects build from :py:class:`WeatherSummaryType`

"""
# pylint: disable=too-few-public-methods

from typing import Union
from typing_extensions import TypedDict, NotRequired


class TemperatureType(TypedDict):
    """Units of thermodynamic temperature.  A value of ``Null`` is equivalent to
    *unset*.
    """

    # pylint: disable=invalid-name

    K: NotRequired[Union[float, None]]
    """Temperature (unit Kelvin °K)"""

    C: NotRequired[Union[float, None]]
    """Temperature (unit Celsius °C)

    Unit (and scale) of temperature, with same magnitude as the Kelvin and a
    zero-point offset of 273.15
    """

    F: NotRequired[Union[float, None]]
    """Temperature (unit Fahrenheit °F)

    Unit of thermodynamic temperature (°R @ 459.67).
    """


class WeatherSummaryType(TypedDict):
    """Data type of a :py:obj:`WeatherSummary`"""

    symbol_code: str
    """A `list of symbols`_ is available from `Yr weather symbols`_

    .. _Yr weather symbols: https://nrkno.github.io/yr-weather-symbols/
    .. _list of symbols: https://api.met.no/weatherapi/weathericon/2.0/documentation#List_of_symbols
    """


class WeatherSummary:
    """A identifier that sums up the weather condition for *this* time period."""

    # https://api.met.no/weatherapi/weathericon/2.0/legends
    legend = {
        "clearsky": {
            "desc_en": "Clear sky",
            "variants": ["day", "night", "polartwilight"],
        },
        "cloudy": {"desc_en": "Cloudy", "variants": []},
        "fair": {
            "desc_en": "Fair",
            "variants": ["day", "night", "polartwilight"],
        },
        "fog": {"desc_en": "Fog", "variants": []},
        "heavyrain": {
            "desc_en": "Heavy rain",
            "variants": [],
        },
        "heavyrainandthunder": {
            "desc_en": "Heavy rain and thunder",
            "variants": [],
        },
        "heavyrainshowers": {
            "desc_en": "Heavy rain showers",
            "variants": ["day", "night", "polartwilight"],
        },
        "heavyrainshowersandthunder": {
            "desc_en": "Heavy rain showers and thunder",
            "variants": ["day", "night", "polartwilight"],
        },
        "heavysleet": {
            "desc_en": "Heavy sleet",
            "variants": [],
        },
        "heavysleetandthunder": {
            "desc_en": "Heavy sleet and thunder",
            "variants": [],
        },
        "heavysleetshowers": {
            "desc_en": "Heavy sleet showers",
            "variants": ["day", "night", "polartwilight"],
        },
        "heavysleetshowersandthunder": {
            "desc_en": "Heavy sleet showers and thunder",
            "variants": ["day", "night", "polartwilight"],
        },
        "heavysnow": {
            "desc_en": "Heavy snow",
            "variants": [],
        },
        "heavysnowandthunder": {
            "desc_en": "Heavy snow and thunder",
            "variants": [],
        },
        "heavysnowshowers": {
            "desc_en": "Heavy snow showers",
            "variants": ["day", "night", "polartwilight"],
        },
        "heavysnowshowersandthunder": {
            "desc_en": "Heavy snow showers and thunder",
            "variants": ["day", "night", "polartwilight"],
        },
        "lightrain": {
            "desc_en": "Light rain",
            "variants": [],
        },
        "lightrainandthunder": {
            "desc_en": "Light rain and thunder",
            "variants": [],
        },
        "lightrainshowers": {
            "desc_en": "Light rain showers",
            "variants": ["day", "night", "polartwilight"],
        },
        "lightrainshowersandthunder": {
            "desc_en": "Light rain showers and thunder",
            "variants": ["day", "night", "polartwilight"],
        },
        "lightsleet": {
            "desc_en": "Light sleet",
            "variants": [],
        },
        "lightsleetandthunder": {
            "desc_en": "Light sleet and thunder",
            "variants": [],
        },
        "lightsleetshowers": {
            "desc_en": "Light sleet showers",
            "variants": ["day", "night", "polartwilight"],
        },
        "lightsnow": {
            "desc_en": "Light snow",
            "variants": [],
        },
        "lightsnowandthunder": {
            "desc_en": "Light snow and thunder",
            "variants": [],
        },
        "lightsnowshowers": {
            "desc_en": "Light snow showers",
            "variants": ["day", "night", "polartwilight"],
        },
        "lightssleetshowersandthunder": {
            "desc_en": "Light sleet showers and thunder",
            "variants": ["day", "night", "polartwilight"],
        },
        "lightssnowshowersandthunder": {
            "desc_en": "Light snow showers and thunder",
            "variants": ["day", "night", "polartwilight"],
        },
        "partlycloudy": {
            "desc_en": "Partly cloudy",
            "variants": ["day", "night", "polartwilight"],
        },
        "rain": {"desc_en": "Rain", "variants": []},
        "rainandthunder": {
            "desc_en": "Rain and thunder",
            "variants": [],
        },
        "rainshowers": {
            "desc_en": "Rain showers",
            "variants": ["day", "night", "polartwilight"],
        },
        "rainshowersandthunder": {
            "desc_en": "Rain showers and thunder",
            "variants": ["day", "night", "polartwilight"],
        },
        "sleet": {"desc_en": "Sleet", "variants": []},
        "sleetandthunder": {
            "desc_en": "Sleet and thunder",
            "variants": [],
        },
        "sleetshowers": {
            "desc_en": "Sleet showers",
            "variants": ["day", "night", "polartwilight"],
        },
        "sleetshowersandthunder": {
            "desc_en": "Sleet showers and thunder",
            "variants": ["day", "night", "polartwilight"],
        },
        "snow": {"desc_en": "Snow", "variants": []},
        "snowandthunder": {
            "desc_en": "Snow and thunder",
            "variants": [],
        },
        "snowshowers": {
            "desc_en": "Snow showers",
            "variants": ["day", "night", "polartwilight"],
        },
        "snowshowersandthunder": {
            "desc_en": "Snow showers and thunder",
            "variants": ["day", "night", "polartwilight"],
        },
    }
    """Legend of the `Yr weather symbols`_.  The *key* is the name of the icon and
    the value is a dict with a legend and a list of variants of this icon.

    .. code::

       "clearsky": {
           "desc_en": "Clear sky",
           "variants": ["day", "night", "polartwilight"],
        },

    :meta hide-value:
    """

    def __init__(self, data: WeatherSummaryType):
        self.data = data


class WeatherInstantType(TypedDict):
    """Weather parameters valid for a specific point in time (in the instant case).
    A value of ``Null`` is equivalent to *unset*.
    """

    air_pressure_at_sea_level: NotRequired[Union[float, None]]
    """Air pressure at sea level (unit hPa)"""

    air_temperature: NotRequired[Union[TemperatureType, None]]
    """Air temperature at 2m above the ground"""

    air_temperature_percentile_10: NotRequired[Union[TemperatureType, None]]
    """10th percentile of air temperature (i.e 90% chance it will be above this
    value)"""

    air_temperature_percentile_90: NotRequired[Union[TemperatureType, None]]
    """90th percentile of air temperature (i.e 10% chance it will be above this
    value)"""

    cloud_area_fraction: NotRequired[Union[float, None]]
    """Amount of sky covered by clouds / total cloud cover for all heights
    (cloudiness, unit: %)"""

    cloud_area_fraction_high: NotRequired[Union[float, None]]
    """Amount of sky covered by clouds at high elevation / cloud cover higher than
    5000m above the ground (cloudiness, unit: %)"""

    cloud_area_fraction_low: NotRequired[Union[float, None]]
    """Amount of sky covered by clouds at low elevation / cloud cover lower than
    2000m above the ground (cloudiness, unit: %)"""

    cloud_area_fraction_medium: NotRequired[Union[float, None]]
    """Amount of sky covered by clouds at medium elevation / cloud cover between
    2000 and 5000m above the ground (cloudiness, unit: %)"""

    dew_point_temperature: NotRequired[Union[TemperatureType, None]]
    """Dew point temperature at sea level / dew point temperature 2m above the
    ground."""

    fog_area_fraction: NotRequired[Union[float, None]]
    """Amount of area covered by fog / amount of surrounding area covered in fog
    (horizontal view under a 1000 meters, unit: %)"""

    relative_humidity: NotRequired[Union[float, None]]
    """Amount of humidity in the air / relative humidity at 2m above the ground
    (unit: %))"""

    wind_from_direction: NotRequired[Union[float, None]]
    """The directon which moves towards / direction the wind is coming from (unit:
    degrees, 0° is north, 90° east, etc.)"""

    wind_speed: NotRequired[Union[float, None]]
    """Speed of wind / wind speed at 10m above the ground (10 min average, unit:
    m/s)"""

    wind_speed_of_gust: NotRequired[Union[float, None]]
    """Speed of wind gust / maximum gust for period at 10m above the ground. Gust is
    wind speed averaged over 3s."""

    wind_speed_percentile_10: NotRequired[Union[float, None]]
    """10th percentile of wind speed at 10m above the ground (10 min average, unit
    m/s)"""

    wind_speed_percentile_90: NotRequired[Union[float, None]]
    """90th percentile of wind speed at 10m above the ground (10 min average,
    unit m/s)"""


class WeatherPeriodType(TypedDict):
    """Weather parameters valid for a specified time period.  A value of ``Null`` is
    equivalent to *unset*.
    """

    air_temperature_max: NotRequired[Union[TemperatureType, None]]
    """Maximum air temperature in period."""

    air_temperature_min: NotRequired[Union[TemperatureType, None]]
    """Minimum air temperature in period."""

    precipitation_amount: NotRequired[Union[float, None]]
    """Best estimate for amount of precipitation for this period (unit: mm)."""

    precipitation_amount_max: NotRequired[Union[float, None]]
    """Maximum amount of precipitation for this period (unit: mm)."""

    precipitation_amount_min: NotRequired[Union[float, None]]
    """Minimum amount of precipitation for this period (unit: mm)."""

    probability_of_precipitation: NotRequired[Union[float, None]]
    """Probability of any precipitation coming for this period / chance of
    precipitation during period (unit: %)."""

    probability_of_thunder: NotRequired[Union[float, None]]
    """Probability of any thunder coming for this period / chance of thunder during
    period (unit: %)."""

    ultraviolet_index_clear_sky_max: NotRequired[Union[int, None]]
    """Maximum ultraviolet index if sky is clear / Index for cloud free conditions;
    0 (low) to 11+ (extreme)."""
