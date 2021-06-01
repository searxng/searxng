# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Searx preferences implementation.
"""

# pylint: disable=useless-object-inheritance

from base64 import urlsafe_b64encode, urlsafe_b64decode
from zlib import compress, decompress
from urllib.parse import parse_qs, urlencode

from searx import settings, autocomplete
from searx.languages import language_codes as languages
from searx.webutils import VALID_LANGUAGE_CODE


COOKIE_MAX_AGE = 60 * 60 * 24 * 365 * 5  # 5 years
LANGUAGE_CODES = [l[0] for l in languages]
LANGUAGE_CODES.append('all')
DISABLED = 0
ENABLED = 1
DOI_RESOLVERS = list(settings['doi_resolvers'])


class MissingArgumentException(Exception):
    """Exption from ``cls._post_init`` when a argument is missed.
    """


class ValidationException(Exception):

    """Exption from ``cls._post_init`` when configuration value is invalid.
    """


class Setting:
    """Base class of user settings"""

    def __init__(self, default_value, locked=False, **kwargs):
        super().__init__()
        self.value = default_value
        self.locked = locked
        for key, value in kwargs.items():
            setattr(self, key, value)

        self._post_init()

    def _post_init(self):
        pass

    def parse(self, data):
        """Parse ``data`` and store the result at ``self.value``

        If needed, its overwritten in the inheritance.
        """
        self.value = data

    def get_value(self):
        """Returns the value of the setting

        If needed, its overwritten in the inheritance.
        """
        return self.value

    def save(self, name, resp):
        """Save cookie ``name`` in the HTTP reponse obect

        If needed, its overwritten in the inheritance."""
        resp.set_cookie(name, self.value, max_age=COOKIE_MAX_AGE)


class StringSetting(Setting):
    """Setting of plain string values"""


class EnumStringSetting(Setting):
    """Setting of a value which can only come from the given choices"""

    def _post_init(self):
        if not hasattr(self, 'choices'):
            raise MissingArgumentException('Missing argument: choices')
        self._validate_selection(self.value)

    def _validate_selection(self, selection):
        if selection not in self.choices:  # pylint: disable=no-member
            raise ValidationException('Invalid value: "{0}"'.format(selection))

    def parse(self, data):
        """Parse and validate ``data`` and store the result at ``self.value``
        """
        self._validate_selection(data)
        self.value = data


class MultipleChoiceSetting(EnumStringSetting):
    """Setting of values which can only come from the given choices"""

    def _validate_selections(self, selections):
        for item in selections:
            if item not in self.choices:  # pylint: disable=no-member
                raise ValidationException('Invalid value: "{0}"'.format(selections))

    def _post_init(self):
        if not hasattr(self, 'choices'):
            raise MissingArgumentException('Missing argument: choices')
        self._validate_selections(self.value)

    def parse(self, data):
        """Parse and validate ``data`` and store the result at ``self.value``
        """
        if data == '':
            self.value = []
            return

        elements = data.split(',')
        self._validate_selections(elements)
        self.value = elements

    def parse_form(self, data):  # pylint: disable=missing-function-docstring
        if self.locked:
            return

        self.value = []
        for choice in data:
            if choice in self.choices and choice not in self.value:  # pylint: disable=no-member
                self.value.append(choice)

    def save(self, name, resp):
        """Save cookie ``name`` in the HTTP reponse obect
        """
        resp.set_cookie(name, ','.join(self.value), max_age=COOKIE_MAX_AGE)


class SetSetting(Setting):
    """Setting of values of type ``set`` (comma separated string) """
    def _post_init(self):
        if not hasattr(self, 'values'):
            self.values = set()

    def get_value(self):
        """Returns a string with comma separated values.
        """
        return ','.join(self.values)

    def parse(self, data):
        """Parse and validate ``data`` and store the result at ``self.value``
        """
        if data == '':
            self.values = set()  # pylint: disable=attribute-defined-outside-init
            return

        elements = data.split(',')
        for element in elements:
            self.values.add(element)

    def parse_form(self, data):  # pylint: disable=missing-function-docstring
        if self.locked:
            return

        elements = data.split(',')
        self.values = set(elements)  # pylint: disable=attribute-defined-outside-init

    def save(self, name, resp):
        """Save cookie ``name`` in the HTTP reponse obect
        """
        resp.set_cookie(name, ','.join(self.values), max_age=COOKIE_MAX_AGE)


class SearchLanguageSetting(EnumStringSetting):
    """Available choices may change, so user's value may not be in choices anymore"""

    def _validate_selection(self, selection):
        if selection != '' and not VALID_LANGUAGE_CODE.match(selection):
            raise ValidationException('Invalid language code: "{0}"'.format(selection))

    def parse(self, data):
        """Parse and validate ``data`` and store the result at ``self.value``
        """
        if data not in self.choices and data != self.value:  # pylint: disable=no-member
            # hack to give some backwards compatibility with old language cookies
            data = str(data).replace('_', '-')
            lang = data.split('-')[0]
            # pylint: disable=no-member
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

    def _post_init(self):
        if not hasattr(self, 'map'):
            raise MissingArgumentException('missing argument: map')
        if self.value not in self.map.values():  # pylint: disable=no-member
            raise ValidationException('Invalid default value')

    def parse(self, data):
        """Parse and validate ``data`` and store the result at ``self.value``
        """
        # pylint: disable=no-member
        if data not in self.map:
            raise ValidationException('Invalid choice: {0}'.format(data))
        self.value = self.map[data]
        self.key = data  # pylint: disable=attribute-defined-outside-init

    def save(self, name, resp):
        """Save cookie ``name`` in the HTTP reponse obect
        """
        if hasattr(self, 'key'):
            resp.set_cookie(name, self.key, max_age=COOKIE_MAX_AGE)


class SwitchableSetting(Setting):
    """ Base class for settings that can be turned on && off"""

    def _post_init(self):
        self.disabled = set()
        self.enabled = set()
        if not hasattr(self, 'choices'):
            raise MissingArgumentException('missing argument: choices')

    def transform_form_items(self, items):  # pylint: disable=missing-function-docstring
        # pylint: disable=no-self-use
        return items

    def transform_values(self, values):   # pylint: disable=missing-function-docstring
        # pylint: disable=no-self-use
        return values

    def parse_cookie(self, data):   # pylint: disable=missing-function-docstring
        # pylint: disable=attribute-defined-outside-init
        if data[DISABLED] != '':
            self.disabled = set(data[DISABLED].split(','))
        if data[ENABLED] != '':
            self.enabled = set(data[ENABLED].split(','))

    def parse_form(self, items):   # pylint: disable=missing-function-docstring
        if self.locked:
            return

        items = self.transform_form_items(items)
        self.disabled = set()  # pylint: disable=attribute-defined-outside-init
        self.enabled = set()   # pylint: disable=attribute-defined-outside-init
        for choice in self.choices:  # pylint: disable=no-member
            if choice['default_on']:
                if choice['id'] in items:
                    self.disabled.add(choice['id'])
            else:
                if choice['id'] not in items:
                    self.enabled.add(choice['id'])

    def save(self, resp):  # pylint: disable=arguments-differ
        """Save cookie in the HTTP reponse obect
        """
        resp.set_cookie('disabled_{0}'.format(self.value), ','.join(self.disabled), max_age=COOKIE_MAX_AGE)
        resp.set_cookie('enabled_{0}'.format(self.value), ','.join(self.enabled), max_age=COOKIE_MAX_AGE)

    def get_disabled(self):   # pylint: disable=missing-function-docstring
        disabled = self.disabled
        for choice in self.choices:  # pylint: disable=no-member
            if not choice['default_on'] and choice['id'] not in self.enabled:
                disabled.add(choice['id'])
        return self.transform_values(disabled)

    def get_enabled(self):   # pylint: disable=missing-function-docstring
        enabled = self.enabled
        for choice in self.choices:  # pylint: disable=no-member
            if choice['default_on'] and choice['id'] not in self.disabled:
                enabled.add(choice['id'])
        return self.transform_values(enabled)


class EnginesSetting(SwitchableSetting):
    """Engine settings"""

    def _post_init(self):
        super()._post_init()
        transformed_choices = []
        for engine_name, engine in self.choices.items():  # pylint: disable=no-member,access-member-before-definition
            for category in engine.categories:
                transformed_choice = dict()
                transformed_choice['default_on'] = not engine.disabled
                transformed_choice['id'] = '{}__{}'.format(engine_name, category)
                transformed_choices.append(transformed_choice)
        self.choices = transformed_choices

    def transform_form_items(self, items):
        return [item[len('engine_'):].replace('_', ' ').replace('  ', '__') for item in items]

    def transform_values(self, values):
        if len(values) == 1 and next(iter(values)) == '':
            return list()
        transformed_values = []
        for value in values:
            engine, category = value.split('__')
            transformed_values.append((engine, category))
        return transformed_values


class PluginsSetting(SwitchableSetting):
    """Plugin settings"""

    def _post_init(self):
        super()._post_init()
        transformed_choices = []
        for plugin in self.choices:  # pylint: disable=access-member-before-definition
            transformed_choice = dict()
            transformed_choice['default_on'] = plugin.default_on
            transformed_choice['id'] = plugin.id
            transformed_choices.append(transformed_choice)
        self.choices = transformed_choices

    def transform_form_items(self, items):
        return [item[len('plugin_'):] for item in items]


class Preferences:
    """Validates and saves preferences to cookies"""

    def __init__(self, themes, categories, engines, plugins):
        super().__init__()

        self.key_value_settings = {
            'categories': MultipleChoiceSetting(
                ['general'],
                is_locked('categories'),
                choices=categories + ['none']
            ),
            'language': SearchLanguageSetting(
                settings['search']['default_lang'],
                is_locked('language'),
                choices=list(LANGUAGE_CODES) + ['']
            ),
            'locale': EnumStringSetting(
                settings['ui']['default_locale'],
                is_locked('locale'),
                choices=list(settings['locales'].keys()) + ['']
            ),
            'autocomplete': EnumStringSetting(
                settings['search']['autocomplete'],
                is_locked('autocomplete'),
                choices=list(autocomplete.backends.keys()) + ['']
            ),
            'image_proxy': MapSetting(
                settings['server']['image_proxy'],
                is_locked('image_proxy'),
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
                is_locked('method'),
                choices=('GET', 'POST')
            ),
            'safesearch': MapSetting(
                settings['search']['safe_search'],
                is_locked('safesearch'),
                map={
                    '0': 0,
                    '1': 1,
                    '2': 2
                }
            ),
            'theme': EnumStringSetting(
                settings['ui']['default_theme'],
                is_locked('theme'),
                choices=themes
            ),
            'results_on_new_tab': MapSetting(
                settings['ui']['results_on_new_tab'],
                is_locked('results_on_new_tab'),
                map={
                    '0': False,
                    '1': True,
                    'False': False,
                    'True': True
                }
            ),
            'doi_resolver': MultipleChoiceSetting(
                [settings['default_doi_resolver'], ],
                is_locked('doi_resolver'),
                choices=DOI_RESOLVERS
            ),
            'oscar-style': EnumStringSetting(
                settings['ui']['theme_args']['oscar_style'],
                is_locked('oscar-style'),
                choices=['', 'logicodev', 'logicodev-dark', 'pointhi']),
            'advanced_search': MapSetting(
                settings['ui']['advanced_search'],
                is_locked('advanced_search'),
                map={
                    '0': False,
                    '1': True,
                    'False': False,
                    'True': True,
                    'on': True,
                }
            ),
        }

        self.engines = EnginesSetting('engines', choices=engines)
        self.plugins = PluginsSetting('plugins', choices=plugins)
        self.tokens = SetSetting('tokens')
        self.unknown_params = {}

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

    def parse_encoded_data(self, input_data):
        """parse (base64) preferences from request (``flask.request.form['preferences']``)"""
        decoded_data = decompress(urlsafe_b64decode(input_data.encode()))
        dict_data = {}
        for x, y in parse_qs(decoded_data).items():
            dict_data[x.decode()] = y[0].decode()
        self.parse_dict(dict_data)

    def parse_dict(self, input_data):
        """parse preferences from request (``flask.request.form``)"""
        for user_setting_name, user_setting in input_data.items():
            if user_setting_name in self.key_value_settings:
                if self.key_value_settings[user_setting_name].locked:
                    continue
                self.key_value_settings[user_setting_name].parse(user_setting)
            elif user_setting_name == 'disabled_engines':
                self.engines.parse_cookie((input_data.get('disabled_engines', ''),
                                           input_data.get('enabled_engines', '')))
            elif user_setting_name == 'disabled_plugins':
                self.plugins.parse_cookie((input_data.get('disabled_plugins', ''),
                                           input_data.get('enabled_plugins', '')))
            elif user_setting_name == 'tokens':
                self.tokens.parse(user_setting)
            elif not any(user_setting_name.startswith(x) for x in [
                    'enabled_',
                    'disabled_',
                    'engine_',
                    'category_',
                    'plugin_']):
                self.unknown_params[user_setting_name] = user_setting

    def parse_form(self, input_data):
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
                enabled_categories.append(user_setting_name[len('category_'):])
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
    def get_value(self, user_setting_name):
        """Returns the value for ``user_setting_name``
        """
        ret_val = None
        if user_setting_name in self.key_value_settings:
            ret_val = self.key_value_settings[user_setting_name].get_value()
        if user_setting_name in self.unknown_params:
            ret_val = self.unknown_params[user_setting_name]
        return ret_val

    def save(self, resp):
        """Save cookie in the HTTP reponse obect
        """
        for user_setting_name, user_setting in self.key_value_settings.items():
            if self.key_value_settings[user_setting_name].locked:
                continue
            user_setting.save(user_setting_name, resp)
        self.engines.save(resp)
        self.plugins.save(resp)
        self.tokens.save('tokens', resp)
        for k, v in self.unknown_params.items():
            resp.set_cookie(k, v, max_age=COOKIE_MAX_AGE)
        return resp

    def validate_token(self, engine):  # pylint: disable=missing-function-docstring
        valid = True
        if hasattr(engine, 'tokens') and engine.tokens:
            valid = False
            for token in self.tokens.values:
                if token in engine.tokens:
                    valid = True
                    break

        return valid


def is_locked(setting_name):
    """Checks if a given setting name is locked by settings.yml
    """
    if 'preferences' not in settings:
        return False
    if 'lock' not in settings['preferences']:
        return False
    return setting_name in settings['preferences']['lock']
