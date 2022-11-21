'''
searx is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

searx is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with searx. If not, see < http://www.gnu.org/licenses/ >.

(C) 2017- by Alexandre Flament, <alex@al-f.net>
'''


from typing import Optional, Union


class SearxException(Exception):
    pass


class SearxParameterException(SearxException):
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

    def __init__(self, suspended_time=None, message='Access denied'):
        suspended_time = suspended_time or self._get_default_suspended_time()
        super().__init__(message + ', suspended_time=' + str(suspended_time))
        self.suspended_time = suspended_time
        self.message = message

    def _get_default_suspended_time(self):
        from searx import get_setting

        return get_setting(self.SUSPEND_TIME_SETTING)


class SearxEngineCaptchaException(SearxEngineAccessDeniedException):
    """The website has returned a CAPTCHA

    By default, searx stops sending requests to this engine for 1 day.
    """

    SUSPEND_TIME_SETTING = "search.suspended_times.SearxEngineCaptcha"

    def __init__(self, suspended_time=None, message='CAPTCHA'):
        super().__init__(message=message, suspended_time=suspended_time)


class SearxEngineTooManyRequestsException(SearxEngineAccessDeniedException):
    """The website has returned a Too Many Request status code

    By default, searx stops sending requests to this engine for 1 hour.
    """

    SUSPEND_TIME_SETTING = "search.suspended_times.SearxEngineTooManyRequests"

    def __init__(self, suspended_time=None, message='Too many request'):
        super().__init__(message=message, suspended_time=suspended_time)


class SearxEngineXPathException(SearxEngineResponseException):
    """Error while getting the result of an XPath expression"""

    def __init__(self, xpath_spec, message):
        super().__init__(str(xpath_spec) + " " + message)
        self.message = message
        # str(xpath_spec) to deal with str and XPath instance
        self.xpath_str = str(xpath_spec)
