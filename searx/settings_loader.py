# SPDX-License-Identifier: AGPL-3.0-or-later

from os import environ
from os.path import dirname, join, abspath, isfile
from collections.abc import Mapping
from itertools import filterfalse

import yaml

from searx.exceptions import SearxSettingsException


searx_dir = abspath(dirname(__file__))


def check_settings_yml(file_name):
    if isfile(file_name):
        return file_name
    return None


def load_yaml(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as settings_yaml:
            return yaml.safe_load(settings_yaml)
    except IOError as e:
        raise SearxSettingsException(e, file_name) from e
    except yaml.YAMLError as e:
        raise SearxSettingsException(e, file_name) from e


def get_default_settings_path():
    return check_settings_yml(join(searx_dir, 'settings.yml'))


def get_user_settings_path():
    # find location of settings.yml
    if 'SEARXNG_SETTINGS_PATH' in environ:
        # if possible set path to settings using the
        # enviroment variable SEARXNG_SETTINGS_PATH
        return check_settings_yml(environ['SEARXNG_SETTINGS_PATH'])

    if environ.get('SEARXNG_DISABLE_ETC_SETTINGS', '').lower() in ('1', 'true'):
        return None

    # if not, get it from searx code base or last solution from /etc/searxng
    try:
        return check_settings_yml('/etc/searxng/settings.yml')
    except SearxSettingsException as e:
        # fall back to searx settings
        try:
            return check_settings_yml('/etc/searx/settings.yml')
        except SearxSettingsException:
            # if none are found, raise the exception about SearXNG
            raise e  # pylint: disable=raise-missing-from


def update_dict(default_dict, user_dict):
    for k, v in user_dict.items():
        if isinstance(v, Mapping):
            default_dict[k] = update_dict(default_dict.get(k, {}), v)
        else:
            default_dict[k] = v
    return default_dict


def update_settings(default_settings, user_settings):
    # merge everything except the engines
    for k, v in user_settings.items():
        if k not in ('use_default_settings', 'engines'):
            if k in default_settings and isinstance(v, Mapping):
                update_dict(default_settings[k], v)
            else:
                default_settings[k] = v

    # parse the engines
    remove_engines = None
    keep_only_engines = None
    use_default_settings = user_settings.get('use_default_settings')
    if isinstance(use_default_settings, dict):
        remove_engines = use_default_settings.get('engines', {}).get('remove')
        keep_only_engines = use_default_settings.get('engines', {}).get('keep_only')

    if 'engines' in user_settings or remove_engines is not None or keep_only_engines is not None:
        engines = default_settings['engines']

        # parse "use_default_settings.engines.remove"
        if remove_engines is not None:
            engines = list(filterfalse(lambda engine: (engine.get('name')) in remove_engines, engines))

        # parse "use_default_settings.engines.keep_only"
        if keep_only_engines is not None:
            engines = list(filter(lambda engine: (engine.get('name')) in keep_only_engines, engines))

        # parse "engines"
        user_engines = user_settings.get('engines')
        if user_engines:
            engines_dict = dict((definition['name'], definition) for definition in engines)
            for user_engine in user_engines:
                default_engine = engines_dict.get(user_engine['name'])
                if default_engine:
                    update_dict(default_engine, user_engine)
                else:
                    engines.append(user_engine)

        # store the result
        default_settings['engines'] = engines

    return default_settings


def is_use_default_settings(user_settings):
    use_default_settings = user_settings.get('use_default_settings')
    if use_default_settings is True:
        return True
    if isinstance(use_default_settings, dict):
        return True
    if use_default_settings is False or use_default_settings is None:
        return False
    raise ValueError('Invalid value for use_default_settings')


def load_settings(load_user_setttings=True):
    default_settings_path = get_default_settings_path()
    user_settings_path = get_user_settings_path()
    if user_settings_path is None or not load_user_setttings:
        # no user settings
        return (load_yaml(default_settings_path), 'load the default settings from {}'.format(default_settings_path))

    # user settings
    user_settings = load_yaml(user_settings_path)
    if is_use_default_settings(user_settings):
        # the user settings are merged with the default configuration
        default_settings = load_yaml(default_settings_path)
        update_settings(default_settings, user_settings)
        return (
            default_settings,
            'merge the default settings ( {} ) and the user setttings ( {} )'.format(
                default_settings_path, user_settings_path
            ),
        )

    # the user settings, fully replace the default configuration
    return (user_settings, 'load the user settings from {}'.format(user_settings_path))
