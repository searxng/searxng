# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Initialize :py:obj:`LOCALE_NAMES`, :py:obj:`RTL_LOCALES`.
"""

from typing import Set
import os
import pathlib

from babel import Locale
from babel.support import Translations
import babel.languages
import babel.core
import flask_babel
import flask
from flask.ctx import has_request_context
from searx import logger

logger = logger.getChild('locales')


# safe before monkey patching flask_babel.get_translations
_flask_babel_get_translations = flask_babel.get_translations

LOCALE_NAMES = {}
"""Mapping of locales and their description.  Locales e.g. 'fr' or 'pt-BR' (see
:py:obj:`locales_initialize`)."""

RTL_LOCALES: Set[str] = set()
"""List of *Right-To-Left* locales e.g. 'he' or 'fa-IR' (see
:py:obj:`locales_initialize`)."""

ADDITIONAL_TRANSLATIONS = {
    "oc": "Occitan",
    "szl": "Ślōnski (Silesian)",
    "pap": "Papiamento",
}
"""Additional languages SearXNG has translations for but not supported by
python-babel (see :py:obj:`locales_initialize`)."""

LOCALE_BEST_MATCH = {
    "oc": 'fr-FR',
    "szl": "pl",
    "nl-BE": "nl",
    "zh-HK": "zh-Hant-TW",
    "pap": "pt-BR",
}
"""Map a locale we do not have a translations for to a locale we have a
translation for. By example: use Taiwan version of the translation for Hong
Kong."""


def localeselector():
    locale = 'en'
    if has_request_context():
        value = flask.request.preferences.get_value('locale')
        if value:
            locale = value

    # first, set the language that is not supported by babel
    if locale in ADDITIONAL_TRANSLATIONS:
        flask.request.form['use-translation'] = locale

    # second, map locale to a value python-babel supports
    locale = LOCALE_BEST_MATCH.get(locale, locale)

    if locale == '':
        # if there is an error loading the preferences
        # the locale is going to be ''
        locale = 'en'

    # babel uses underscore instead of hyphen.
    locale = locale.replace('-', '_')
    return locale


def get_translations():
    """Monkey patch of :py:obj:`flask_babel.get_translations`"""
    if has_request_context() and flask.request.form.get('use-translation') == 'oc':
        babel_ext = flask_babel.current_app.extensions['babel']
        return Translations.load(next(babel_ext.translation_directories), 'oc')
    if has_request_context() and flask.request.form.get('use-translation') == 'szl':
        babel_ext = flask_babel.current_app.extensions['babel']
        return Translations.load(next(babel_ext.translation_directories), 'szl')
    if has_request_context() and flask.request.form.get('use-translation') == 'pap':
        babel_ext = flask_babel.current_app.extensions['babel']
        return Translations.load(next(babel_ext.translation_directories), 'pap')
    return _flask_babel_get_translations()


def get_locale_descr(locale, locale_name):
    """Get locale name e.g. 'Français - fr' or 'Português (Brasil) - pt-BR'

    :param locale: instance of :py:class:`Locale`
    :param locale_name: name e.g. 'fr'  or 'pt_BR' (delimiter is *underscore*)
    """

    native_language, native_territory = _get_locale_descr(locale, locale_name)
    english_language, english_territory = _get_locale_descr(locale, 'en')

    if native_territory == english_territory:
        english_territory = None

    if not native_territory and not english_territory:
        if native_language == english_language:
            return native_language
        return native_language + ' (' + english_language + ')'

    result = native_language + ', ' + native_territory + ' (' + english_language
    if english_territory:
        return result + ', ' + english_territory + ')'
    return result + ')'


def _get_locale_descr(locale, language_code):
    language_name = locale.get_language_name(language_code).capitalize()
    if language_name and ('a' <= language_name[0] <= 'z'):
        language_name = language_name.capitalize()
    terrirtory_name = locale.get_territory_name(language_code)
    return language_name, terrirtory_name


def locales_initialize(directory=None):
    """Initialize locales environment of the SearXNG session.

    - monkey patch :py:obj:`flask_babel.get_translations` by :py:obj:`get_translations`
    - init global names :py:obj:`LOCALE_NAMES`, :py:obj:`RTL_LOCALES`
    """

    directory = directory or pathlib.Path(__file__).parent / 'translations'
    logger.debug("locales_initialize: %s", directory)
    flask_babel.get_translations = get_translations

    for tag, descr in ADDITIONAL_TRANSLATIONS.items():
        LOCALE_NAMES[tag] = descr

    for tag in LOCALE_BEST_MATCH:
        descr = LOCALE_NAMES.get(tag)
        if not descr:
            locale = Locale.parse(tag, sep='-')
            LOCALE_NAMES[tag] = get_locale_descr(locale, tag.replace('-', '_'))

    for dirname in sorted(os.listdir(directory)):
        # Based on https://flask-babel.tkte.ch/_modules/flask_babel.html#Babel.list_translations
        if not os.path.isdir(os.path.join(directory, dirname, 'LC_MESSAGES')):
            continue
        tag = dirname.replace('_', '-')
        descr = LOCALE_NAMES.get(tag)
        if not descr:
            locale = Locale.parse(dirname)
            LOCALE_NAMES[tag] = get_locale_descr(locale, dirname)
            if locale.text_direction == 'rtl':
                RTL_LOCALES.add(tag)


def get_engine_locale(searxng_locale, engine_locales, default=None):
    """Return engine's language (aka locale) string that best fits to argument
    ``searxng_locale``.

    Argument ``engine_locales`` is a python dict that maps *SearXNG locales* to
    corresponding *engine locales*:

      <engine>: {
          # SearXNG string : engine-string
          'ca-ES'          : 'ca_ES',
          'fr-BE'          : 'fr_BE',
          'fr-CA'          : 'fr_CA',
          'fr-CH'          : 'fr_CH',
          'fr'             : 'fr_FR',
          ...
          'pl-PL'          : 'pl_PL',
          'pt-PT'          : 'pt_PT'
      }

    .. hint::

       The *SearXNG locale* string has to be known by babel!

    If there is no direct 1:1 mapping, this functions tries to narrow down
    engine's language (locale).  If no value can be determined by these
    approximation attempts the ``default`` value is returned.

    Assumptions:

    A. When user select a language the results should be optimized according to
       the selected language.

    B. When user select a language and a territory the results should be
       optimized with first priority on terrirtory and second on language.

    First approximation rule (*by territory*):

      When the user selects a locale with terrirtory (and a language), the
      territory has priority over the language.  If any of the offical languages
      in the terrirtory is supported by the engine (``engine_locales``) it will
      be used.

    Second approximation rule (*by language*):

      If "First approximation rule" brings no result or the user selects only a
      language without a terrirtory.  Check in which territories the language
      has an offical status and if one of these territories is supported by the
      engine.

    """
    # pylint: disable=too-many-branches

    engine_locale = engine_locales.get(searxng_locale)

    if engine_locale is not None:
        # There was a 1:1 mapping (e.g. "fr-BE --> fr_BE" or "fr --> fr_FR"), no
        # need to narrow language nor territory.
        return engine_locale

    try:
        locale = babel.Locale.parse(searxng_locale, sep='-')
    except babel.core.UnknownLocaleError:
        try:
            locale = babel.Locale.parse(searxng_locale.split('-')[1])
        except babel.core.UnknownLocaleError:
            return default

    # SearXNG's selected locale is not supported by the engine ..

    if locale.territory:
        # Try to narrow by *offical* languages in the territory (??-XX).

        for official_language in babel.languages.get_official_languages(locale.territory, de_facto=True):
            searxng_locale = official_language + '-' + locale.territory
            engine_locale = engine_locales.get(searxng_locale)
            if engine_locale is not None:
                return engine_locale

    # Engine does not support one of the offical languages in the territory or
    # there is only a language selected without a territory.

    # Now lets have a look if the searxng_lang (the language selected by the
    # user) is a offical language in other territories.  If so, check if
    # engine does support the searxng_lang in this other territory.

    if locale.language:

        searxng_lang = locale.language
        if locale.script:
            searxng_lang += '_' + locale.script

        terr_lang_dict = {}
        for territory, langs in babel.core.get_global("territory_languages").items():
            if not langs.get(searxng_lang, {}).get('official_status'):
                continue
            terr_lang_dict[territory] = langs.get(searxng_lang)

        # first: check fr-FR, de-DE .. is supported by the engine

        territory = locale.language.upper()
        if terr_lang_dict.get(territory):
            searxng_locale = locale.language + '-' + territory
            engine_locale = engine_locales.get(searxng_locale)
            if engine_locale is not None:
                return engine_locale

        # second: sort by population_percent and take first match

        # drawback of "population percent": if there is a terrirtory with a
        #   small number of people (e.g 100) but the majority speaks the
        #   language, then the percentage migth be 100% (--> 100 people) but in
        #   a different terrirtory with more people (e.g. 10.000) where only 10%
        #   speak the language the total amount of speaker is higher (--> 200
        #   people).
        #
        #   By example: The population of Saint-Martin is 33.000, of which 100%
        #   speak French, but this is less than the 30% of the approximately 2.5
        #   million Belgian citizens
        #
        #   - 'fr-MF', 'population_percent': 100.0, 'official_status': 'official'
        #   - 'fr-BE', 'population_percent': 38.0, 'official_status': 'official'

        terr_lang_list = []
        for k, v in terr_lang_dict.items():
            terr_lang_list.append((k, v))

        for territory, _lang in sorted(terr_lang_list, key=lambda item: item[1]['population_percent'], reverse=True):
            searxng_locale = locale.language + '-' + territory
            engine_locale = engine_locales.get(searxng_locale)
            if engine_locale is not None:
                return engine_locale

    # No luck: narrow by "language from territory" and "territory from language"
    # does not fit to a locale supported by the engine.

    if engine_locale is None:
        engine_locale = default

    return default
