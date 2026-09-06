# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring

from searx.engines import braveapi
from searx.search.processors import OnlineParams
from searx.search.processors.online import default_request_params
from tests import SearxTestCase


class BraveAPITests(SearxTestCase):

    def test_request_headers(self):
        self.setattr4test(braveapi, 'api_key', 'test-api-key')
        for headers in ({}, {'Accept': 'text/html,application/xhtml+xml'}):
            with self.subTest(headers=headers):
                params: OnlineParams = {
                    **default_request_params(),
                    'query': 'test query',
                    'category': 'general',
                    'pageno': 1,
                    'time_range': None,
                    'safesearch': 0,
                    'engine_data': {},
                    'searxng_locale': 'all',
                    'headers': headers,
                }

                braveapi.request('test query', params)

                self.assertEqual(params['headers']['X-Subscription-Token'], 'test-api-key')
                self.assertEqual(params['headers']['Accept'], 'application/json')
