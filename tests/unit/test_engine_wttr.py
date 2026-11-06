# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring

from json import JSONDecodeError
from unittest.mock import Mock

import searx.plugins
import searx.preferences
from searx.extended_types import sxng_request
from searx.engines import wttr
from searx.result_types import WeatherAnswer
from tests import SearxTestCase


class WttrEngineTests(SearxTestCase):

    def setUp(self):
        super().setUp()
        self.storage = searx.plugins.PluginStorage()
        self.pref = searx.preferences.Preferences(["simple"], ["general"], {}, self.storage)
        self.pref.parse_dict({"locale": "en"})

    def _sample_weather_data(self, weather_code="113"):
        return {
            "current_condition": [
                {
                    "temp_C": "21",
                    "weatherCode": weather_code,
                    "FeelsLikeC": "22",
                    "winddirDegree": "180",
                    "windspeedKmph": "10",
                    "pressure": "1013",
                    "humidity": "65",
                    "cloudcover": "20",
                }
            ],
            "weather": [
                {
                    "date": "2026-11-06",
                    "hourly": [
                        {
                            "temp_C": "20",
                            "weatherCode": weather_code,
                            "FeelsLikeC": "20",
                            "winddirDegree": "190",
                            "windspeedKmph": "12",
                            "pressure": "1012",
                            "humidity": "70",
                            "cloudcover": "30",
                        }
                    ],
                }
            ],
        }

    def test_http_error_status(self):
        for status in (404, 500, 502, 503):
            resp = Mock(status_code=status)
            results = wttr.response(resp)
            self.assertEqual(len(results), 0)

    def test_json_decode_error(self):
        resp = Mock(status_code=200)
        resp.json.side_effect = JSONDecodeError("Expecting value", "doc", 0)
        results = wttr.response(resp)
        self.assertEqual(len(results), 0)

    def test_invalid_json_payload(self):
        for invalid_payload in [None, [], {}, {"current_condition": []}]:
            resp = Mock(status_code=200)
            resp.json.return_value = invalid_payload
            results = wttr.response(resp)
            self.assertEqual(len(results), 0)

    def test_weather_code_152(self):
        resp = Mock(status_code=200)
        resp.search_params = {"query": "Jakarta"}
        resp.json.return_value = self._sample_weather_data(weather_code="152")

        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            results = wttr.response(resp)
            self.assertEqual(len(results), 1)
            weather_answer = results[0]
            assert isinstance(weather_answer, WeatherAnswer)
            self.assertEqual(weather_answer.current.condition, "fog")
            self.assertEqual(weather_answer.forecasts[0].condition, "fog")

    def test_unknown_weather_code(self):
        resp = Mock(status_code=200)
        resp.search_params = {"query": "Jakarta"}
        resp.json.return_value = self._sample_weather_data(weather_code="999")

        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            results = wttr.response(resp)
            self.assertEqual(len(results), 1)
            weather_answer = results[0]
            assert isinstance(weather_answer, WeatherAnswer)
            self.assertEqual(weather_answer.current.condition, "fair")
            self.assertEqual(weather_answer.forecasts[0].condition, "fair")

    def test_valid_response(self):
        resp = Mock(status_code=200)
        resp.search_params = {"query": "London"}
        resp.json.return_value = self._sample_weather_data(weather_code="113")

        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            results = wttr.response(resp)
            self.assertEqual(len(results), 1)
            weather_answer = results[0]
            assert isinstance(weather_answer, WeatherAnswer)
            self.assertEqual(weather_answer.current.condition, "clear sky")
            self.assertEqual(len(weather_answer.forecasts), 1)
            self.assertEqual(weather_answer.forecasts[0].condition, "clear sky")
