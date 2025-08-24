# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implementations for loading configurations from YAML files.  This essentially
includes the configuration of the (:ref:`SearXNG appl <searxng settings.yml>`)
server. The default configuration for the application server is loaded from the
:origin:`DEFAULT_SETTINGS_FILE <searx/settings.yml>`.  This default
configuration can be completely replaced or :ref:`customized individually
<use_default_settings.yml>` and the ``SEARXNG_SETTINGS_PATH`` environment
variable can be used to set the location from which the local customizations are
to be loaded. The rules used for this can be found in the
:py:obj:`get_user_cfg_folder` function.

- By default, local configurations are expected in folder ``/etc/searxng`` from
  where applications can load them with the :py:obj:`get_yaml_cfg` function.

- By default, customized :ref:`SearXNG appl <searxng settings.yml>` settings are
  expected in a file named ``settings.yml``.

"""

import typing as t
import os.path
from collections.abc import MutableMapping
from itertools import filterfalse
from pathlib import Path

import yaml

from searx.exceptions import SearxSettingsException

JSONType: t.TypeAlias = dict[str, "JSONType"] | list["JSONType"] | str | int | float | bool | None
SettingsType: t.TypeAlias = dict[str, JSONType]

searx_dir = os.path.abspath(os.path.dirname(__file__))

SETTINGS_YAML = Path("settings.yml")
DEFAULT_SETTINGS_FILE = Path(searx_dir) / SETTINGS_YAML
"""The :origin:`searx/settings.yml` file with all the default settings."""


def load_yaml(file_name: str | Path) -> SettingsType:
    """Load YAML config from a file."""
    try:
        with open(file_name, 'r', encoding='utf-8') as settings_yaml:
            return yaml.safe_load(settings_yaml) or {}
    except IOError as e:
        raise SearxSettingsException(e, str(file_name)) from e
    except yaml.YAMLError as e:
        raise SearxSettingsException(e, str(file_name)) from e


def get_yaml_cfg(file_name: str | Path) -> SettingsType:
    """Shortcut to load a YAML config from a file, located in the

    - :py:obj:`get_user_cfg_folder` or
    - in the ``searx`` folder of the SearXNG installation
    """

    folder = get_user_cfg_folder() or Path(searx_dir)
    fname = folder / file_name
    if not fname.is_file():
        raise FileNotFoundError(f"File {fname} does not exist!")

    return load_yaml(fname)


def get_user_cfg_folder() -> Path | None:
    """Returns folder where the local configurations are located.

    1. If the ``SEARXNG_SETTINGS_PATH`` environment is set and points to a
       folder (e.g. ``/etc/mysxng/``), all local configurations are expected in
       this folder.  The settings of the :ref:`SearXNG appl <searxng
       settings.yml>` then expected in ``settings.yml``
       (e.g. ``/etc/mysxng/settings.yml``).

    2. If the ``SEARXNG_SETTINGS_PATH`` environment is set and points to a file
       (e.g. ``/etc/mysxng/myinstance.yml``), this file contains the settings of
       the :ref:`SearXNG appl <searxng settings.yml>` and the folder
       (e.g. ``/etc/mysxng/``) is used for all other configurations.

       This type (``SEARXNG_SETTINGS_PATH`` points to a file) is suitable for
       use cases in which different profiles of the :ref:`SearXNG appl <searxng
       settings.yml>` are to be managed, such as in test scenarios.

    3. If folder ``/etc/searxng`` exists, it is used.

    In case none of the above path exists, ``None`` is returned.  In case of
    environment ``SEARXNG_SETTINGS_PATH`` is set, but the (folder or file) does
    not exists, a :py:obj:`EnvironmentError` is raised.

    """

    folder = None
    settings_path = os.environ.get("SEARXNG_SETTINGS_PATH")

    # Disable default /etc/searxng is intended exclusively for internal testing purposes
    # and is therefore not documented!
    disable_etc = os.environ.get('SEARXNG_DISABLE_ETC_SETTINGS', '').lower() in ('1', 'true')

    if settings_path:
        # rule 1. and 2.
        settings_path = Path(settings_path)
        if settings_path.is_dir():
            folder = settings_path
        elif settings_path.is_file():
            folder = settings_path.parent
        else:
            raise EnvironmentError(1, f"{settings_path} not exists!", settings_path)

    if not folder and not disable_etc:
        # default: rule 3.
        folder = Path("/etc/searxng")
        if not folder.is_dir():
            folder = None

    return folder


def update_dict(default_dict: MutableMapping[str, t.Any], user_dict: MutableMapping[str, t.Any]):
    for k, v in user_dict.items():
        if isinstance(v, MutableMapping):
            default_dict[k] = update_dict(default_dict.get(k, {}), v)  # type: ignore
        else:
            default_dict[k] = v
    return default_dict


def update_settings(default_settings: MutableMapping[str, t.Any], user_settings: MutableMapping[str, t.Any]):
    # pylint: disable=too-many-branches

    # merge everything except the engines
    for k, v in user_settings.items():
        if k not in ('use_default_settings', 'engines'):
            if k in default_settings and isinstance(v, MutableMapping):
                update_dict(default_settings[k], v)  # type: ignore
            else:
                default_settings[k] = v

    categories_as_tabs = user_settings.get('categories_as_tabs')
    if categories_as_tabs:
        default_settings['categories_as_tabs'] = categories_as_tabs

    plugins = user_settings.get('plugins')
    if plugins is not None:
        default_settings['plugins'] = plugins

    # parse the engines
    remove_engines: None | list[str] = None
    keep_only_engines: list[str] | None = None
    use_default_settings: dict[str, t.Any] | None = user_settings.get('use_default_settings')
    if isinstance(use_default_settings, dict):
        remove_engines = use_default_settings.get('engines', {}).get('remove')
        keep_only_engines = use_default_settings.get('engines', {}).get('keep_only')

    if 'engines' in user_settings or remove_engines is not None or keep_only_engines is not None:
        engines: list[dict[str, t.Any]] = default_settings['engines']

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
                default_engine: dict[str, t.Any] | None = engines_dict.get(user_engine['name'])
                if default_engine:
                    update_dict(default_engine, user_engine)
                else:
                    engines.append(user_engine)

        # store the result
        default_settings['engines'] = engines

    return default_settings


def is_use_default_settings(user_settings: SettingsType) -> bool:

    use_default_settings: bool | JSONType = user_settings.get('use_default_settings')
    if use_default_settings is True:
        return True
    if isinstance(use_default_settings, dict):
        return True
    if use_default_settings is False or use_default_settings is None:
        return False
    raise ValueError('Invalid value for use_default_settings')


def load_settings(load_user_settings: bool = True) -> tuple[SettingsType, str]:
    """Function for loading the settings of the SearXNG application
    (:ref:`settings.yml <searxng settings.yml>`)."""

    msg = f"load the default settings from {DEFAULT_SETTINGS_FILE}"
    cfg = load_yaml(DEFAULT_SETTINGS_FILE)
    cfg_folder = get_user_cfg_folder()

    if not load_user_settings or not cfg_folder:
        return cfg, msg

    settings_yml = os.environ.get("SEARXNG_SETTINGS_PATH")
    if settings_yml and Path(settings_yml).is_file():
        # see get_user_cfg_folder() --> SEARXNG_SETTINGS_PATH points to a file
        settings_yml = Path(settings_yml).name
    else:
        # see get_user_cfg_folder() --> SEARXNG_SETTINGS_PATH points to a folder
        settings_yml = SETTINGS_YAML

    cfg_file = cfg_folder / settings_yml
    if not cfg_file.exists():
        return cfg, msg

    msg = f"load the user settings from {cfg_file}"
    user_cfg = load_yaml(cfg_file)

    if is_use_default_settings(user_cfg):
        # the user settings are merged with the default configuration
        msg = f"merge the default settings ( {DEFAULT_SETTINGS_FILE} ) and the user settings ( {cfg_file} )"
        update_settings(cfg, user_cfg)
    else:
        cfg = user_cfg

    return cfg, msg
