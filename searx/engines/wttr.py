# SPDX-License-Identifier: AGPL-3.0-or-later
"""wttr.in (weather forecast service)"""

from urllib.parse import quote
from datetime import datetime

from searx.result_types import EngineResults, WeatherAnswer
from searx import weather

about = {
    "website": "https://wttr.in",
    "wikidata_id": "Q107586666",
    "official_api_documentation": "https://github.com/chubin/wttr.in#json-output",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["weather"]

url = "https://wttr.in/{query}?format=j1&lang={lang}"

# adapted from https://github.com/chubin/wttr.in/blob/master/lib/constants.py
WWO_TO_CONDITION: dict[str, weather.WeatherConditionType] = {
    "113": "clear sky",
    "116": "partly cloudy",
    "119": "cloudy",
    "122": "fair",
    "143": "fair",
    "176": "light rain showers",
    "179": "light snow showers",
    "182": "light sleet showers",
    "185": "light sleet",
    "200": "rain and thunder",
    "227": "light snow",
    "230": "heavy snow",
    "248": "fog",
    "260": "fog",
    "263": "light rain showers",
    "266": "light rain showers",
    "281": "light sleet showers",
    "284": "light snow showers",
    "293": "light rain showers",
    "296": "light rain",
    "299": "rain showers",
    "302": "rain",
    "305": "heavy rain showers",
    "308": "heavy rain",
    "311": "light sleet",
    "314": "sleet",
    "317": "light sleet",
    "320": "heavy sleet",
    "323": "light snow showers",
    "326": "light snow showers",
    "329": "heavy snow showers",
    "332": "heavy snow",
    "335": "heavy snow showers",
    "338": "heavy snow",
    "350": "light sleet",
    "353": "light rain showers",
    "356": "heavy rain showers",
    "359": "heavy rain",
    "362": "light sleet showers",
    "365": "sleet showers",
    "368": "light snow showers",
    "371": "heavy snow showers",
    "374": "light sleet showers",
    "377": "heavy sleet",
    "386": "rain showers and thunder",
    "389": "heavy rain showers and thunder",
    "392": "snow showers and thunder",
    "395": "heavy snow showers",
}


def request(query, params):
    params["url"] = url.format(query=quote(query), lang=params["language"])
    params["raise_for_httperror"] = False

    return params


def _weather_data(location: weather.GeoLocation, data: dict):
    # the naming between different data objects is inconsitent, thus temp_C and
    # tempC are possible
    tempC: float = data.get("temp_C") or data.get("tempC")  # type: ignore

    return WeatherAnswer.Item(
        location=location,
        temperature=weather.Temperature(unit="°C", value=tempC),
        condition=WWO_TO_CONDITION[data["weatherCode"]],
        feels_like=weather.Temperature(unit="°C", value=data["FeelsLikeC"]),
        wind_from=weather.Compass(int(data["winddirDegree"])),
        wind_speed=weather.WindSpeed(data["windspeedKmph"], unit="km/h"),
        pressure=weather.Pressure(data["pressure"], unit="hPa"),
        humidity=weather.RelativeHumidity(data["humidity"]),
        cloud_cover=data["cloudcover"],
    )


def response(resp):
    res = EngineResults()

    if resp.status_code == 404:
        return res

    json_data = resp.json()
    geoloc = weather.GeoLocation.by_query(resp.search_params["query"])

    weather_answer = WeatherAnswer(
        current=_weather_data(geoloc, json_data["current_condition"][0]),
        service="wttr.in",
    )

    for day in json_data["weather"]:
        date = datetime.fromisoformat(day["date"])
        time_slot_len = 24 // len(day["hourly"])
        for index, forecast in enumerate(day["hourly"]):
            forecast_data = _weather_data(geoloc, forecast)
            forecast_data.datetime = weather.DateTime(date.replace(hour=index * time_slot_len + 1))
            weather_answer.forecasts.append(forecast_data)

    res.add(weather_answer)
    return res
