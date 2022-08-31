# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""DuckDuckGo Weather"""

from json import loads
from urllib.parse import quote

from datetime import datetime

about = {
    "website": 'https://duckduckgo.com/',
    "wikidata_id": 'Q12805',
    "official_api_documentation": None,
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["weather"]

url = "https://duckduckgo.com/js/spice/forecast/{query}/{lang}"


def request(query, params):
    params["url"] = url.format(query=quote(query), lang=params['language'].split('-')[0])

    return params


def f_to_c(temperature):
    return "%.2f" % ((temperature - 32) / 1.8)


def response(resp):
    results = []

    if resp.text.strip() == "ddg_spice_forecast();":
        return []

    result = loads(resp.text[resp.text.find('{') : resp.text.rfind('}') + 1])

    current = result["currently"]

    forecast_data = []
    last_date = None
    current_data = {}

    for time in result['hourly']['data']:
        current_time = datetime.fromtimestamp(time['time'])

        if last_date != current_time.date():
            if last_date is not None:
                forecast_data.append(current_data)

            today = next(
                day
                for day in result['daily']['data']
                if datetime.fromtimestamp(day['time']).date() == current_time.date()
            )

            current_data = {
                'date': current_time.strftime('%Y-%m-%d'),
                'metric': {
                    'min_temp': f_to_c(today['temperatureLow']),
                    'max_temp': f_to_c(today['temperatureHigh']),
                },
                'uv_index': today['uvIndex'],
                'sunrise': datetime.fromtimestamp(today['sunriseTime']).strftime('%H:%M'),
                'sunset': datetime.fromtimestamp(today['sunsetTime']).strftime('%H:%M'),
                'forecast': [],
            }

        current_data['forecast'].append(
            {
                'time': current_time.strftime('%H:%M'),
                'metric': {
                    'temperature': f_to_c(time['temperature']),
                    'feels_like': f_to_c(time['apparentTemperature']),
                    'wind_speed': '%.2f' % (time['windSpeed'] * 1.6093440006147),
                    'visibility': time['visibility'],
                },
                'imperial': {
                    'temperature': time['temperature'],
                    'feels_like': time['apparentTemperature'],
                    'wind_speed': time['windSpeed'],
                },
                'condition': time['summary'],
                'wind_direction': time['windBearing'],
                'humidity': time['humidity'] * 100,
            }
        )

        last_date = current_time.date()

    forecast_data.append(current_data)

    results.append(
        {
            'template': 'weather.html',
            'location': result['flags']['ddg-location'],
            'currently': {
                'metric': {
                    'temperature': f_to_c(current['temperature']),
                    'feels_like': f_to_c(current['apparentTemperature']),
                    'wind_speed': '%.2f' % (current['windSpeed'] * 1.6093440006147),
                    'visibility': current['visibility'],
                },
                'imperial': {
                    'temperature': current['temperature'],
                    'feels_like': current['apparentTemperature'],
                    'wind_speed': current['windSpeed'],
                },
                'condition': current['summary'],
                'wind_direction': current['windBearing'],
                'humidity': current['humidity'] * 100,
            },
            'forecast': forecast_data,
        }
    )

    return results
