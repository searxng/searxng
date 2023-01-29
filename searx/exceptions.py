# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Exception types raised by SearXNG modules.
"""

from typing import Optional, Union


class SearxException(Exception):
    """Base SearXNG exception."""


class SearxParameterException(SearxException):
    """Raised when query miss a required paramater"""

    def __init__(self, name, value):
        if value == '' or value is None:
            message = 'Empty ' + name + ' parameter'
        else:
            message = 'Invalid value "' + value + '" for parameter ' + name
        super().__init__(message)
        self.message = message
        self.parameter_name = name
        self.parameter_value = value


class SearxSettingsException(SearxException):
    """Error while loading the settings"""

    def __init__(self, message: Union[str, Exception], filename: Optional[str]):
        super().__init__(message)
        self.message = message
        self.filename = filename


class SearxEngineException(SearxException):
    """Error inside an engine"""


class SearxXPathSyntaxException(SearxEngineException):
    """Syntax error in a XPATH"""

    def __init__(self, xpath_spec, message):
        super().__init__(str(xpath_spec) + " " + message)
        self.message = message
        # str(xpath_spec) to deal with str and XPath instance
        self.xpath_str = str(xpath_spec)


class SearxEngineResponseException(SearxEngineException):
    """Impossible to parse the result of an engine"""


class SearxEngineAPIException(SearxEngineResponseException):
    """The website has returned an application error"""


class SearxEngineAccessDeniedException(SearxEngineResponseException):
    """The website is blocking the access"""

    SUSPEND_TIME_SETTING = "search.suspended_times.SearxEngineAccessDenied"
    """This settings contains the default suspended time (default 86400 sec / 1
    day)."""

    def __init__(self, suspended_time: int = None, message: str = 'Access denied'):
        """Generic exception to raise when an engine denies access to the results.

        :param suspended_time: How long the engine is going to be suspended in
            second. Defaults to None.
        :type suspended_time: int, None
        :param message: Internal message.  Defaults to ``Access denied``
        :type message: str
        """
        suspended_time = suspended_time or self._get_default_suspended_time()
        super().__init__(message + ', suspended_time=' + str(suspended_time))
        self.suspended_time = suspended_time
        self.message = message

    def _get_default_suspended_time(self):
        from searx import get_setting  # pylint: disable=C0415

        return get_setting(self.SUSPEND_TIME_SETTING)


class SearxEngineCaptchaException(SearxEngineAccessDeniedException):
    """The website has returned a CAPTCHA."""

    SUSPEND_TIME_SETTING = "search.suspended_times.SearxEngineCaptcha"
    """This settings contains the default suspended time (default 86400 sec / 1
    day)."""

    def __init__(self, suspended_time=None, message='CAPTCHA'):
        super().__init__(message=message, suspended_time=suspended_time)


class SearxEngineTooManyRequestsException(SearxEngineAccessDeniedException):
    """The website has returned a Too Many Request status code

    By default, searx stops sending requests to this engine for 1 hour.
    """

    SUSPEND_TIME_SETTING = "search.suspended_times.SearxEngineTooManyRequests"
    """This settings contains the default suspended time (default 3660 sec / 1
    hour)."""

    def __init__(self, suspended_time=None, message='Too many request'):
        super().__init__(message=message, suspended_time=suspended_time)


class SearxEngineXPathException(SearxEngineResponseException):
    """Error while getting the result of an XPath expression"""

    def __init__(self, xpath_spec, message):
        super().__init__(str(xpath_spec) + " " + message)
        self.message = message
        # str(xpath_spec) to deal with str and XPath instance
        self.xpath_str = str(xpath_spec)
