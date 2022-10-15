# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This module implements the engine loader.

Load and initialize the ``engines``, see :py:func:`load_engines` and register
:py:obj:`engine_shortcuts`.

usage::

    load_engines( settings['engines'] )

"""

import sys
import copy
import dataclasses
from typing import Dict, List, Optional, Any

from os.path import realpath, dirname
from babel.localedata import locale_identifiers
from searx import logger, settings, locales
from searx.data import ENGINES_LANGUAGES, ENGINES_LOCALES
from searx.utils import load_module, match_language


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
    "using_tor_proxy": False,
    "display_error_messages": True,
    "send_accept_language_header": False,
    "tokens": [],
    "about": {},
}
# set automatically when an engine does not have any tab category
OTHER_CATEGORY = 'other'


@dataclasses.dataclass
class EngineLocales:
    """The class is intended to be instanciated for each engine."""

    regions: Dict[str, str] = dataclasses.field(default_factory=dict)
    """
    .. code:: python
       {
           'fr-BE' : <engine's region name>,
       }
    """

    languages: Dict[str, str] = dataclasses.field(default_factory=dict)
    """
    .. code:: python
       {
           'ca' : <engine's language name>,
       }
    """

    all_locale: Optional[str] = None
    """To which locale value SearXNG's ``all`` language is mapped (shown a "Default
    language").
    """

    def get_language(self, searxng_locale: str, default: Optional[str] = None):
        """Return engine's language string that *best fits* to SearXNG's locale.
        :param searxng_locale: SearXNG's internal representation of locale
          selected by the user.
        :param default: engine's default language
        The *best fits* rules are implemented in
        :py:obj:`locales.get_engine_locale`.  Except for the special value ``all``
        which is determined from :py:obj`EngineTraits.all_language`.
        """
        if searxng_locale == 'all' and self.all_locale is not None:
            return self.all_locale
        sxng_lang = searxng_locale.split('-')[0]
        return locales.get_engine_locale(sxng_lang, self.languages, default=default)

    def get_region(self, searxng_locale: str, default: Optional[str] = None):
        """Return engine's region string that best fits to SearXNG's locale.
        :param searxng_locale: SearXNG's internal representation of locale
          selected by the user.
        :param default: engine's default region
        The *best fits* rules are implemented in
        :py:obj:`locales.get_engine_locale`.  Except for the special value ``all``
        which is determined from :py:obj`EngineTraits.all_language`.
        """
        if searxng_locale == 'all' and self.all_locale is not None:
            return self.all_locale
        return locales.get_engine_locale(searxng_locale, self.regions, default=default)

    def is_locale_supported(self, searxng_locale: str) -> bool:
        """A *locale* (SearXNG's internal representation) is considered to be supported
        by the engine if the *region* or the *language* is supported by the
        engine.  For verification the functions :py:func:`self.get_region` and
        :py:func:`self.get_region` are used.
        """
        return bool(self.get_region(searxng_locale) or self.get_language(searxng_locale))

    @classmethod
    def load(
        cls, engine_locales_key: str, language: Optional[str] = None, region: Optional[str] = None
    ) -> "EngineLocales":
        #
        engine_locales_value = {**ENGINES_LOCALES[engine_locales_key]}

        _msg = "settings.yml - engine: '%s' / %s: '%s' not supported"

        if language is not None:
            el_languages = engine_locales_value['languages']
            if language not in el_languages:
                raise ValueError(_msg % (engine_locales_key, 'language', language))
            engine_locales_value['languages'] = {language: el_languages[language]}

        if region is not None:
            el_regions = engine_locales_value['regions']
            if region in el_regions:
                raise ValueError(_msg % (engine_locales_key, 'region', region))
            engine_locales_value['regions'] = {region: el_regions[region]}

        return cls(**engine_locales_value)

    @classmethod
    def exists(cls, engine_locales_key: str):
        return engine_locales_key in ENGINES_LOCALES


class Engine:  # pylint: disable=too-few-public-methods
    """This class is currently never initialized and only used for type hinting."""

    name: str
    engine: str
    shortcut: str
    categories: List[str]
    about: dict
    inactive: bool
    disabled: bool
    paging: bool
    safesearch: bool
    time_range_support: bool
    timeout: float
    language_support: bool
    engine_locales: EngineLocales
    supported_languages: List[str]
    language_aliases: Dict[str, str]


# Defaults for the namespace of an engine module, see :py:func:`load_engine`

categories = {'general': []}
engines: Dict[str, Engine] = {}
engine_shortcuts = {}
"""Simple map of registered *shortcuts* to name of the engine (or ``None``).

::

    engine_shortcuts[engine.shortcut] = engine.name

:meta hide-value:
"""


def load_engine(engine_setting: Dict[str, Any]) -> Optional[Engine]:
    """Load engine from ``engine_setting``.

    :param dict engine_setting:  Attributes from YAML ``settings:engines/<engine>``
    :return: initialized namespace of the ``<engine>``.

    1. create a namespace and load module of the ``<engine>``
    2. update namespace with the defaults from :py:obj:`ENGINE_DEFAULT_ARGS`
    3. update namespace with values from ``engine_setting``

    If engine *is active*, return namespace of the engine, otherwise return
    ``None``.

    This function also returns ``None`` if initialization of the namespace fails
    for one of the following reasons:

    - engine name contains underscore
    - engine name is not lowercase
    - required attribute is not set :py:func:`is_missing_required_attributes`

    """

    engine_name = engine_setting['name']
    if '_' in engine_name:
        logger.error('Engine name contains underscore: "{}"'.format(engine_name))
        return None

    if engine_name.lower() != engine_name:
        logger.warn('Engine name is not lowercase: "{}", converting to lowercase'.format(engine_name))
        engine_name = engine_name.lower()
        engine_setting['name'] = engine_name

    # load_module
    engine_module = engine_setting['engine']
    try:
        engine = load_module(engine_module + '.py', ENGINE_DIR)
    except (SyntaxError, KeyboardInterrupt, SystemExit, SystemError, ImportError, RuntimeError):
        logger.exception('Fatal exception in engine "{}"'.format(engine_module))
        sys.exit(1)
    except BaseException:
        logger.exception('Cannot load engine "{}"'.format(engine_module))
        return None

    update_engine_attributes(engine, engine_setting)
    update_attributes_for_tor(engine)
    if not set_engine_locales(engine):
        set_language_attributes(engine)

    if not is_engine_active(engine):
        return None

    if is_missing_required_attributes(engine):
        return None

    set_loggers(engine, engine_name)

    if not any(cat in settings['categories_as_tabs'] for cat in engine.categories):
        engine.categories.append(OTHER_CATEGORY)

    return engine


def set_loggers(engine, engine_name):
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
            module.logger = logger.getChild(module_engine_name)


def update_engine_attributes(engine: Engine, engine_setting: Dict[str, Any]):
    # set engine attributes from engine_setting
    for param_name, param_value in engine_setting.items():
        if param_name == 'categories':
            if isinstance(param_value, str):
                param_value = list(map(str.strip, param_value.split(',')))
            engine.categories = param_value
        elif hasattr(engine, 'about') and param_name == 'about':
            engine.about = {**engine.about, **engine_setting['about']}
        else:
            setattr(engine, param_name, param_value)

    # set default attributes
    for arg_name, arg_value in ENGINE_DEFAULT_ARGS.items():
        if not hasattr(engine, arg_name):
            setattr(engine, arg_name, copy.deepcopy(arg_value))


def set_engine_locales(engine: Engine):
    engine_locales_key = None

    if EngineLocales.exists(engine.name):
        engine_locales_key = engine.name
    elif EngineLocales.exists(engine.engine):
        # The key of the dictionary engine_data_dict is the *engine name*
        # configured in settings.xml.  When multiple engines are configured in
        # settings.yml to use the same origin engine (python module) these
        # additional engines can use the languages from the origin engine.
        # For this use the configured ``engine: ...`` from settings.yml
        engine_locales_key = engine.engine
    else:
        return False

    #
    engine.engine_locales = EngineLocales.load(
        engine_locales_key, getattr(engine, 'language', None), getattr(engine, 'region', None)
    )

    # language_support
    # NOTE: actually the value should be true, or the entry in engine_locales.json should not exists.
    engine.language_support = len(engine.engine_locales.regions) > 0 or len(engine.engine_locales.languages) > 0
    return True


def set_language_attributes(engine: Engine):
    # assign supported languages from json file
    if engine.name in ENGINES_LANGUAGES:
        engine.supported_languages = ENGINES_LANGUAGES[engine.name]

    elif engine.engine in ENGINES_LANGUAGES:
        # The key of the dictionary ENGINES_LANGUAGES is the *engine name*
        # configured in settings.xml.  When multiple engines are configured in
        # settings.yml to use the same origin engine (python module) these
        # additional engines can use the languages from the origin engine.
        # For this use the configured ``engine: ...`` from settings.yml
        engine.supported_languages = ENGINES_LANGUAGES[engine.engine]

    if hasattr(engine, 'language'):
        # For an engine, when there is `language: ...` in the YAML settings, the
        # engine supports only one language, in this case
        # engine.supported_languages should contains this value defined in
        # settings.yml
        if engine.language not in engine.supported_languages:
            raise ValueError(
                "settings.yml - engine: '%s' / language: '%s' not supported" % (engine.name, engine.language)
            )

        if isinstance(engine.supported_languages, dict):
            engine.supported_languages = {engine.language: engine.supported_languages[engine.language]}
        else:
            engine.supported_languages = [engine.language]

    # find custom aliases for non standard language codes
    for engine_lang in engine.supported_languages:
        iso_lang = match_language(engine_lang, BABEL_LANGS, fallback=None)
        if (
            iso_lang
            and iso_lang != engine_lang
            and not engine_lang.startswith(iso_lang)
            and iso_lang not in engine.supported_languages
        ):
            engine.language_aliases[iso_lang] = engine_lang

    # language_support
    engine.language_support = len(engine.supported_languages) > 0


def update_attributes_for_tor(engine: Engine) -> bool:
    if using_tor_proxy(engine) and hasattr(engine, 'onion_url'):
        engine.search_url = engine.onion_url + getattr(engine, 'search_path', '')
        engine.timeout += settings['outgoing'].get('extra_proxy_timeout', 0)


def is_missing_required_attributes(engine):
    """An attribute is required when its name doesn't start with ``_`` (underline).
    Required attributes must not be ``None``.

    """
    missing = False
    for engine_attr in dir(engine):
        if not engine_attr.startswith('_') and getattr(engine, engine_attr) is None:
            logger.error('Missing engine config attribute: "{0}.{1}"'.format(engine.name, engine_attr))
            missing = True
    return missing


def using_tor_proxy(engine: Engine):
    """Return True if the engine configuration declares to use Tor."""
    return settings['outgoing'].get('using_tor_proxy') or getattr(engine, 'using_tor_proxy', False)


def is_engine_active(engine: Engine):
    # check if engine is inactive
    if engine.inactive is True:
        return False

    # exclude onion engines if not using tor
    if 'onions' in engine.categories and not using_tor_proxy(engine):
        return False

    return True


def register_engine(engine: Engine):
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


def load_engines(engine_list):
    """usage: ``engine_list = settings['engines']``"""
    engines.clear()
    engine_shortcuts.clear()
    categories.clear()
    categories['general'] = []
    for engine_setting in engine_list:
        engine = load_engine(engine_setting)
        if engine:
            register_engine(engine)
    return engines
