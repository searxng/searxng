# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name

import json
import typing as t
from unittest.mock import MagicMock, patch

from searx import weather
from searx.engines import wttr
from searx.result_types import WeatherAnswer
from tests import SearxTestCase

GEO = weather.GeoLocation(
    name="Berlin",
    latitude=52.5,
    longitude=13.4,
    elevation=74.0,
    country_code="DE",
    timezone="Europe/Berlin",
)


def _response(status_code: int, payload=None, invalid_json: bool = False):
    resp = MagicMock()
    resp.status_code = status_code
    resp.search_params = {"query": "Berlin"}
    if invalid_json:
        resp.json.side_effect = json.JSONDecodeError("invalid", "", 0)
    else:
        resp.json.return_value = payload
    return resp


class TestWttr(SearxTestCase):

    def setUp(self):
        super().setUp()
        patcher = patch.object(weather.GeoLocation, "by_query", return_value=GEO)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_non_200_returns_empty(self):
        self.assertEqual(len(wttr.response(_response(500))), 0)

    def test_invalid_json_returns_empty(self):
        self.assertEqual(len(wttr.response(_response(200, invalid_json=True))), 0)

    def test_unknown_weather_code_does_not_raise(self):
        payload = {
            "current_condition": [
                {
                    "temp_C": "10",
                    "weatherCode": "152",
                    "FeelsLikeC": "9",
                    "winddirDegree": "180",
                    "windspeedKmph": "10",
                    "pressure": "1013",
                    "humidity": "80",
                    "cloudcover": "50",
                }
            ],
            "weather": [],
        }
        with (
            patch("searx.weather._get_sxng_locale_tag", return_value="en"),
            patch("searx.result_types.answer.gettext", side_effect=lambda s: s),
        ):
            res = wttr.response(_response(200, payload))
        self.assertEqual(len(res), 1)
        answer = t.cast(WeatherAnswer, res[0])
        self.assertEqual(answer.current.condition, "fog")
