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

    def __init__(self, suspended_time=24 * 3600, message='Access denied'):
        super().__init__(message + ', suspended_time=' + str(suspended_time))
        self.suspended_time = suspended_time
        self.message = message


class SearxEngineCaptchaException(SearxEngineAccessDeniedException):
    """The website has returned a CAPTCHA

    By default, searx stops sending requests to this engine for 1 day.
    """

    def __init__(self, suspended_time=24 * 3600, message='CAPTCHA'):
        super().__init__(message=message, suspended_time=suspended_time)


class SearxEngineTooManyRequestsException(SearxEngineAccessDeniedException):
    """The website has returned a Too Many Request status code

    By default, searx stops sending requests to this engine for 1 hour.
    """

    def __init__(self, suspended_time=3600, message='Too many request'):
        super().__init__(message=message, suspended_time=suspended_time)


class SearxEngineXPathException(SearxEngineResponseException):
    """Error while getting the result of an XPath expression"""

    def __init__(self, xpath_spec, message):
        super().__init__(str(xpath_spec) + " " + message)
        self.message = message
        # str(xpath_spec) to deal with str and XPath instance
        self.xpath_str = str(xpath_spec)
