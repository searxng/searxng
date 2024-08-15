from flask_babel import gettext
import requests
import re

name = "MOA Weather Data Plugin"
description = gettext("Displays weather data for a given location using the Open Meteo API, with improved formatting.")
default_on = True
preference_section = 'general'

query_re = re.compile(r'weather\s+(?:in\s+)?(.+)', re.IGNORECASE)

conditions = {
    99: {
        "name": gettext("Thunderstorm with heavy hail"),
        "emoji": "⛈️"
    },
    96: {
        "name": gettext("Thunderstorm with slight hail"),
        "emoji": "⛈️"
    },
    95: {
        "name": gettext("Thunderstorm"),
        "emoji": "🌩️"
    },
    86: {
        "name": gettext("Heavy snow showers"),
        "emoji": "🌧️"
    },
    85: {
        "name": gettext("Slight snow showers"),
        "emoji": "🌧️"
    },
    82: {
        "name": gettext("Violent rain showers"),
        "emoji": "🌧️"
    },
    81: {
        "name": gettext("Moderate rain showers"),
        "emoji": "🌧️"
    },
    80: {
        "name": gettext("Slight rain showers"),
        "emoji": "🌧️"
    },
    77: {
        "name": gettext("Snow grains"),
        "emoji": "🌨️"
    },
    75: {
        "name": gettext("Heavy snowfall"),
        "emoji": "🌨️"
    },
    73: {
        "name": gettext("Moderate snowfall"),
        "emoji": "🌨️"
    },
    71: {
        "name": gettext("Slight snowfall"),
        "emoji": "🌨️"
    },
    67: {
        "name": gettext("Heavy freezing rain"),
        "emoji": "🌧️"
    },
    66: {
        "name": gettext("Light freezing rain"),
        "emoji": "🌧️"
    },
    65: {
        "name": gettext("Heavy rain"),
        "emoji": "🌧️"
    },
    63: {
        "name": gettext("Moderate rain"),
        "emoji": "🌧️"
    },
    61: {
        "name": gettext("Slight rain"),
        "emoji": "🌧️"
    },
    57: {
        "name": gettext("Dense freezing drizzle"),
        "emoji": "🌧️"
    },
    56: {
        "name": gettext("Light freezing drizzle"),
        "emoji": "🌧️"
    },
    55: {
        "name": gettext("Dense drizzle"),
        "emoji": "🌧️"
    },
    53: {
        "name": gettext("Moderate drizzle"),
        "emoji": "🌧️"
    },
    51: {
        "name": gettext("Light drizzle"),
        "emoji": "🌧️"
    },
    48: {
        "name": gettext("Depositing rime fog"),
        "emoji": "🌫️"
    },
    45: {
        "name": gettext("Fog"),
        "emoji": "🌫️"
    },
    3: {
        "name": gettext("Overcast"),
        "emoji": "☁️"
    },
    2: {
        "name": gettext("Partly cloudy"),
        "emoji": "🌥️"
    },
    1: {
        "name": gettext("Mainly clear"),
        "emoji": "🌤️"
    },
    0: {
        "name": gettext("Clear"),
        "emoji": "☀️",
        "emoji_night": "🌙"
    }
}

def query_location(location_query):
    geocoding_url = f'https://nominatim.openstreetmap.org/search?format=json&q={location_query}'
    response = requests.get(geocoding_url).json()
    if response:
        lat = response[0]['lat']
        lon = response[0]['lon']
        return {
            'lat': lat,
            'lon': lon,
            'display_coords': gettext('%s °N, %s °E') % (lat, lon),
            'display_name': response[0]['display_name']
        }

    return None

def fetch_weather_data(lat, lon, params):
    weather_url = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}'
    if params:
        weather_url += f'&{params}'
    response = requests.get(weather_url).json()
    return response

def get_named_weather_condition(current_weather, with_emoji=False):
    for code, condition in conditions.items():
        if current_weather['weather_code'] >= code:
            condition = conditions[code]
            emoji = condition['emoji'] if current_weather.get('is_day', True) else condition.get('emoji_night', condition['emoji'])
            return f"{emoji} {condition['name']}" if with_emoji else condition['name']
    return gettext('Unknown')

def post_search(request, search):
    match = query_re.match(search.search_query.query)
    if not match:
        return True  # Continue with normal search if no match

    location_query = match.group(1)
    location = query_location(location_query)

    if not location:
        search.result_container.answers.clear()
        search.result_container.answers['weather_error'] = {'answer': gettext('Location not found or invalid coordinates format.')}
        return True

    weather_data = fetch_weather_data(location['lat'], location['lon'], 'current=weather_code,is_day,temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m')
    if 'current' in weather_data:
        current_weather = weather_data['current']
    else:
        search.result_container.answers.clear()
        search.result_container.answers['weather_error'] = {'answer': gettext('Weather data not available.')}
        return True

    search.result_container.answers.clear()
    search.result_container.answers['weather'] = {
        'title': gettext('Weather for %s') % f"{location['display_name']} ({location['display_coords']})",
        'fields': [
            {'label': gettext('Condition'), 'value': get_named_weather_condition(current_weather, with_emoji=True)},
            {'label': gettext('Temperature'), 'value': f"{current_weather['temperature_2m']}°C"},
            {'label': gettext('Wind Speed'), 'value': f"{current_weather['wind_speed_10m']}m/s"}
        ],
        'sources': [
            {'title': 'Open Meteo', 'url': 'https://open-meteo.com/'},
            {'title': 'OpenStreetMap', 'url': 'https://www.openstreetmap.org/'}
        ],
    }
    return True
