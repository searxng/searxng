# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
DuckDuckGo Weather
~~~~~~~~~~~~~~~~~~
"""

from typing import TYPE_CHECKING
from json import loads
from urllib.parse import quote

from dateutil import parser as date_parser
from flask_babel import gettext

from searx.engines.duckduckgo import fetch_traits  # pylint: disable=unused-import
from searx.engines.duckduckgo import get_ddg_lang
from searx.enginelib.traits import EngineTraits

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

traits: EngineTraits


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
URL = "https://duckduckgo.com/js/spice/forecast/{query}/{lang}"


def generate_condition_table(condition):
    res = ""

    res += f"<tr><td><b>{gettext('Condition')}</b></td>" f"<td><b>{condition['conditionCode']}</b></td></tr>"

    res += (
        f"<tr><td><b>{gettext('Temperature')}</b></td>"
        f"<td><b>{condition['temperature']}°C / {c_to_f(condition['temperature'])}°F</b></td></tr>"
    )

    res += (
        f"<tr><td>{gettext('Feels like')}</td><td>{condition['temperatureApparent']}°C / "
        f"{c_to_f(condition['temperatureApparent'])}°F</td></tr>"
    )

    res += (
        f"<tr><td>{gettext('Wind')}</td><td>{condition['windDirection']}° — "
        f"{(condition['windSpeed'] * 1.6093440006147):.2f} km/h / {condition['windSpeed']} mph</td></tr>"
    )

    res += f"<tr><td>{gettext('Visibility')}</td><td>{condition['visibility']} m</td>"

    res += f"<tr><td>{gettext('Humidity')}</td><td>{(condition['humidity'] * 100):.1f}%</td></tr>"

    return res


def generate_day_table(day):
    res = ""

    res += (
        f"<tr><td>{gettext('Min temp.')}</td><td>{day['temperatureMin']}°C / "
        f"{c_to_f(day['temperatureMin'])}°F</td></tr>"
    )
    res += (
        f"<tr><td>{gettext('Max temp.')}</td><td>{day['temperatureMax']}°C / "
        f"{c_to_f(day['temperatureMax'])}°F</td></tr>"
    )
    res += f"<tr><td>{gettext('UV index')}</td><td>{day['maxUvIndex']}</td></tr>"
    res += f"<tr><td>{gettext('Sunrise')}</td><td>{date_parser.parse(day['sunrise']).strftime('%H:%M')}</td></tr>"
    res += f"<tr><td>{gettext('Sunset')}</td><td>{date_parser.parse(day['sunset']).strftime('%H:%M')}</td></tr>"

    return res


def request(query, params):

    eng_region = traits.get_region(params['searxng_locale'], traits.all_locale)
    eng_lang = get_ddg_lang(traits, params['searxng_locale'])

    # !ddw paris :es-AR --> {'ad': 'es_AR', 'ah': 'ar-es', 'l': 'ar-es'}
    params['cookies']['ad'] = eng_lang
    params['cookies']['ah'] = eng_region
    params['cookies']['l'] = eng_region
    logger.debug("cookies: %s", params['cookies'])

    params["url"] = URL.format(query=quote(query), lang=eng_lang.split('_')[0])
    return params


def c_to_f(temperature):
    return "%.2f" % ((temperature * 1.8) + 32)


def response(resp):
    results = []

    if resp.text.strip() == "ddg_spice_forecast();":
        return []

    result = loads(resp.text[resp.text.find('\n') + 1 : resp.text.rfind('\n') - 2])

    current = result["currentWeather"]

    title = result['location']

    infobox = f"<h3>{gettext('Current condition')}</h3><table><tbody>"

    infobox += generate_condition_table(current)

    infobox += "</tbody></table>"

    last_date = None

    for time in result['forecastHourly']['hours']:
        current_time = date_parser.parse(time['forecastStart'])

        if last_date != current_time.date():
            if last_date is not None:
                infobox += "</tbody></table>"

            infobox += f"<h3>{current_time.strftime('%Y-%m-%d')}</h3>"

            infobox += "<table><tbody>"

            for day in result['forecastDaily']['days']:
                if date_parser.parse(day['forecastStart']).date() == current_time.date():
                    infobox += generate_day_table(day)

            infobox += "</tbody></table><table><tbody>"

        last_date = current_time.date()

        infobox += f"<tr><td rowspan=\"7\"><b>{current_time.strftime('%H:%M')}</b></td></tr>"

        infobox += generate_condition_table(time)

    infobox += "</tbody></table>"

    results.append(
        {
            "infobox": title,
            "content": infobox,
        }
    )

    return results
