# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Initialize :py:obj:`LOCALE_NAMES`, :py:obj:`RTL_LOCALES`.
"""

from typing import Set, Dict, Optional, Tuple
import os
import pathlib

from babel import Locale

LOCALE_NAMES = {
    "oc": "Occitan",
    "nl-BE": "Vlaams (Dutch, Belgium)",
}
"""Mapping of locales and their description.  Locales e.g. 'fr' or 'pt-BR'
(delimiter is *underline* '-')"""

RTL_LOCALES: Set[str] = set()
"""List of *Right-To-Left* locales e.g. 'he' or 'fa-IR' (delimiter is
*underline* '-')"""


class SupportedLocales:
    """Map the Preferences.get("languages) value to a Locale, a language and a region.

    The class is intended to be instanciated for each engine.
    """

    all_language: Optional[str]
    """
    To which locale value the "all" language is mapped (shown a "Default language")
    """

    regions: Dict[str, str]
    """
    {
        'fr-BE' : <engine's region name>
    },
    """

    languages: Dict[str, str]
    """
    {
        'ca' : <engine's language name>
    },
    """

    @classmethod
    def loads(cls, data):
        if isinstance(data, dict) and 'all_language' in data and 'languages' in data and 'regions' in data:
            return cls(data['all_language'], data['regions'], data['languages'])
        return cls()

    def __init__(self, all_language=None, regions=None, languages=None):
        self.all_language = all_language
        self.regions = regions or {}
        self.languages = languages or {}

    def empty(self):
        return len(self.regions) == 0 and len(self.languages) == 0

    def get(self, language: str) -> Tuple[Optional[Locale], Optional[str], Optional[str]]:
        if language == 'all' and self.all_language is None:
            return None, None, None

        if language == 'all' and self.all_language is not None:
            language = self.all_language

        locale = Locale.parse(language, sep='-')

        engine_language = self.languages.get(locale.language)

        engine_region = None
        if locale.territory:
            engine_region = self.regions.get(locale.language + '-' + locale.territory)

        return locale, engine_language, engine_region

    def dumps(self):
        return {
            'all_language': self.all_language,
            'regions': self.regions,
            'languages': self.languages,
        }


def _get_name(locale, language_code):
    language_name = locale.get_language_name(language_code).capitalize()
    if language_name and ('a' <= language_name[0] <= 'z'):
        language_name = language_name.capitalize()
    terrirtory_name = locale.get_territory_name(language_code)
    return language_name, terrirtory_name


def _get_locale_name(locale, locale_name):
    """Get locale name e.g. 'Français - fr' or 'Português (Brasil) - pt-BR'

    :param locale: instance of :py:class:`Locale`
    :param locale_name: name e.g. 'fr'  or 'pt_BR' (delimiter is *underscore*)
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
    """Initialize global names :py:obj:`LOCALE_NAMES`, :py:obj:`RTL_LOCALES`."""
    for dirname in sorted(os.listdir(directory)):
        # Based on https://flask-babel.tkte.ch/_modules/flask_babel.html#Babel.list_translations
        if not os.path.isdir(os.path.join(directory, dirname, 'LC_MESSAGES')):
            continue
        locale_name = dirname.replace('_', '-')
        info = LOCALE_NAMES.get(locale_name)
        if not info:
            locale = Locale.parse(dirname)
            LOCALE_NAMES[locale_name] = _get_locale_name(locale, dirname)
            if locale.text_direction == 'rtl':
                RTL_LOCALES.add(locale_name)


initialize_locales(pathlib.Path(__file__).parent / 'translations')
