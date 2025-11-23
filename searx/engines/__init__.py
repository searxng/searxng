# SPDX-License-Identifier: AGPL-3.0-or-later
"""Load and initialize the ``engines``, see :py:func:`load_engines` and register
:py:obj:`engine_shortcuts`.

usage::

    load_engines( settings['engines'] )

"""

import typing as t

import sys
import copy
from os.path import realpath, dirname

import types
import inspect

from searx import logger, settings
from searx.utils import load_module

if t.TYPE_CHECKING:
    from searx.enginelib import Engine

logger = logger.getChild('engines')
ENGINE_DIR = dirname(realpath(__file__))

# Defaults for the namespace of an engine module, see load_engine()
ENGINE_DEFAULT_ARGS: dict[str, int | str | list[t.Any] | dict[str, t.Any] | bool] = {
    # Common options in the engine module
    "engine_type": "online",
    "paging": False,
    "time_range_support": False,
    "safesearch": False,
    # settings.yml
    "categories": ["general"],
    "enable_http": False,
    "shortcut": "-",
    "timeout": settings["outgoing"]["request_timeout"],
    "display_error_messages": True,
    "disabled": False,
    "inactive": False,
    "about": {},
    "using_tor_proxy": False,
    "send_accept_language_header": False,
    "tokens": [],
    "max_page": 0,
}
# set automatically when an engine does not have any tab category
DEFAULT_CATEGORY = 'other'

categories: "dict[str, list[Engine|types.ModuleType]]" = {'general': []}

engines: "dict[str, Engine | types.ModuleType]" = {}
"""Global registered engine instances."""

engine_shortcuts = {}
"""Simple map of registered *shortcuts* to name of the engine (or ``None``).

::

    engine_shortcuts[engine.shortcut] = engine.name

:meta hide-value:
"""


def check_engine_module(module: types.ModuleType):
    # probe unintentional name collisions / for example name collisions caused
    # by import statements in the engine module ..

    # network: https://github.com/searxng/searxng/issues/762#issuecomment-1605323861
    obj = getattr(module, 'network', None)
    if obj and inspect.ismodule(obj):
        msg = f'type of {module.__name__}.network is a module ({obj.__name__}), expected a string'
        # logger.error(msg)
        raise TypeError(msg)


def load_engine(engine_data: dict[str, t.Any]) -> "Engine | types.ModuleType | None":
    """Load engine from ``engine_data``.

    :param dict engine_data:  Attributes from YAML ``settings:engines/<engine>``
    :return: initialized namespace of the ``<engine>``.

    1. create a namespace and load module of the ``<engine>``
    2. update namespace with the defaults from :py:obj:`ENGINE_DEFAULT_ARGS`
    3. update namespace with values from ``engine_data``

    If engine *is active*, return namespace of the engine, otherwise return
    ``None``.

    This function also returns ``None`` if initialization of the namespace fails
    for one of the following reasons:

    - engine name contains underscore
    - engine name is not lowercase
    - required attribute is not set :py:func:`is_missing_required_attributes`

    """
    # pylint: disable=too-many-return-statements

    engine_name = engine_data.get('name')
    if engine_name is None:
        logger.error('An engine does not have a "name" field')
        return None
    if '_' in engine_name:
        logger.error('Engine name contains underscore: "{}"'.format(engine_name))
        return None

    if engine_name.lower() != engine_name:
        logger.warning('Engine name is not lowercase: "{}", converting to lowercase'.format(engine_name))
        engine_name = engine_name.lower()
        engine_data['name'] = engine_name

    # load_module
    module_name = engine_data.get('engine')
    if module_name is None:
        logger.error('The "engine" field is missing for the engine named "{}"'.format(engine_name))
        return None
    try:
        engine = load_module(module_name + '.py', ENGINE_DIR)
    except (SyntaxError, KeyboardInterrupt, SystemExit, SystemError, ImportError, RuntimeError):
        logger.exception('Fatal exception in engine "{}"'.format(module_name))
        sys.exit(1)
    except BaseException:
        logger.exception('Cannot load engine "{}"'.format(module_name))
        return None

    check_engine_module(engine)
    update_engine_attributes(engine, engine_data)
    update_attributes_for_tor(engine)

    # avoid cyclic imports
    # pylint: disable=import-outside-toplevel
    from searx.enginelib.traits import EngineTraitsMap

    trait_map = EngineTraitsMap.from_data()
    trait_map.set_traits(engine)

    if not is_engine_active(engine):
        return None

    if is_missing_required_attributes(engine):
        return None

    set_loggers(engine, engine_name)

    if not call_engine_setup(engine, engine_data):
        return None

    if not any(cat in settings['categories_as_tabs'] for cat in engine.categories):
        engine.categories.append(DEFAULT_CATEGORY)

    return engine


def set_loggers(engine: "Engine|types.ModuleType", engine_name: str):
    # set the logger for engine
    engine.logger = logger.getChild(engine_name)
    # the engine may have load some other engines
    # may sure the logger is initialized
    # use sys.modules.copy() to avoid "RuntimeError: dictionary changed size during iteration"
    # see https://github.com/python/cpython/issues/89516
    # and https://docs.python.org/3.10/library/sys.html#sys.modules
    modules = sys.modules.copy()
    for module_name, module in modules.items():
        if (
            module_name.startswith("searx.engines")
            and module_name != "searx.engines.__init__"
            and not hasattr(module, "logger")
        ):
            module_engine_name = module_name.split(".")[-1]
            module.logger = logger.getChild(module_engine_name)  # type: ignore


def update_engine_attributes(engine: "Engine | types.ModuleType", engine_data: dict[str, t.Any]):
    # set engine attributes from engine_data
    for param_name, param_value in engine_data.items():
        if param_name == 'categories':
            if isinstance(param_value, str):
                param_value = list(map(str.strip, param_value.split(',')))
            engine.categories = param_value  # type: ignore
        elif hasattr(engine, 'about') and param_name == 'about':
            engine.about = {**engine.about, **engine_data['about']}  # type: ignore
        else:
            setattr(engine, param_name, param_value)

    # set default attributes
    for arg_name, arg_value in ENGINE_DEFAULT_ARGS.items():
        if not hasattr(engine, arg_name):
            setattr(engine, arg_name, copy.deepcopy(arg_value))


def update_attributes_for_tor(engine: "Engine | types.ModuleType"):
    if using_tor_proxy(engine) and hasattr(engine, 'onion_url'):
        engine.search_url = engine.onion_url + getattr(engine, 'search_path', '')  # type: ignore
        engine.timeout += settings['outgoing'].get('extra_proxy_timeout', 0)  # type: ignore


def is_missing_required_attributes(engine: "Engine | types.ModuleType"):
    """An attribute is required when its name doesn't start with ``_`` (underline).
    Required attributes must not be ``None``.

    """
    missing = False
    for engine_attr in dir(engine):
        if not engine_attr.startswith('_') and getattr(engine, engine_attr) is None:
            logger.error('Missing engine config attribute: "{0}.{1}"'.format(engine.name, engine_attr))
            missing = True
    return missing


def using_tor_proxy(engine: "Engine | types.ModuleType"):
    """Return True if the engine configuration declares to use Tor."""
    return settings['outgoing'].get('using_tor_proxy') or getattr(engine, 'using_tor_proxy', False)


def is_engine_active(engine: "Engine | types.ModuleType"):
    # check if engine is inactive
    if engine.inactive is True:
        return False

    # exclude onion engines if not using tor
    if 'onions' in engine.categories and not using_tor_proxy(engine):
        return False

    return True


def call_engine_setup(engine: "Engine | types.ModuleType", engine_data: dict[str, t.Any]) -> bool:
    setup_ok = False
    setup_func = getattr(engine, "setup", None)

    if setup_func is None:
        setup_ok = True
    elif not callable(setup_func):
        logger.error("engine's setup method isn't a callable (is of type: %s)", type(setup_func))
    else:
        try:
            setup_ok = engine.setup(engine_data)
        except Exception as e:  # pylint: disable=broad-except
            logger.exception('exception : {0}'.format(e))

    if not setup_ok:
        logger.error("%s: Engine setup was not successful, engine is set to inactive.", engine.name)
    return setup_ok


def register_engine(engine: "Engine | types.ModuleType"):
    if engine.name in engines:
        logger.error('Engine config error: ambiguous name: {0}'.format(engine.name))
        sys.exit(1)
    engines[engine.name] = engine

    if engine.shortcut in engine_shortcuts:
        logger.error('Engine config error: ambiguous shortcut: {0}'.format(engine.shortcut))
        sys.exit(1)
    engine_shortcuts[engine.shortcut] = engine.name

    for category_name in engine.categories:
        categories.setdefault(category_name, []).append(engine)


def load_engines(engine_list: list[dict[str, t.Any]]):
    """usage: ``engine_list = settings['engines']``"""
    engines.clear()
    engine_shortcuts.clear()
    categories.clear()
    categories['general'] = []
    for engine_data in engine_list:
        if engine_data.get("inactive") is True:
            continue
        engine = load_engine(engine_data)
        if engine:
            register_engine(engine)
        else:
            # if an engine can't be loaded (if for example the engine is missing
            # tor or some other requirements) its set to inactive!
            logger.error("loading engine %s failed: set engine to inactive!", engine_data.get("name", "???"))
            engine_data["inactive"] = True
    return engines
