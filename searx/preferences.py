# SPDX-License-Identifier: AGPL-3.0-or-later
"""Searx preferences implementation."""

# pylint: disable=useless-object-inheritance

import typing as t

from base64 import urlsafe_b64encode, urlsafe_b64decode
from zlib import compress, decompress
from urllib.parse import parse_qs, urlencode
from collections import OrderedDict
from collections.abc import Iterable

import flask
import babel
import babel.core

import searx.plugins

from searx import settings, autocomplete, favicons
from searx.enginelib import Engine
from searx.engines import DEFAULT_CATEGORY
from searx.extended_types import SXNG_Request
from searx.locales import LOCALE_NAMES
from searx.webutils import VALID_LANGUAGE_CODE


COOKIE_MAX_AGE = 60 * 60 * 24 * 365 * 5  # 5 years
DOI_RESOLVERS = list(settings['doi_resolvers'])

MAP_STR2BOOL: dict[str, bool] = OrderedDict(
    [
        ('0', False),
        ('1', True),
        ('on', True),
        ('off', False),
        ('True', True),
        ('False', False),
        ('none', False),
    ]
)


class ValidationException(Exception):
    """Exption from ``cls.__init__`` when configuration value is invalid."""


class Setting:
    """Base class of user settings"""

    def __init__(self, default_value: t.Any, locked: bool = False):
        super().__init__()
        self.value: t.Any = default_value
        self.locked: bool = locked

    def parse(self, data: str):
        """Parse ``data`` and store the result at ``self.value``

        If needed, its overwritten in the inheritance.
        """
        self.value = data

    def get_value(self):
        """Returns the value of the setting

        If needed, its overwritten in the inheritance.
        """
        return self.value

    def save(self, name: str, resp: flask.Response):
        """Save cookie ``name`` in the HTTP response object

        If needed, its overwritten in the inheritance."""
        resp.set_cookie(name, self.value, max_age=COOKIE_MAX_AGE)


class StringSetting(Setting):
    """Setting of plain string values"""


class EnumStringSetting(Setting):
    """Setting of a value which can only come from the given choices"""

    value: str

    def __init__(self, default_value: str, choices: Iterable[str], locked: bool = False):
        super().__init__(default_value, locked)
        self.choices: Iterable[str] = choices
        self._validate_selection(self.value)

    def _validate_selection(self, selection: str):
        if selection not in self.choices:
            raise ValidationException('Invalid value: "{0}"'.format(selection))

    def parse(self, data: str):
        """Parse and validate ``data`` and store the result at ``self.value``"""
        self._validate_selection(data)
        self.value = data


class MultipleChoiceSetting(Setting):
    """Setting of values which can only come from the given choices"""

    def __init__(self, default_value: list[str], choices: Iterable[str], locked: bool = False):
        super().__init__(default_value, locked)
        self.choices: Iterable[str] = choices
        self._validate_selections(self.value)

    def _validate_selections(self, selections: list[str]):
        for item in selections:
            if item not in self.choices:
                raise ValidationException('Invalid value: "{0}"'.format(selections))

    def parse(self, data: str):
        """Parse and validate ``data`` and store the result at ``self.value``"""
        if data == '':
            self.value: list[str] = []
            return

        elements = data.split(',')
        self._validate_selections(elements)
        self.value = elements

    def parse_form(self, data: list[str]):
        if self.locked:
            return

        self.value = []
        for choice in data:
            if choice in self.choices and choice not in self.value:
                self.value.append(choice)

    def save(self, name: str, resp: flask.Response):
        """Save cookie ``name`` in the HTTP response object"""
        resp.set_cookie(name, ','.join(self.value), max_age=COOKIE_MAX_AGE)


class SetSetting(Setting):
    """Setting of values of type ``set`` (comma separated string)"""

    def __init__(self, *args, **kwargs):  # type: ignore
        super().__init__(*args, **kwargs)  # type: ignore
        self.values: set[str] = set()

    def get_value(self):
        """Returns a string with comma separated values."""
        return ','.join(self.values)

    def parse(self, data: str):
        """Parse and validate ``data`` and store the result at ``self.value``"""
        if data == '':
            self.values = set()
            return

        elements = data.split(',')
        for element in elements:
            self.values.add(element)

    def parse_form(self, data: str):
        if self.locked:
            return

        elements = data.split(',')
        self.values = set(elements)

    def save(self, name: str, resp: flask.Response):
        """Save cookie ``name`` in the HTTP response object"""
        resp.set_cookie(name, ','.join(self.values), max_age=COOKIE_MAX_AGE)


class SearchLanguageSetting(EnumStringSetting):
    """Available choices may change, so user's value may not be in choices anymore"""

    value: str

    def _validate_selection(self, selection: str):
        if selection != '' and selection != 'auto' and not VALID_LANGUAGE_CODE.match(selection):
            raise ValidationException('Invalid language code: "{0}"'.format(selection))

    def parse(self, data: str):
        """Parse and validate ``data`` and store the result at ``self.value``"""
        if data not in self.choices and data != self.value:
            # hack to give some backwards compatibility with old language cookies
            data = str(data).replace('_', '-')
            lang = data.split('-', maxsplit=1)[0]

            if data in self.choices:
                pass
            elif lang in self.choices:
                data = lang
            else:
                data = self.value
        self._validate_selection(data)
        self.value = data


class MapSetting(Setting):
    """Setting of a value that has to be translated in order to be storable"""

    key: str
    value: object

    def __init__(
        self, default_value: object, map: dict[str, object], locked: bool = False
    ):  # pylint: disable=redefined-builtin
        super().__init__(default_value, locked)
        self.map: dict[str, object] = map

        if self.value not in self.map.values():
            raise ValidationException('Invalid default value')

    def parse(self, data: str):
        """Parse and validate ``data`` and store the result at ``self.value``"""

        if data not in self.map:
            raise ValidationException('Invalid choice: {0}'.format(data))
        self.value = self.map[data]
        self.key = data  # pylint: disable=attribute-defined-outside-init

    def save(self, name: str, resp: flask.Response):
        """Save cookie ``name`` in the HTTP response object"""
        if hasattr(self, 'key'):
            resp.set_cookie(name, self.key, max_age=COOKIE_MAX_AGE)


class BooleanSetting(Setting):
    """Setting of a boolean value that has to be translated in order to be storable"""

    value: bool
    key: str

    def normalized_str(self, val: t.Any) -> str:
        for v_str, v_obj in MAP_STR2BOOL.items():
            if val == v_obj:
                return v_str
        raise ValueError("Invalid value: %s (%s) is not a boolean!" % (repr(val), type(val)))

    def parse(self, data: str):
        """Parse and validate ``data`` and store the result at ``self.value``"""
        self.value = MAP_STR2BOOL[data]
        self.key = self.normalized_str(self.value)  # pylint: disable=attribute-defined-outside-init

    def save(self, name: str, resp: flask.Response):
        """Save cookie ``name`` in the HTTP response object"""
        if hasattr(self, 'key'):
            resp.set_cookie(name, self.key, max_age=COOKIE_MAX_AGE)


class BooleanChoices:
    """Maps strings to booleans that are either true or false."""

    def __init__(self, name: str, choices: dict[str, bool], locked: bool = False):
        self.name: str = name
        self.choices: dict[str, bool] = choices
        self.locked: bool = locked
        self.default_choices: dict[str, bool] = dict(choices)

    def transform_form_items(self, items):
        return items

    def transform_values(self, values):
        return values

    def parse_cookie(self, data_disabled: str, data_enabled: str):
        for disabled in data_disabled.split(','):
            if disabled in self.choices:
                self.choices[disabled] = False

        for enabled in data_enabled.split(','):
            if enabled in self.choices:
                self.choices[enabled] = True

    def parse_form(self, items: list[str]):
        if self.locked:
            return

        disabled = self.transform_form_items(items)
        for setting in self.choices:
            self.choices[setting] = setting not in disabled

    @property
    def enabled(self):
        return (k for k, v in self.choices.items() if v)

    @property
    def disabled(self):
        return (k for k, v in self.choices.items() if not v)

    def save(self, resp: flask.Response):
        """Save cookie in the HTTP response object"""
        disabled_changed = (k for k in self.disabled if self.default_choices[k])
        enabled_changed = (k for k in self.enabled if not self.default_choices[k])
        resp.set_cookie('disabled_{0}'.format(self.name), ','.join(disabled_changed), max_age=COOKIE_MAX_AGE)
        resp.set_cookie('enabled_{0}'.format(self.name), ','.join(enabled_changed), max_age=COOKIE_MAX_AGE)

    def get_disabled(self):
        return self.transform_values(list(self.disabled))

    def get_enabled(self):
        return self.transform_values(list(self.enabled))


class EnginesSetting(BooleanChoices):
    """Engine settings"""

    def __init__(self, default_value, engines: Iterable[Engine]):
        choices = {}
        for engine in engines:
            for category in engine.categories:
                if not category in list(settings['categories_as_tabs'].keys()) + [DEFAULT_CATEGORY]:
                    continue
                choices['{}__{}'.format(engine.name, category)] = not engine.disabled
        super().__init__(default_value, choices)

    def transform_form_items(self, items):
        return [item[len('engine_') :].replace('_', ' ').replace('  ', '__') for item in items]

    def transform_values(self, values):
        if len(values) == 1 and next(iter(values)) == '':
            return []
        transformed_values = []
        for value in values:
            engine, category = value.split('__')
            transformed_values.append((engine, category))
        return transformed_values


class PluginsSetting(BooleanChoices):
    """Plugin settings"""

    def __init__(self, default_value, plugins: Iterable[searx.plugins.Plugin]):
        super().__init__(default_value, {plugin.id: plugin.active for plugin in plugins})

    def transform_form_items(self, items):
        return [item[len('plugin_') :] for item in items]


class ClientPref:
    """Container to assemble client prefferences and settings."""

    # hint: searx.webapp.get_client_settings should be moved into this class

    locale: babel.Locale | None
    """Locale preferred by the client."""

    def __init__(self, locale: babel.Locale | None = None):
        self.locale = locale

    @property
    def locale_tag(self):
        if self.locale is None:
            return None
        tag = self.locale.language
        if self.locale.territory:
            tag += '-' + self.locale.territory
        return tag

    @classmethod
    def from_http_request(cls, http_request: SXNG_Request):
        """Build ClientPref object from HTTP request.

        - `Accept-Language used for locale setting
          <https://www.w3.org/International/questions/qa-accept-lang-locales.en>`__

        """
        al_header = http_request.headers.get("Accept-Language")
        if not al_header:
            return cls(locale=None)

        pairs: list[tuple[babel.Locale, float]] = []
        for l in al_header.split(','):
            # fmt: off
            lang, qvalue = [_.strip() for _ in (l.split(';') + ['q=1',])[:2]]
            # fmt: on
            try:
                qvalue = float(qvalue.split('=')[-1])
                locale = babel.Locale.parse(lang, sep='-')
            except (ValueError, babel.core.UnknownLocaleError):
                continue
            pairs.append((locale, qvalue))

        locale = None
        if pairs:
            pairs.sort(reverse=True, key=lambda x: x[1])
            locale = pairs[0][0]
        return cls(locale=locale)


class Preferences:
    """Validates and saves preferences to cookies"""

    def __init__(
        self,
        themes: list[str],
        categories: list[str],
        engines: dict[str, Engine],
        plugins: searx.plugins.PluginStorage,
        client: ClientPref | None = None,
    ):

        super().__init__()

        self.key_value_settings: dict[str, Setting] = {
            # fmt: off
            'categories': MultipleChoiceSetting(
                ['general'],
                locked=is_locked('categories'),
                choices=categories + ['none']
            ),
            'language': SearchLanguageSetting(
                settings['search']['default_lang'],
                locked=is_locked('language'),
                choices=settings['search']['languages'] + ['']
            ),
            'locale': EnumStringSetting(
                settings['ui']['default_locale'],
                locked=is_locked('locale'),
                choices=list(LOCALE_NAMES.keys()) + ['']
            ),
            'autocomplete': EnumStringSetting(
                settings['search']['autocomplete'],
                locked=is_locked('autocomplete'),
                choices=list(autocomplete.backends.keys()) + ['']
            ),
            'favicon_resolver': EnumStringSetting(
                settings['search']['favicon_resolver'],
                locked=is_locked('favicon_resolver'),
                choices=list(favicons.proxy.CFG.resolver_map.keys()) + ['']
            ),
            'image_proxy': BooleanSetting(
                settings['server']['image_proxy'],
                locked=is_locked('image_proxy')
            ),
            'method': EnumStringSetting(
                settings['server']['method'],
                locked=is_locked('method'),
                choices=('GET', 'POST')
            ),
            'safesearch': MapSetting(
                settings['search']['safe_search'],
                locked=is_locked('safesearch'),
                map={
                    '0': 0,
                    '1': 1,
                    '2': 2
                }
            ),
            'theme': EnumStringSetting(
                settings['ui']['default_theme'],
                locked=is_locked('theme'),
                choices=themes
            ),
            'results_on_new_tab': BooleanSetting(
                settings['ui']['results_on_new_tab'],
                locked=is_locked('results_on_new_tab')
            ),
            'doi_resolver': MultipleChoiceSetting(
                [settings['default_doi_resolver'], ],
                locked=is_locked('doi_resolver'),
                choices=DOI_RESOLVERS
            ),
            'simple_style': EnumStringSetting(
                settings['ui']['theme_args']['simple_style'],
                locked=is_locked('simple_style'),
                choices=['', 'auto', 'light', 'dark', 'black']
            ),
            'center_alignment': BooleanSetting(
                settings['ui']['center_alignment'],
                locked=is_locked('center_alignment')
            ),
            'advanced_search': BooleanSetting(
                settings['ui']['advanced_search'],
                locked=is_locked('advanced_search')
            ),
            'query_in_title': BooleanSetting(
                settings['ui']['query_in_title'],
                locked=is_locked('query_in_title')
            ),
            'search_on_category_select': BooleanSetting(
                settings['ui']['search_on_category_select'],
                locked=is_locked('search_on_category_select')
            ),
            'hotkeys': EnumStringSetting(
                settings['ui']['hotkeys'],
                choices=['default', 'vim']
            ),
            'url_formatting': EnumStringSetting(
                settings['ui']['url_formatting'],
                choices=['pretty', 'full', 'host']
            ),
            # fmt: on
        }

        self.engines = EnginesSetting('engines', engines=engines.values())
        self.plugins = PluginsSetting('plugins', plugins=plugins)
        self.tokens = SetSetting('tokens')
        self.client = client or ClientPref()

    def get_as_url_params(self):
        """Return preferences as URL parameters"""
        settings_kv = {}
        for k, v in self.key_value_settings.items():
            if v.locked:
                continue
            if isinstance(v, MultipleChoiceSetting):
                settings_kv[k] = ','.join(v.get_value())
            else:
                settings_kv[k] = v.get_value()

        settings_kv['disabled_engines'] = ','.join(self.engines.disabled)
        settings_kv['enabled_engines'] = ','.join(self.engines.enabled)

        settings_kv['disabled_plugins'] = ','.join(self.plugins.disabled)
        settings_kv['enabled_plugins'] = ','.join(self.plugins.enabled)

        settings_kv['tokens'] = ','.join(self.tokens.values)

        return urlsafe_b64encode(compress(urlencode(settings_kv).encode())).decode()

    def parse_encoded_data(self, input_data: str):
        """parse (base64) preferences from request (``flask.request.form['preferences']``)"""
        bin_data = decompress(urlsafe_b64decode(input_data))
        dict_data = {}
        for x, y in parse_qs(bin_data.decode('ascii'), keep_blank_values=True).items():
            dict_data[x] = y[0]
        self.parse_dict(dict_data)

    def parse_dict(self, input_data: dict[str, str]):
        """parse preferences from request (``flask.request.form``)"""
        for user_setting_name, user_setting in input_data.items():
            if user_setting_name in self.key_value_settings:
                if self.key_value_settings[user_setting_name].locked:
                    continue
                self.key_value_settings[user_setting_name].parse(user_setting)
            elif user_setting_name == 'disabled_engines':
                self.engines.parse_cookie(input_data.get('disabled_engines', ''), input_data.get('enabled_engines', ''))
            elif user_setting_name == 'disabled_plugins':
                self.plugins.parse_cookie(input_data.get('disabled_plugins', ''), input_data.get('enabled_plugins', ''))
            elif user_setting_name == 'tokens':
                self.tokens.parse(user_setting)

    def parse_form(self, input_data: dict[str, str]):
        """Parse formular (``<input>``) data from a ``flask.request.form``"""
        disabled_engines = []
        enabled_categories = []
        disabled_plugins = []

        # boolean preferences are not sent by the form if they're false,
        # so we have to add them as false manually if they're not sent (then they would be true)
        for key, setting in self.key_value_settings.items():
            if key not in input_data.keys() and isinstance(setting, BooleanSetting):
                input_data[key] = 'False'

        for user_setting_name, user_setting in input_data.items():
            if user_setting_name in self.key_value_settings:
                self.key_value_settings[user_setting_name].parse(user_setting)
            elif user_setting_name.startswith('engine_'):
                disabled_engines.append(user_setting_name)
            elif user_setting_name.startswith('category_'):
                enabled_categories.append(user_setting_name[len('category_') :])
            elif user_setting_name.startswith('plugin_'):
                disabled_plugins.append(user_setting_name)
            elif user_setting_name == 'tokens':
                self.tokens.parse_form(user_setting)

        self.key_value_settings['categories'].parse_form(enabled_categories)  # type: ignore
        self.engines.parse_form(disabled_engines)
        self.plugins.parse_form(disabled_plugins)

    # cannot be used in case of engines or plugins
    def get_value(self, user_setting_name: str) -> t.Any:
        """Returns the value for ``user_setting_name``"""
        ret_val = None
        if user_setting_name in self.key_value_settings:
            ret_val = self.key_value_settings[user_setting_name].get_value()
        return ret_val

    def save(self, resp: flask.Response):
        """Save cookie in the HTTP response object"""
        for user_setting_name, user_setting in self.key_value_settings.items():
            # pylint: disable=unnecessary-dict-index-lookup
            if self.key_value_settings[user_setting_name].locked:
                continue
            user_setting.save(user_setting_name, resp)
        self.engines.save(resp)
        self.plugins.save(resp)
        self.tokens.save('tokens', resp)
        return resp

    def validate_token(self, engine):
        valid = True
        if hasattr(engine, 'tokens') and engine.tokens:
            valid = False
            for token in self.tokens.values:
                if token in engine.tokens:
                    valid = True
                    break

        return valid


def is_locked(setting_name: str):
    """Checks if a given setting name is locked by settings.yml"""
    if 'preferences' not in settings:
        return False
    if 'lock' not in settings['preferences']:
        return False
    return setting_name in settings['preferences']['lock']
