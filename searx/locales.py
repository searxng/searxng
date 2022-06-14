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
}
"""Additional languages SearXNG has translations for but not supported by
python-babel (see :py:obj:`locales_initialize`)."""

LOCALE_BEST_MATCH = {
    "oc": 'fr-FR',
    "szl": "pl",
    "nl-BE": "nl",
    "zh-HK": "zh-Hant-TW",
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
