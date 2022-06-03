# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Searx preferences implementation.
"""

# pylint: disable=useless-object-inheritance

from base64 import urlsafe_b64encode, urlsafe_b64decode
from zlib import compress, decompress
from urllib.parse import parse_qs, urlencode
from typing import Iterable, Dict, List

import flask

from searx import settings, autocomplete
from searx.engines import Engine
from searx.plugins import Plugin
from searx.locales import LOCALE_NAMES
from searx.webutils import VALID_LANGUAGE_CODE
from searx.engines import OTHER_CATEGORY


COOKIE_MAX_AGE = 60 * 60 * 24 * 365 * 5  # 5 years
DOI_RESOLVERS = list(settings['doi_resolvers'])


class ValidationException(Exception):

    """Exption from ``cls.__init__`` when configuration value is invalid."""


class Setting:
    """Base class of user settings"""

    def __init__(self, default_value, locked: bool = False):
        super().__init__()
        self.value = default_value
        self.locked = locked

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
        """Save cookie ``name`` in the HTTP reponse obect

        If needed, its overwritten in the inheritance."""
        resp.set_cookie(name, self.value, max_age=COOKIE_MAX_AGE)


class StringSetting(Setting):
    """Setting of plain string values"""


class EnumStringSetting(Setting):
    """Setting of a value which can only come from the given choices"""

    def __init__(self, default_value: str, choices: Iterable[str], locked=False):
        super().__init__(default_value, locked)
        self.choices = choices
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

    def __init__(self, default_value: List[str], choices: Iterable[str], locked=False):
        super().__init__(default_value, locked)
        self.choices = choices
        self._validate_selections(self.value)

    def _validate_selections(self, selections: List[str]):
        for item in selections:
            if item not in self.choices:
                raise ValidationException('Invalid value: "{0}"'.format(selections))

    def parse(self, data: str):
        """Parse and validate ``data`` and store the result at ``self.value``"""
        if data == '':
            self.value = []
            return

        elements = data.split(',')
        self._validate_selections(elements)
        self.value = elements

    def parse_form(self, data: List[str]):
        if self.locked:
            return

        self.value = []
        for choice in data:
            if choice in self.choices and choice not in self.value:
                self.value.append(choice)

    def save(self, name: str, resp: flask.Response):
        """Save cookie ``name`` in the HTTP reponse obect"""
        resp.set_cookie(name, ','.join(self.value), max_age=COOKIE_MAX_AGE)


class SetSetting(Setting):
    """Setting of values of type ``set`` (comma separated string)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.values = set()

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
        """Save cookie ``name`` in the HTTP reponse obect"""
        resp.set_cookie(name, ','.join(self.values), max_age=COOKIE_MAX_AGE)


class SearchLanguageSetting(EnumStringSetting):
    """Available choices may change, so user's value may not be in choices anymore"""

    def _validate_selection(self, selection):
        if selection != '' and not VALID_LANGUAGE_CODE.match(selection):
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

    def __init__(self, default_value, map: Dict[str, object], locked=False):  # pylint: disable=redefined-builtin
        super().__init__(default_value, locked)
        self.map = map

        if self.value not in self.map.values():
            raise ValidationException('Invalid default value')

    def parse(self, data: str):
        """Parse and validate ``data`` and store the result at ``self.value``"""

        if data not in self.map:
            raise ValidationException('Invalid choice: {0}'.format(data))
        self.value = self.map[data]
        self.key = data  # pylint: disable=attribute-defined-outside-init

    def save(self, name: str, resp: flask.Response):
        """Save cookie ``name`` in the HTTP reponse obect"""
        if hasattr(self, 'key'):
            resp.set_cookie(name, self.key, max_age=COOKIE_MAX_AGE)


class BooleanChoices:
    """Maps strings to booleans that are either true or false."""

    def __init__(self, name: str, choices: Dict[str, bool], locked: bool = False):
        self.name = name
        self.choices = choices
        self.locked = locked
        self.default_choices = dict(choices)

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

    def parse_form(self, items: List[str]):
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
        """Save cookie in the HTTP reponse obect"""
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
                if not category in list(settings['categories_as_tabs'].keys()) + [OTHER_CATEGORY]:
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

    def __init__(self, default_value, plugins: Iterable[Plugin]):
        super().__init__(default_value, {plugin.id: plugin.default_on for plugin in plugins})

    def transform_form_items(self, items):
        return [item[len('plugin_') :] for item in items]


class Preferences:
    """Validates and saves preferences to cookies"""

    def __init__(self, themes: List[str], categories: List[str], engines: Dict[str, Engine], plugins: Iterable[Plugin]):
        super().__init__()

        self.key_value_settings: Dict[str, Setting] = {
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
            'image_proxy': MapSetting(
                settings['server']['image_proxy'],
                locked=is_locked('image_proxy'),
                map={
                    '': settings['server']['image_proxy'],
                    '0': False,
                    '1': True,
                    'True': True,
                    'False': False
                }
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
            'results_on_new_tab': MapSetting(
                settings['ui']['results_on_new_tab'],
                locked=is_locked('results_on_new_tab'),
                map={
                    '0': False,
                    '1': True,
                    'False': False,
                    'True': True
                }
            ),
            'doi_resolver': MultipleChoiceSetting(
                [settings['default_doi_resolver'], ],
                locked=is_locked('doi_resolver'),
                choices=DOI_RESOLVERS
            ),
            'simple_style': EnumStringSetting(
                settings['ui']['theme_args']['simple_style'],
                locked=is_locked('simple_style'),
                choices=['', 'auto', 'light', 'dark']
            ),
            'center_aligment': MapSetting(
                settings['ui']['center_aligment'],
                locked=is_locked('center_aligment'),
                map={
                    '0': False,
                    '1': True,
                    'False': False,
                    'True': True
                }
            ),
            'advanced_search': MapSetting(
                settings['ui']['advanced_search'],
                locked=is_locked('advanced_search'),
                map={
                    '0': False,
                    '1': True,
                    'False': False,
                    'True': True,
                    'on': True,
                }
            ),
            'query_in_title': MapSetting(
                settings['ui']['query_in_title'],
                locked=is_locked('query_in_title'),
                map={
                    '': settings['ui']['query_in_title'],
                    '0': False,
                    '1': True,
                    'True': True,
                    'False': False
                }
            ),
            'infinite_scroll': MapSetting(
                settings['ui']['infinite_scroll'],
                locked=is_locked('infinite_scroll'),
                map={
                    '': settings['ui']['infinite_scroll'],
                    '0': False,
                    '1': True,
                    'True': True,
                    'False': False
                }
            ),
            # fmt: on
        }

        self.engines = EnginesSetting('engines', engines=engines.values())
        self.plugins = PluginsSetting('plugins', plugins=plugins)
        self.tokens = SetSetting('tokens')
        self.unknown_params: Dict[str, str] = {}

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
        for x, y in parse_qs(bin_data.decode('ascii')).items():
            dict_data[x] = y[0]
        self.parse_dict(dict_data)

    def parse_dict(self, input_data: Dict[str, str]):
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
            elif not any(
                user_setting_name.startswith(x) for x in ['enabled_', 'disabled_', 'engine_', 'category_', 'plugin_']
            ):
                self.unknown_params[user_setting_name] = user_setting

    def parse_form(self, input_data: Dict[str, str]):
        """Parse formular (``<input>``) data from a ``flask.request.form``"""
        disabled_engines = []
        enabled_categories = []
        disabled_plugins = []
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
            else:
                self.unknown_params[user_setting_name] = user_setting
        self.key_value_settings['categories'].parse_form(enabled_categories)
        self.engines.parse_form(disabled_engines)
        self.plugins.parse_form(disabled_plugins)

    # cannot be used in case of engines or plugins
    def get_value(self, user_setting_name: str):
        """Returns the value for ``user_setting_name``"""
        ret_val = None
        if user_setting_name in self.key_value_settings:
            ret_val = self.key_value_settings[user_setting_name].get_value()
        if user_setting_name in self.unknown_params:
            ret_val = self.unknown_params[user_setting_name]
        return ret_val

    def save(self, resp: flask.Response):
        """Save cookie in the HTTP reponse obect"""
        for user_setting_name, user_setting in self.key_value_settings.items():
            # pylint: disable=unnecessary-dict-index-lookup
            if self.key_value_settings[user_setting_name].locked:
                continue
            user_setting.save(user_setting_name, resp)
        self.engines.save(resp)
        self.plugins.save(resp)
        self.tokens.save('tokens', resp)
        for k, v in self.unknown_params.items():
            resp.set_cookie(k, v, max_age=COOKIE_MAX_AGE)
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
