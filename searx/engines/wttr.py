# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""wttr.in (weather forecast service)"""

from json import loads
from urllib.parse import quote
from flask_babel import gettext

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


def get_weather_condition_key(lang):
    if lang == "en":
        return "weatherDesc"

    return "lang_" + lang.lower()


def generate_day_table(day):
    res = ""

    res += f"<tr><td>{gettext('Average temp.')}</td><td>{day['avgtempC']}°C / {day['avgtempF']}°F</td></tr>"
    res += f"<tr><td>{gettext('Min temp.')}</td><td>{day['mintempC']}°C / {day['mintempF']}°F</td></tr>"
    res += f"<tr><td>{gettext('Max temp.')}</td><td>{day['maxtempC']}°C / {day['maxtempF']}°F</td></tr>"
    res += f"<tr><td>{gettext('UV index')}</td><td>{day['uvIndex']}</td></tr>"
    res += f"<tr><td>{gettext('Sunrise')}</td><td>{day['astronomy'][0]['sunrise']}</td></tr>"
    res += f"<tr><td>{gettext('Sunset')}</td><td>{day['astronomy'][0]['sunset']}</td></tr>"

    return res


def generate_condition_table(condition, lang, current=False):
    res = ""

    if current:
        key = "temp_"
    else:
        key = "temp"

    res += (
        f"<tr><td><b>{gettext('Condition')}</b></td>"
        f"<td><b>{condition[get_weather_condition_key(lang)][0]['value']}</b></td></tr>"
    )
    res += (
        f"<tr><td><b>{gettext('Temperature')}</b></td>"
        f"<td><b>{condition[key+'C']}°C / {condition[key+'F']}°F</b></td></tr>"
    )
    res += (
        f"<tr><td>{gettext('Feels like')}</td><td>{condition['FeelsLikeC']}°C / {condition['FeelsLikeF']}°F</td></tr>"
    )
    res += (
        f"<tr><td>{gettext('Wind')}</td><td>{condition['winddir16Point']} — "
        f"{condition['windspeedKmph']} km/h / {condition['windspeedMiles']} mph</td></tr>"
    )
    res += (
        f"<tr><td>{gettext('Visibility')}</td><td>{condition['visibility']} km / {condition['visibilityMiles']} mi</td>"
    )
    res += f"<tr><td>{gettext('Humidity')}</td><td>{condition['humidity']}%</td></tr>"

    return res


def request(query, params):
    if query.replace('/', '') in [":help", ":bash.function", ":translation"]:
        return None

    if params["language"] == "all":
        params["language"] = "en"
    else:
        params["language"] = params["language"].split("-")[0]

    params["url"] = url.format(query=quote(query), lang=params["language"])

    params["raise_for_httperror"] = False

    return params


def response(resp):
    results = []

    if resp.status_code == 404:
        return []

    result = loads(resp.text)

    current = result["current_condition"][0]
    location = result['nearest_area'][0]

    forecast_indices = {3: gettext('Morning'), 4: gettext('Noon'), 6: gettext('Evening'), 7: gettext('Night')}

    title = f"{location['areaName'][0]['value']}, {location['region'][0]['value']}"

    infobox = f"<h3>{gettext('Current condition')}</h3><table><tbody>"

    infobox += generate_condition_table(current, resp.search_params['language'], True)

    infobox += "</tbody></table>"

    for day in result["weather"]:
        infobox += f"<h3>{day['date']}</h3>"

        infobox += "<table><tbody>"

        infobox += generate_day_table(day)

        infobox += "</tbody></table>"

        infobox += "<table><tbody>"

        for time in forecast_indices.items():
            infobox += f"<tr><td rowspan=\"7\"><b>{time[1]}</b></td></tr>"

            infobox += generate_condition_table(day['hourly'][time[0]], resp.search_params['language'])

        infobox += "</tbody></table>"

    results.append(
        {
            "infobox": title,
            "content": infobox,
        }
    )

    return results
