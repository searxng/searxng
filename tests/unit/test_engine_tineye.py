# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring

import logging
from datetime import datetime
from unittest.mock import Mock
from requests import HTTPError
from parameterized import parameterized

import searx.search
import searx.engines
from tests import SearxTestCase


class TinEyeTests(SearxTestCase):

    TEST_SETTINGS = "test_tineye.yml"

    def setUp(self):
        super().setUp()
        self.tineye = searx.engines.engines['tineye']
        self.tineye.logger.setLevel(logging.INFO)

    def tearDown(self):
        searx.search.load_engines([])

    def test_status_code_raises(self):
        response = Mock()
        response.status_code = 401
        response.raise_for_status.side_effect = HTTPError()
        self.assertRaises(HTTPError, lambda: self.tineye.response(response))

    @parameterized.expand([(400), (422)])
    def test_returns_empty_list(self, status_code):
        response = Mock()
        response.json.return_value = {"suggestions": {"key": "Download Error"}}
        response.status_code = status_code
        response.raise_for_status.side_effect = HTTPError()
        with self.assertLogs(self.tineye.logger):
            results = self.tineye.response(response)
            self.assertEqual(0, len(results))

    def test_logs_format_for_422(self):
        response = Mock()
        response.json.return_value = {"suggestions": {"key": "Invalid image URL"}}
        response.status_code = 422
        response.raise_for_status.side_effect = HTTPError()

        with self.assertLogs(self.tineye.logger) as assert_logs_context:
            self.tineye.response(response)
            self.assertIn(self.tineye.FORMAT_NOT_SUPPORTED, ','.join(assert_logs_context.output))

    def test_logs_signature_for_422(self):
        response = Mock()
        response.json.return_value = {"suggestions": {"key": "NO_SIGNATURE_ERROR"}}
        response.status_code = 422
        response.raise_for_status.side_effect = HTTPError()

        with self.assertLogs(self.tineye.logger) as assert_logs_context:
            self.tineye.response(response)
            self.assertIn(self.tineye.NO_SIGNATURE_ERROR, ','.join(assert_logs_context.output))

    def test_logs_download_for_422(self):
        response = Mock()
        response.json.return_value = {"suggestions": {"key": "Download Error"}}
        response.status_code = 422
        response.raise_for_status.side_effect = HTTPError()

        with self.assertLogs(self.tineye.logger) as assert_logs_context:
            self.tineye.response(response)
            self.assertIn(self.tineye.DOWNLOAD_ERROR, ','.join(assert_logs_context.output))

    def test_logs_description_for_400(self):
        description = 'There was a problem with that request. Error ID: ad5fc955-a934-43c1-8187-f9a61d301645'
        response = Mock()
        response.json.return_value = {"suggestions": {"description": [description], "title": "Oops! We're sorry!"}}
        response.status_code = 400
        response.raise_for_status.side_effect = HTTPError()

        with self.assertLogs(self.tineye.logger) as assert_logs_context:
            self.tineye.response(response)
            self.assertIn(description, ','.join(assert_logs_context.output))

    def test_crawl_date_parses(self):
        date_str = '2020-05-25'
        date = datetime.strptime(date_str, '%Y-%m-%d')
        response = Mock()
        response.json.return_value = {
            'matches': [
                {
                    'backlinks': [
                        {
                            'crawl_date': date_str,
                        }
                    ]
                }
            ]
        }
        response.status_code = 200
        results = self.tineye.response(response)
        self.assertEqual(date, results[0]['publishedDate'])
