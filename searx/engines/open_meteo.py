# SPDX-License-Identifier: AGPL-3.0-or-later
"""Open Meteo (weather)"""

from urllib.parse import urlencode, quote_plus
from datetime import datetime
from flask_babel import gettext

from searx.network import get
from searx.exceptions import SearxEngineAPIException
from searx.result_types import EngineResults, Weather

about = {
    "website": 'https://open-meteo.com',
    "wikidata_id": None,
    "official_api_documentation": 'https://open-meteo.com/en/docs',
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["weather"]

geo_url = "https://geocoding-api.open-meteo.com"
api_url = "https://api.open-meteo.com"

data_of_interest = "temperature_2m,relative_humidity_2m,apparent_temperature,cloud_cover,pressure_msl,wind_speed_10m,wind_direction_10m"  # pylint: disable=line-too-long


def request(query, params):
    location_url = f"{geo_url}/v1/search?name={quote_plus(query)}"

    resp = get(location_url)
    if resp.status_code != 200:
        raise SearxEngineAPIException("invalid geo location response code")

    json_locations = resp.json().get("results", [])
    if len(json_locations) == 0:
        raise SearxEngineAPIException("location not found")

    location = json_locations[0]
    args = {
        'latitude': location['latitude'],
        'longitude': location['longitude'],
        'timeformat': 'unixtime',
        'format': 'json',
        'current': data_of_interest,
        'forecast_days': 7,
        'hourly': data_of_interest,
    }

    params['url'] = f"{api_url}/v1/forecast?{urlencode(args)}"
    params['location'] = location['name']

    return params


def c_to_f(temperature):
    return "%.2f" % ((temperature * 1.8) + 32)


def get_direction(degrees):
    if degrees < 45 or degrees >= 315:
        return "N"

    if 45 <= degrees < 135:
        return "O"

    if 135 <= degrees < 225:
        return "S"

    return "W"


def build_condition_string(data):
    if data['relative_humidity_2m'] > 50:
        return "rainy"

    if data['cloud_cover'] > 30:
        return 'cloudy'

    return 'clear sky'


def generate_weather_data(data):
    return Weather.DataItem(
        condition=build_condition_string(data),
        temperature=f"{data['temperature_2m']}°C / {c_to_f(data['temperature_2m'])}°F",
        feelsLike=f"{data['apparent_temperature']}°C / {c_to_f(data['apparent_temperature'])}°F",
        wind=(
            f"{get_direction(data['wind_direction_10m'])}, "
            f"{data['wind_direction_10m']}° — "
            f"{data['wind_speed_10m']} km/h"
        ),
        pressure=f"{data['pressure_msl']}hPa",
        humidity=f"{data['relative_humidity_2m']}hPa",
        attributes={gettext('Cloud cover'): f"{data['cloud_cover']}%"},
    )


def response(resp):
    res = EngineResults()
    json_data = resp.json()

    current_weather = generate_weather_data(json_data['current'])
    weather_answer = Weather(
        location=resp.search_params['location'],
        current=current_weather,
    )

    for index, time in enumerate(json_data['hourly']['time']):
        hourly_data = {}

        for key in data_of_interest.split(","):
            hourly_data[key] = json_data['hourly'][key][index]

        forecast_data = generate_weather_data(hourly_data)
        forecast_data.time = datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M')
        weather_answer.forecasts.append(forecast_data)

    res.add(weather_answer)
    return res
