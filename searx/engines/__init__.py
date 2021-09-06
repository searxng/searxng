# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-function-docstring
"""This module implements the engine loader.

Load and initialize the ``engines``, see :py:func:`load_engines` and register
:py:obj:`engine_shortcuts`.

usage::

    load_engines( settings['engines'] )

"""

import sys
import copy

from os.path import realpath, dirname
from babel.localedata import locale_identifiers
from searx import logger, settings
from searx.data import ENGINES_LANGUAGES
from searx.network import get
from searx.utils import load_module, match_language, gen_useragent


logger = logger.getChild('engines')
ENGINE_DIR = dirname(realpath(__file__))
BABEL_LANGS = [
    lang_parts[0] + '-' + lang_parts[-1] if len(lang_parts) > 1 else lang_parts[0]
    for lang_parts in (lang_code.split('_') for lang_code in locale_identifiers())
]
ENGINE_DEFAULT_ARGS = {
    "engine_type": "online",
    "inactive": False,
    "disabled": False,
    "timeout": settings["outgoing"]["request_timeout"],
    "shortcut": "-",
    "categories": ["general"],
    "supported_languages": [],
    "language_aliases": {},
    "paging": False,
    "safesearch": False,
    "time_range_support": False,
    "enable_http": False,
    "display_error_messages": True,
    "tokens": [],
}
"""Defaults for the namespace of an engine module, see :py:func:`load_engine`"""

categories = {'general': []}
engines = {}
engine_shortcuts = {}
"""Simple map of registered *shortcuts* to name of the engine (or ``None``).

::

    engine_shortcuts[engine.shortcut] = engine.name

"""

def load_engine(engine_data):
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

    engine_name = engine_data['name']
    if '_' in engine_name:
        logger.error('Engine name contains underscore: "{}"'.format(engine_name))
        return None

    if engine_name.lower() != engine_name:
        logger.warn('Engine name is not lowercase: "{}", converting to lowercase'.format(engine_name))
        engine_name = engine_name.lower()
        engine_data['name'] = engine_name

    # load_module
    engine_module = engine_data['engine']
    try:
        engine = load_module(engine_module + '.py', ENGINE_DIR)
    except (SyntaxError, KeyboardInterrupt, SystemExit, SystemError, ImportError, RuntimeError):
        logger.exception('Fatal exception in engine "{}"'.format(engine_module))
        sys.exit(1)
    except BaseException:
        logger.exception('Cannot load engine "{}"'.format(engine_module))
        return None

    update_engine_attributes(engine, engine_data)
    set_language_attributes(engine)
    update_attributes_for_tor(engine)

    if not is_engine_active(engine):
        return None

    if is_missing_required_attributes(engine):
        return None

    engine.logger = logger.getChild(engine_name)
    return engine


def update_engine_attributes(engine, engine_data):
    # set engine attributes from engine_data
    for param_name, param_value in engine_data.items():
        if param_name == 'categories':
            if isinstance(param_value, str):
                param_value = list(map(str.strip, param_value.split(',')))
            engine.categories = param_value
        elif param_name != 'engine':
            setattr(engine, param_name, param_value)

    # set default attributes
    for arg_name, arg_value in ENGINE_DEFAULT_ARGS.items():
        if not hasattr(engine, arg_name):
            setattr(engine, arg_name, copy.deepcopy(arg_value))


def set_language_attributes(engine):
    # pylint: disable=protected-access
    # assign supported languages from json file
    if engine.name in ENGINES_LANGUAGES:
        engine.supported_languages = ENGINES_LANGUAGES[engine.name]

    # find custom aliases for non standard language codes
    for engine_lang in engine.supported_languages:
        iso_lang = match_language(engine_lang, BABEL_LANGS, fallback=None)
        if (iso_lang
            and iso_lang != engine_lang
            and not engine_lang.startswith(iso_lang)
            and iso_lang not in engine.supported_languages
        ):
            engine.language_aliases[iso_lang] = engine_lang

    # language_support
    engine.language_support = len(engine.supported_languages) > 0

    # assign language fetching method if auxiliary method exists
    if hasattr(engine, '_fetch_supported_languages'):
        headers = {
            'User-Agent': gen_useragent(),
            'Accept-Language': 'ja-JP,ja;q=0.8,en-US;q=0.5,en;q=0.3',  # bing needs a non-English language
        }
        engine.fetch_supported_languages = (
            lambda: engine._fetch_supported_languages(
                get(engine.supported_languages_url, headers=headers))
        )


def update_attributes_for_tor(engine):
    if (settings['outgoing'].get('using_tor_proxy')
        and hasattr(engine, 'onion_url') ):
        engine.search_url = engine.onion_url + getattr(engine, 'search_path', '')
        engine.timeout += settings['outgoing'].get('extra_proxy_timeout', 0)


def is_missing_required_attributes(engine):
    """An attribute is required when its name doesn't start with ``_`` (underline).
    Required attributes must not be ``None``.

    """
    missing = False
    for engine_attr in dir(engine):
        if not engine_attr.startswith('_') and getattr(engine, engine_attr) is None:
            logger.error(
                'Missing engine config attribute: "{0}.{1}"'
                .format(engine.name, engine_attr))
            missing = True
    return missing


def is_engine_active(engine):
    # check if engine is inactive
    if engine.inactive is True:
        return False

    # exclude onion engines if not using tor
    if ('onions' in engine.categories
        and not settings['outgoing'].get('using_tor_proxy') ):
        return False

    return True


def register_engine(engine):
    if engine.name in engines:
        logger.error('Engine config error: ambigious name: {0}'.format(engine.name))
        sys.exit(1)
    engines[engine.name] = engine

    if engine.shortcut in engine_shortcuts:
        logger.error('Engine config error: ambigious shortcut: {0}'.format(engine.shortcut))
        sys.exit(1)
    engine_shortcuts[engine.shortcut] = engine.name

    for category_name in engine.categories:
        categories.setdefault(category_name, []).append(engine)


def load_engines(engine_list):
    """usage: ``engine_list = settings['engines']``
    """
    engines.clear()
    engine_shortcuts.clear()
    categories.clear()
    categories['general'] = []
    for engine_data in engine_list:
        engine = load_engine(engine_data)
        if engine:
            register_engine(engine)
    return engines
