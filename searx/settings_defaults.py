# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implementation of the default settings."""
from __future__ import annotations

import typing as t
import numbers
import errno
import os
import logging
from base64 import b64decode
from os.path import dirname, abspath

import msgspec

from typing_extensions import override
from .brand import SettingsBrand
from .sxng_locales import sxng_locales

searx_dir = abspath(dirname(__file__))

logger = logging.getLogger('searx')
OUTPUT_FORMATS = ['html', 'csv', 'json', 'rss']
SXNG_LOCALE_TAGS = ['all', 'auto'] + list(l[0] for l in sxng_locales)
SIMPLE_STYLE = ('auto', 'light', 'dark', 'black')
CATEGORIES_AS_TABS: dict[str, dict[str, t.Any]] = {
    'general': {},
    'images': {},
    'videos': {},
    'news': {},
    'map': {},
    'music': {},
    'it': {},
    'science': {},
    'files': {},
    'social media': {},
}
STR_TO_BOOL = {
    '0': False,
    'false': False,
    'off': False,
    '1': True,
    'true': True,
    'on': True,
}
_UNDEFINED = object()

# This type definition for SettingsValue.type_definition is incomplete, but it
# helps to significantly reduce the most common error messages regarding type
# annotations.
TypeDefinition: t.TypeAlias = (  # pylint: disable=invalid-name
    tuple[None, bool, type]
    | tuple[None, type, type]
    | tuple[None, type]
    | tuple[bool, type]
    | tuple[type, type]
    | tuple[type]
    | tuple[str | int, ...]
)

TypeDefinitionArg: t.TypeAlias = type | TypeDefinition  # pylint: disable=invalid-name


class SettingsValue:
    """Check and update a setting value"""

    def __init__(
        self,
        type_definition_arg: TypeDefinitionArg,
        default: t.Any = None,
        environ_name: str | None = None,
    ):
        self.type_definition: TypeDefinition = (
            type_definition_arg if isinstance(type_definition_arg, tuple) else (type_definition_arg,)
        )
        self.default: t.Any = default
        self.environ_name: str | None = environ_name

    @property
    def type_definition_repr(self):
        types_str = [td.__name__ if isinstance(td, type) else repr(td) for td in self.type_definition]
        return ', '.join(types_str)

    def check_type_definition(self, value: t.Any) -> None:
        if value in self.type_definition:
            return
        type_list = tuple(t for t in self.type_definition if isinstance(t, type))
        if not isinstance(value, type_list):
            raise ValueError('The value has to be one of these types/values: {}'.format(self.type_definition_repr))

    def __call__(self, value: t.Any) -> t.Any:
        if value == _UNDEFINED:
            value = self.default
        # override existing value with environ
        if self.environ_name and self.environ_name in os.environ:
            value = os.environ[self.environ_name]
            if self.type_definition == (bool,):
                value = STR_TO_BOOL[value.lower()]

        self.check_type_definition(value)
        return value


class SettingSublistValue(SettingsValue):
    """Check the value is a sublist of type definition."""

    @override
    def check_type_definition(self, value: list[t.Any]) -> None:
        if not isinstance(value, list):
            raise ValueError('The value has to a list')
        for item in value:
            if not item in self.type_definition[0]:
                raise ValueError('{} not in {}'.format(item, self.type_definition))


class SettingsDirectoryValue(SettingsValue):
    """Check and update a setting value that is a directory path"""

    @override
    def check_type_definition(self, value: t.Any) -> t.Any:
        super().check_type_definition(value)
        if not os.path.isdir(value):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), value)

    @override
    def __call__(self, value: t.Any) -> t.Any:
        if value == '':
            value = self.default
        return super().__call__(value)


class SettingsBytesValue(SettingsValue):
    """str are base64 decoded"""

    @override
    def __call__(self, value: t.Any) -> t.Any:
        if isinstance(value, str):
            value = b64decode(value)
        return super().__call__(value)


def apply_schema(settings: dict[str, t.Any], schema: dict[str, t.Any], path_list: list[str]):
    error = False
    for key, value in schema.items():
        if isinstance(value, type) and issubclass(value, msgspec.Struct):
            try:
                # Type Validation at runtime:
                # https://jcristharif.com/msgspec/structs.html#type-validation
                cfg_dict = settings.get(key)
                cfg_json = msgspec.json.encode(cfg_dict)
                settings[key] = msgspec.json.decode(cfg_json, type=value)
            except msgspec.ValidationError as e:
                # To get a more meaningful error message, we need to replace the
                # `$` by the (doted) name space.  For example if ValidationError
                # was raised for the field `name` in structure at `foo.bar`:
                #     Expected `str`, got `int` - at `$.name`
                # is converted to:
                #     Expected `str`, got `int` - at `foo.bar.name`
                msg = str(e)
                msg = msg.replace("`$.", "`" + ".".join([*path_list, key]) + ".")
                logger.error(msg)
                error = True
        elif isinstance(value, SettingsValue):
            try:
                settings[key] = value(settings.get(key, _UNDEFINED))
            except Exception as e:  # pylint: disable=broad-except
                # don't stop now: check other values
                msg = ".".join([*path_list, key]) + f": {e}"
                logger.error(msg)
                error = True
        elif isinstance(value, dict):
            error = error or apply_schema(settings.setdefault(key, {}), schema[key], [*path_list, key])
        else:
            settings.setdefault(key, value)
    if len(path_list) == 0 and error:
        raise ValueError("Invalid settings.yml")
    return error


SCHEMA: dict[str, t.Any] = {
    'general': {
        'debug': SettingsValue(bool, False, 'SEARXNG_DEBUG'),
        'instance_name': SettingsValue(str, 'SearXNG'),
        'privacypolicy_url': SettingsValue((None, False, str), None),
        'contact_url': SettingsValue((None, False, str), None),
        'donation_url': SettingsValue((bool, str), "https://docs.searxng.org/donate.html"),
        'enable_metrics': SettingsValue(bool, True),
        'open_metrics': SettingsValue(str, ''),
    },
    'brand': SettingsBrand,
    'search': {
        'safe_search': SettingsValue((0, 1, 2), 0),
        'autocomplete': SettingsValue(str, ''),
        'autocomplete_min': SettingsValue(int, 4),
        'favicon_resolver': SettingsValue(str, ''),
        'default_lang': SettingsValue(tuple(SXNG_LOCALE_TAGS + ['']), ''),
        'languages': SettingSublistValue(SXNG_LOCALE_TAGS, SXNG_LOCALE_TAGS),  # type: ignore
        'ban_time_on_fail': SettingsValue(numbers.Real, 5),
        'max_ban_time_on_fail': SettingsValue(numbers.Real, 120),
        'suspended_times': {
            'SearxEngineAccessDenied': SettingsValue(numbers.Real, 86400),
            'SearxEngineCaptcha': SettingsValue(numbers.Real, 86400),
            'SearxEngineTooManyRequests': SettingsValue(numbers.Real, 3600),
            'cf_SearxEngineCaptcha': SettingsValue(numbers.Real, 1296000),
            'cf_SearxEngineAccessDenied': SettingsValue(numbers.Real, 86400),
            'recaptcha_SearxEngineCaptcha': SettingsValue(numbers.Real, 604800),
        },
        'formats': SettingsValue(list, OUTPUT_FORMATS),
        'max_page': SettingsValue(int, 0),
    },
    'server': {
        'port': SettingsValue((int, str), 8888, 'SEARXNG_PORT'),
        'bind_address': SettingsValue(str, '127.0.0.1', 'SEARXNG_BIND_ADDRESS'),
        'limiter': SettingsValue(bool, False, 'SEARXNG_LIMITER'),
        'public_instance': SettingsValue(bool, False, 'SEARXNG_PUBLIC_INSTANCE'),
        'secret_key': SettingsValue(str, environ_name='SEARXNG_SECRET'),
        'base_url': SettingsValue((False, str), False, 'SEARXNG_BASE_URL'),
        'image_proxy': SettingsValue(bool, False, 'SEARXNG_IMAGE_PROXY'),
        'http_protocol_version': SettingsValue(('1.0', '1.1'), '1.0'),
        'method': SettingsValue(('POST', 'GET'), 'POST', 'SEARXNG_METHOD'),
        'default_http_headers': SettingsValue(dict, {}),
    },
    # redis is deprecated ..
    'redis': {
        'url': SettingsValue((None, False, str), False, 'SEARXNG_REDIS_URL'),
    },
    'valkey': {
        'url': SettingsValue((None, False, str), False, 'SEARXNG_VALKEY_URL'),
    },
    'ui': {
        'static_path': SettingsDirectoryValue(str, os.path.join(searx_dir, 'static')),
        'templates_path': SettingsDirectoryValue(str, os.path.join(searx_dir, 'templates')),
        'default_theme': SettingsValue(str, 'simple'),
        'default_locale': SettingsValue(str, ''),
        'theme_args': {
            'simple_style': SettingsValue(SIMPLE_STYLE, 'auto'),
        },
        'center_alignment': SettingsValue(bool, False),
        'results_on_new_tab': SettingsValue(bool, False),
        'advanced_search': SettingsValue(bool, False),
        'query_in_title': SettingsValue(bool, False),
        'cache_url': SettingsValue(str, 'https://web.archive.org/web/'),
        'search_on_category_select': SettingsValue(bool, True),
        'hotkeys': SettingsValue(('default', 'vim'), 'default'),
        'url_formatting': SettingsValue(('pretty', 'full', 'host'), 'pretty'),
    },
    'preferences': {
        'lock': SettingsValue(list, []),
    },
    'outgoing': {
        'useragent_suffix': SettingsValue(str, ''),
        'request_timeout': SettingsValue(numbers.Real, 3.0),
        'enable_http2': SettingsValue(bool, True),
        'verify': SettingsValue((bool, str), True),
        'max_request_timeout': SettingsValue((None, numbers.Real), None),
        'pool_connections': SettingsValue(int, 100),
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
        'networks': {},
    },
    'plugins': SettingsValue(dict, {}),
    'checker': {
        'off_when_debug': SettingsValue(bool, True, None),
        'scheduling': SettingsValue((None, dict), None, None),
    },
    'categories_as_tabs': SettingsValue(dict, CATEGORIES_AS_TABS),
    'engines': SettingsValue(list, []),
    'doi_resolvers': {},
}
