# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name

from unittest.mock import patch

from parameterized import parameterized

import searx
import searx.limiter

from tests import SearxTestCase


class TestLimiterBypassKey(SearxTestCase):

    @parameterized.expand(
        [
            ('disabled', False, 'secret', False),
            ('missing_header', 'secret', None, False),
            ('incorrect_key', 'secret', 'wrong!', False),
            ('correct_key', 'secret', 'secret', True),
        ]
    )
    def test_is_bypass_request(self, _name, bypass_key, request_key, expected):
        headers = {searx.limiter.BYPASS_HEADER: request_key} if request_key else {}

        with patch.dict(searx.settings['server'], {'limiter_bypass_key': bypass_key}):
            with self.app.test_request_context('/search', headers=headers) as ctx:
                self.assertEqual(searx.limiter.is_bypass_request(ctx.request), expected)

    def test_filter_request_bypasses_limiter(self):
        headers = {searx.limiter.BYPASS_HEADER: 'secret'}

        with patch.dict(searx.settings['server'], {'limiter_bypass_key': 'secret'}):
            with self.app.test_request_context('/search', headers=headers) as ctx:
                with patch.object(searx.limiter, 'get_cfg') as get_cfg:
                    self.assertIsNone(searx.limiter.filter_request(ctx.request))
                    get_cfg.assert_not_called()
