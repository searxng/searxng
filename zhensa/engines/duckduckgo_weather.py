# SPDX-License-Identifier: AGPL-3.0-or-later
"""
DuckDuckGo Weather
~~~~~~~~~~~~~~~~~~
"""

import typing as t
from json import loads
from urllib.parse import quote

from dateutil import parser as date_parser

from zhensa.engines.duckduckgo import fetch_traits  # pylint: disable=unused-import
from zhensa.engines.duckduckgo import get_ddg_lang

from zhensa.result_types import EngineResults
from zhensa.extended_types import SXNG_Response
from zhensa import weather


about = {
    "website": 'https://duckduckgo.com/',
    "wikidata_id": 'Q12805',
    "official_api_documentation": None,
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

send_accept_language_header = True

# engine dependent config
categories = ["weather"]
base_url = "https://duckduckgo.com/js/spice/forecast/{query}/{lang}"

# adapted from https://gist.github.com/mikesprague/048a93b832e2862050356ca233ef4dc1
WEATHERKIT_TO_CONDITION: dict[str, weather.WeatherConditionType] = {
    "BlowingDust": "fog",
    "Clear": "clear sky",
    "Cloudy": "cloudy",
    "Foggy": "fog",
    "Haze": "fog",
    "MostlyClear": "clear sky",
    "MostlyCloudy": "partly cloudy",
    "PartlyCloudy": "partly cloudy",
    "Smoky": "fog",
    "Breezy": "partly cloudy",
    "Windy": "partly cloudy",
    "Drizzle": "light rain",
    "HeavyRain": "heavy rain",
    "IsolatedThunderstorms": "rain and thunder",
    "Rain": "rain",
    "SunShowers": "rain",
    "ScatteredThunderstorms": "heavy rain and thunder",
    "StrongStorms": "heavy rain and thunder",
    "Thunderstorms": "rain and thunder",
    "Frigid": "clear sky",
    "Hail": "heavy rain",
    "Hot": "clear sky",
    "Flurries": "light snow",
    "Sleet": "sleet",
    "Snow": "light snow",
    "SunFlurries": "light snow",
    "WintryMix": "sleet",
    "Blizzard": "heavy snow",
    "BlowingSnow": "heavy snow",
    "FreezingDrizzle": "light sleet",
    "FreezingRain": "sleet",
    "HeavySnow": "heavy snow",
    "Hurricane": "rain and thunder",
    "TropicalStorm": "rain and thunder",
}


def _weather_data(location: weather.GeoLocation, data: dict[str, t.Any]):

    return EngineResults.types.WeatherAnswer.Item(
        location=location,
        temperature=weather.Temperature(unit="°C", value=data['temperature']),
        condition=WEATHERKIT_TO_CONDITION[data["conditionCode"]],
        feels_like=weather.Temperature(unit="°C", value=data['temperatureApparent']),
        wind_from=weather.Compass(data["windDirection"]),
        wind_speed=weather.WindSpeed(data["windSpeed"], unit="mi/h"),
        pressure=weather.Pressure(data["pressure"], unit="hPa"),
        humidity=weather.RelativeHumidity(data["humidity"] * 100),
        cloud_cover=data["cloudCover"] * 100,
    )


def request(query: str, params: dict[str, t.Any]):

    eng_region = traits.get_region(params['zhensa_locale'], traits.all_locale)
    eng_lang = get_ddg_lang(traits, params['zhensa_locale'])

    # !ddw paris :es-AR --> {'ad': 'es_AR', 'ah': 'ar-es', 'l': 'ar-es'}
    params['cookies']['ad'] = eng_lang
    params['cookies']['ah'] = eng_region
    params['cookies']['l'] = eng_region
    logger.debug("cookies: %s", params['cookies'])

    params["url"] = base_url.format(query=quote(query), lang=eng_lang.split('_')[0])
    return params


def response(resp: SXNG_Response):
    res = EngineResults()

    if resp.text.strip() == "ddg_spice_forecast();":
        return res

    json_data = loads(resp.text[resp.text.find('\n') + 1 : resp.text.rfind('\n') - 2])

    geoloc = weather.GeoLocation.by_query(resp.search_params["query"])

    weather_answer = EngineResults.types.WeatherAnswer(
        current=_weather_data(geoloc, json_data["currentWeather"]),
        service="duckduckgo weather",
    )

    for forecast in json_data['forecastHourly']['hours']:
        forecast_time = date_parser.parse(forecast['forecastStart'])
        forecast_data = _weather_data(geoloc, forecast)
        forecast_data.datetime = weather.DateTime(forecast_time)
        weather_answer.forecasts.append(forecast_data)

    res.add(weather_answer)
    return res
