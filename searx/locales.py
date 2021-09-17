# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Initialize :py:obj:`LOCALE_NAMES`, :py:obj:`UI_LOCALE_CODES` and
:py:obj:`RTL_LOCALES`."""

from typing import List, Set
import os
import pathlib

from babel import Locale

LOCALE_NAMES = {
    "oc": "Occitan",
    "nl_BE": "Vlaams (Dutch, Belgium)",
}
"""Mapping of locales and their description.  Locales e.g. 'fr' or 'pt_BR'
(delimiter is *underline* '_')"""

UI_LOCALE_CODES: List[str] = []
"""List of locales e.g. 'fr' or 'pt-BR' (delimiter is '-')"""

RTL_LOCALES: Set[str] = set()
"""List of *Right-To-Left* locales e.g. 'he' or 'fa_IR' (delimiter is
*underline* '_')"""


def _get_name(locale, language_code):
    language_name = locale.get_language_name(language_code).capitalize()
    if language_name and ('a' <= language_name[0] <= 'z'):
        language_name = language_name.capitalize()
    terrirtory_name = locale.get_territory_name(language_code)
    return language_name, terrirtory_name


def _get_locale_name(locale, locale_name):
    """Get locale name e.g. 'Français - fr' or 'Português (Brasil) - pt-BR'

    :param locale: instance of :py:class:`Locale`
    :param locale_name: name e.g. 'fr'  or 'pt_BR'
    """
    native_language, native_territory = _get_name(locale, locale_name)
    english_language, english_territory = _get_name(locale, 'en')
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


def initialize_locales(directory):
    """Initialize global names :py:obj:`LOCALE_NAMES`, :py:obj:`UI_LOCALE_CODES` and
    :py:obj:`RTL_LOCALES`.
    """
    global UI_LOCALE_CODES  # pylint: disable=global-statement
    for dirname in sorted(os.listdir(directory)):
        # Based on https://flask-babel.tkte.ch/_modules/flask_babel.html#Babel.list_translations
        if not os.path.isdir( os.path.join(directory, dirname, 'LC_MESSAGES') ):
            continue
        info = LOCALE_NAMES.get(dirname)
        if not info:
            locale = Locale.parse(dirname)
            LOCALE_NAMES[dirname] = _get_locale_name(locale, dirname)
            if locale.text_direction == 'rtl':
                RTL_LOCALES.add(dirname)

    UI_LOCALE_CODES = [l.replace('_', '-') for l in LOCALE_NAMES]


initialize_locales(pathlib.Path(__file__).parent / 'translations')
