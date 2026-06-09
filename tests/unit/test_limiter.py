# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name

import searx
import searx.limiter

from tests import SearxTestCase


class TestLimiterBypassKey(SearxTestCase):

    def setUp(self):
        super().setUp()
        self.previous_bypass_key = searx.settings['server']['limiter_bypass_key']
        self.addCleanup(self._restore_bypass_key)

    def _restore_bypass_key(self):
        searx.settings['server']['limiter_bypass_key'] = self.previous_bypass_key

    def test_is_bypass_request(self):
        searx.settings['server']['limiter_bypass_key'] = 'test-bypass-key'

        with self.app.test_request_context(
            '/search',
            headers={searx.limiter.BYPASS_HEADER: 'test-bypass-key'},
        ) as ctx:
            self.assertTrue(searx.limiter.is_bypass_request(ctx.request))

    def test_filter_request_bypasses_bot_detection(self):
        searx.settings['server']['limiter_bypass_key'] = 'test-bypass-key'

        headers = {
            'Accept': '*/*',
            'User-Agent': 'curl/8.0.0',
            searx.limiter.BYPASS_HEADER: 'test-bypass-key',
        }

        with self.app.test_request_context('/search', headers=headers) as ctx:
            self.assertIsNone(searx.limiter.filter_request(ctx.request))

    def test_filter_request_rejects_invalid_bypass_key(self):
        searx.settings['server']['limiter_bypass_key'] = 'test-bypass-key'

        headers = {
            'Accept': '*/*',
            'User-Agent': 'curl/8.0.0',
            searx.limiter.BYPASS_HEADER: 'wrong-key',
        }

        with self.app.test_request_context('/search', headers=headers) as ctx:
            response = searx.limiter.filter_request(ctx.request)
            self.assertIsNotNone(response)
            self.assertEqual(response.status_code, 429)
