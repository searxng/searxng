# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-function-docstring
"""Implementation of the default settings.

"""

import typing
import numbers
import errno
import os
import logging
from os.path import dirname, abspath

from searx.languages import language_codes as languages

searx_dir = abspath(dirname(__file__))

logger = logging.getLogger('searx')
OUTPUT_FORMATS = ['html', 'csv', 'json', 'rss']
LANGUAGE_CODES = ('', 'all') + tuple(l[0] for l in languages)
OSCAR_STYLE = ('logicodev', 'logicodev-dark', 'pointhi')
CATEGORY_ORDER = [
    'general',
    'images',
    'videos',
    'news',
    'map',
    'music',
    'it',
    'science',
    'files',
    'social media',
]
STR_TO_BOOL = {
    '0': False,
    'false': False,
    'off': False,
    '1': True,
    'true': True,
    'on': True,
}
_UNDEFINED = object()


class SettingsValue:
    """Check and update a setting value
    """

    def __init__(self,
                 type_definition: typing.Union[None, typing.Any, typing.Tuple[typing.Any]]=None,
                 default: typing.Any=None,
                 environ_name: str=None):
        self.type_definition = (
            type_definition
            if type_definition is None or isinstance(type_definition, tuple)
            else (type_definition,)
        )
        self.default = default
        self.environ_name = environ_name

    @property
    def type_definition_repr(self):
        types_str = [
            t.__name__ if isinstance(t, type) else repr(t)
            for t in self.type_definition
        ]
        return ', '.join(types_str)

    def check_type_definition(self, value: typing.Any) -> None:
        if value in self.type_definition:
            return
        type_list = tuple(t for t in self.type_definition if isinstance(t, type))
        if not isinstance(value, type_list):
            raise ValueError(
                'The value has to be one of these types/values: {}'.format(
                    self.type_definition_repr))

    def __call__(self, value: typing.Any) -> typing.Any:
        if value == _UNDEFINED:
            value = self.default
        # override existing value with environ
        if self.environ_name and self.environ_name in os.environ:
            value = os.environ[self.environ_name]
            if self.type_definition == (bool,):
                value = STR_TO_BOOL[value.lower()]

        self.check_type_definition(value)
        return value


class SettingsDirectoryValue(SettingsValue):
    """Check and update a setting value that is a directory path
    """

    def check_type_definition(self, value: typing.Any) -> typing.Any:
        super().check_type_definition(value)
        if not os.path.isdir(value):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), value)

    def __call__(self, value: typing.Any) -> typing.Any:
        if value == '':
            value = self.default
        return super().__call__(value)


def apply_schema(settings, schema, path_list):
    error = False
    for key, value in schema.items():
        if isinstance(value, SettingsValue):
            try:
                settings[key] = value(settings.get(key, _UNDEFINED))
            except Exception as e:  # pylint: disable=broad-except
                # don't stop now: check other values
                logger.error('%s: %s', '.'.join([*path_list, key]), e)
                error = True
        elif isinstance(value, dict):
            error = error or apply_schema(settings.setdefault(key, {}), schema[key], [*path_list, key])
        else:
            settings.setdefault(key, value)
    if len(path_list) == 0 and error:
        raise ValueError('Invalid settings.yml')
    return error


SCHEMA = {
    'general': {
        'debug': SettingsValue(bool, False, 'SEARX_DEBUG'),
        'instance_name': SettingsValue(str, 'searxng'),
        'contact_url': SettingsValue((None, False, str), None),
    },
    'brand': {
        'issue_url': SettingsValue(str, None),
        'new_issue_url': SettingsValue(str, None),
        'docs_url': SettingsValue(str, None),
        'public_instances': SettingsValue(str, None),
        'wiki_url': SettingsValue(str, None),
    },
    'search': {
        'safe_search': SettingsValue((0,1,2), 0),
        'autocomplete': SettingsValue(str, ''),
        'default_lang': SettingsValue(LANGUAGE_CODES, ''),
        'ban_time_on_fail': SettingsValue(numbers.Real, 5),
        'max_ban_time_on_fail': SettingsValue(numbers.Real, 120),
        'formats': SettingsValue(list, OUTPUT_FORMATS),
    },
    'server': {
        'port': SettingsValue((int,str), 8888, 'SEARX_PORT'),
        'bind_address': SettingsValue(str, '127.0.0.1', 'SEARX_BIND_ADDRESS'),
        'secret_key': SettingsValue(str, environ_name='SEARX_SECRET'),
        'base_url': SettingsValue((False, str), False),
        'image_proxy': SettingsValue(bool, False),
        'http_protocol_version': SettingsValue(('1.0', '1.1'), '1.0'),
        'method': SettingsValue(('POST', 'GET'), 'POST'),
        'default_http_headers': SettingsValue(dict, {}),
    },
    'ui': {
        'static_path': SettingsDirectoryValue(str, os.path.join(searx_dir, 'static')),
        'templates_path': SettingsDirectoryValue(str, os.path.join(searx_dir, 'templates')),
        'default_theme': SettingsValue(str, 'oscar'),
        'default_locale': SettingsValue(str, ''),
        'theme_args': {
            'oscar_style': SettingsValue(OSCAR_STYLE, 'logicodev'),
        },
        'results_on_new_tab': SettingsValue(bool, False),
        'advanced_search': SettingsValue(bool, False),
        'categories_order': SettingsValue(list, CATEGORY_ORDER),
    },
    'preferences': {
        'lock': SettingsValue(list, []),
    },
    'outgoing': {
        'useragent_suffix': SettingsValue(str, ''),
        'request_timeout': SettingsValue(numbers.Real, 3.0),
        'enable_http2': SettingsValue(bool, True),
        'max_request_timeout': SettingsValue((None, numbers.Real), None),
        # Magic number kept from previous code
        'pool_connections': SettingsValue(int, 100),
        # Picked from constructor
        'pool_maxsize': SettingsValue(int, 10),
        'keepalive_expiry': SettingsValue(numbers.Real, 5.0),
        # default maximum redirect
        # from https://github.com/psf/requests/blob/8c211a96cdbe9fe320d63d9e1ae15c5c07e179f8/requests/models.py#L55
        'max_redirects': SettingsValue(int, 30),
        'retries': SettingsValue(int, 0),
        'proxies': SettingsValue((None, str, dict), None),
        'source_ips': SettingsValue((None, str, list), None),
        # Tor configuration
        'using_tor_proxy': SettingsValue(bool, False),
        'extra_proxy_timeout': SettingsValue(int, 0),
        'networks': {
        },
    },
    'plugins': SettingsValue((None, list), None),
    'enabled_plugins': SettingsValue(list, []),
    'checker': {
        'off_when_debug': SettingsValue(bool, True),
    },
    'engines': SettingsValue(list, []),
    'doi_resolvers': {
    },
}

def settings_set_defaults(settings):
    apply_schema(settings, SCHEMA, [])
    return settings
