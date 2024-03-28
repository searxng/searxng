# SPDX-License-Identifier: AGPL-3.0-or-later
"""Open Meteo (weather)"""

from urllib.parse import urlencode, quote_plus
from datetime import datetime
from flask_babel import gettext

from searx.network import get
from searx.exceptions import SearxEngineAPIException

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


def generate_condition_table(condition):
    res = ""

    res += (
        f"<tr><td><b>{gettext('Temperature')}</b></td>"
        f"<td><b>{condition['temperature_2m']}°C / {c_to_f(condition['temperature_2m'])}°F</b></td></tr>"
    )

    res += (
        f"<tr><td>{gettext('Feels like')}</td><td>{condition['apparent_temperature']}°C / "
        f"{c_to_f(condition['apparent_temperature'])}°F</td></tr>"
    )

    res += (
        f"<tr><td>{gettext('Wind')}</td><td>{get_direction(condition['wind_direction_10m'])}, "
        f"{condition['wind_direction_10m']}° — "
        f"{condition['wind_speed_10m']} km/h</td></tr>"
    )

    res += f"<tr><td>{gettext('Cloud cover')}</td><td>{condition['cloud_cover']}%</td>"

    res += f"<tr><td>{gettext('Humidity')}</td><td>{condition['relative_humidity_2m']}%</td></tr>"

    res += f"<tr><td>{gettext('Pressure')}</td><td>{condition['pressure_msl']}hPa</td></tr>"

    return res


def response(resp):
    data = resp.json()

    table_content = generate_condition_table(data['current'])

    infobox = f"<table><tbody>{table_content}</tbody></table>"

    for index, time in enumerate(data['hourly']['time']):
        hourly_data = {}

        for key in data_of_interest.split(","):
            hourly_data[key] = data['hourly'][key][index]

        table_content = generate_condition_table(hourly_data)

        infobox += f"<h3>{datetime.utcfromtimestamp(time).strftime('%Y-%m-%d %H:%M')}</h3>"
        infobox += f"<table><tbody>{table_content}</tbody></table>"

    return [{'infobox': 'Open Meteo', 'content': infobox}]
