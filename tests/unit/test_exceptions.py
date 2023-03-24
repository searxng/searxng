# SPDX-License-Identifier: AGPL-3.0-or-later

from tests import SearxTestCase
import searx.exceptions
from searx import get_setting


class TestExceptions(SearxTestCase):
    def test_default_suspend_time(self):
        with self.assertRaises(searx.exceptions.SearxEngineAccessDeniedException) as e:
            raise searx.exceptions.SearxEngineAccessDeniedException()
        self.assertEqual(
            e.exception.suspended_time,
            get_setting(searx.exceptions.SearxEngineAccessDeniedException.SUSPEND_TIME_SETTING),
        )

        with self.assertRaises(searx.exceptions.SearxEngineCaptchaException) as e:
            raise searx.exceptions.SearxEngineCaptchaException()
        self.assertEqual(
            e.exception.suspended_time, get_setting(searx.exceptions.SearxEngineCaptchaException.SUSPEND_TIME_SETTING)
        )

        with self.assertRaises(searx.exceptions.SearxEngineTooManyRequestsException) as e:
            raise searx.exceptions.SearxEngineTooManyRequestsException()
        self.assertEqual(
            e.exception.suspended_time,
            get_setting(searx.exceptions.SearxEngineTooManyRequestsException.SUSPEND_TIME_SETTING),
        )

    def test_custom_suspend_time(self):
        with self.assertRaises(searx.exceptions.SearxEngineAccessDeniedException) as e:
            raise searx.exceptions.SearxEngineAccessDeniedException(suspended_time=1337)
        self.assertEqual(e.exception.suspended_time, 1337)

        with self.assertRaises(searx.exceptions.SearxEngineCaptchaException) as e:
            raise searx.exceptions.SearxEngineCaptchaException(suspended_time=1409)
        self.assertEqual(e.exception.suspended_time, 1409)

        with self.assertRaises(searx.exceptions.SearxEngineTooManyRequestsException) as e:
            raise searx.exceptions.SearxEngineTooManyRequestsException(suspended_time=1543)
        self.assertEqual(e.exception.suspended_time, 1543)
