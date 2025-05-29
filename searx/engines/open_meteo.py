# SPDX-License-Identifier: AGPL-3.0-or-later
"""Open Meteo (weather)"""

from urllib.parse import urlencode
from datetime import datetime

from searx.result_types import EngineResults, WeatherAnswer
from searx import weather


about = {
    "website": "https://open-meteo.com",
    "wikidata_id": None,
    "official_api_documentation": "https://open-meteo.com/en/docs",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["weather"]

geo_url = "https://geocoding-api.open-meteo.com"
api_url = "https://api.open-meteo.com"

data_of_interest = (
    "temperature_2m",
    "apparent_temperature",
    "relative_humidity_2m",
    "apparent_temperature",
    "cloud_cover",
    "pressure_msl",
    "wind_speed_10m",
    "wind_direction_10m",
    "weather_code",
    # "visibility",
    # "is_day",
)


def request(query, params):

    try:
        location = weather.GeoLocation.by_query(query)
    except ValueError:
        return

    args = {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "timeformat": "unixtime",
        "timezone": "auto",  # use timezone of the location
        "format": "json",
        "current": ",".join(data_of_interest),
        "forecast_days": 3,
        "hourly": ",".join(data_of_interest),
    }

    params["url"] = f"{api_url}/v1/forecast?{urlencode(args)}"


# https://open-meteo.com/en/docs#weather_variable_documentation
# https://nrkno.github.io/yr-weather-symbols/

WMO_TO_CONDITION: dict[int, weather.WeatherConditionType] = {
    # 0	Clear sky
    0: "clear sky",
    # 1, 2, 3     Mainly clear, partly cloudy, and overcast
    1: "fair",
    2: "partly cloudy",
    3: "cloudy",
    # 45, 48      Fog and depositing rime fog
    45: "fog",
    48: "fog",
    # 51, 53, 55  Drizzle: Light, moderate, and dense intensity
    51: "light rain",
    53: "light rain",
    55: "light rain",
    # 56, 57      Freezing Drizzle: Light and dense intensity
    56: "light sleet showers",
    57: "light sleet",
    # 61, 63, 65  Rain: Slight, moderate and heavy intensity
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    # 66, 67    Freezing Rain: Light and heavy intensity
    66: "light sleet showers",
    67: "light sleet",
    # 71, 73, 75  Snow fall: Slight, moderate, and heavy intensity
    71: "light sleet",
    73: "sleet",
    75: "heavy sleet",
    # 77    Snow grains
    77: "snow",
    # 80, 81, 82  Rain showers: Slight, moderate, and violent
    80: "light rain showers",
    81: "rain showers",
    82: "heavy rain showers",
    # 85, 86      Snow showers slight and heavy
    85: "snow showers",
    86: "heavy snow showers",
    # 95          Thunderstorm: Slight or moderate
    95: "rain and thunder",
    # 96, 99      Thunderstorm with slight and heavy hail
    96: "light snow and thunder",
    99: "heavy snow and thunder",
}


def _weather_data(location: weather.GeoLocation, data: dict):

    return WeatherAnswer.Item(
        location=location,
        temperature=weather.Temperature(unit="°C", value=data["temperature_2m"]),
        condition=WMO_TO_CONDITION[data["weather_code"]],
        feels_like=weather.Temperature(unit="°C", value=data["apparent_temperature"]),
        wind_from=weather.Compass(data["wind_direction_10m"]),
        wind_speed=weather.WindSpeed(data["wind_speed_10m"], unit="km/h"),
        pressure=weather.Pressure(data["pressure_msl"], unit="hPa"),
        humidity=weather.RelativeHumidity(data["relative_humidity_2m"]),
        cloud_cover=data["cloud_cover"],
    )


def response(resp):
    location = weather.GeoLocation.by_query(resp.search_params["query"])

    res = EngineResults()
    json_data = resp.json()

    weather_answer = WeatherAnswer(
        current=_weather_data(location, json_data["current"]),
        service="Open-meteo",
        # url="https://open-meteo.com/en/docs",
    )

    for index, time in enumerate(json_data["hourly"]["time"]):

        if time < json_data["current"]["time"]:
            # Cut off the hours that are already in the past
            continue

        hourly_data = {}
        for key in data_of_interest:
            hourly_data[key] = json_data["hourly"][key][index]

        forecast_data = _weather_data(location, hourly_data)
        forecast_data.datetime = weather.DateTime(datetime.fromtimestamp(time))
        weather_answer.forecasts.append(forecast_data)

    res.add(weather_answer)
    return res
