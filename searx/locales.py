from typing import List, Set
import os
import pathlib

from babel import Locale

LOCALE_NAMES = {
    "ar": "العَرَبِيَّة (Arabic)",
    "fil": "Wikang Filipino (Filipino)",
    "oc": "Lenga D'òc (Occitan)",
    "nl_BE": "Vlaams (Dutch, Belgium)",
}
UI_LOCALE_CODES: List[str] = []
RTL_LOCALES: Set[str] = set()


def _get_name(locale, language_code):
    language_name = locale.get_language_name(language_code).capitalize()
    if language_name and ('a' <= language_name[0] <= 'z'):
        language_name = language_name.capitalize()
    terrirtory_name = locale.get_territory_name(language_code)
    return language_name, terrirtory_name


def _get_locale_name(locale, locale_name):
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
    global LOCALE_NAMES, UI_LOCALE_CODES, RTL_LOCALES
    for dirname in sorted(os.listdir(directory)):
        # Based on https://flask-babel.tkte.ch/_modules/flask_babel.html#Babel.list_translations
        locale_dir = os.path.join(directory, dirname, 'LC_MESSAGES')
        if not os.path.isdir(locale_dir):
            continue
        info = LOCALE_NAMES.get(dirname)
        if not info:
            locale = Locale.parse(dirname)
            LOCALE_NAMES[dirname] = _get_locale_name(locale, dirname)
            if locale.text_direction == 'rtl':
                RTL_LOCALES.add(dirname)
    #
    UI_LOCALE_CODES = [l.replace('_', '-') for l in LOCALE_NAMES]


initialize_locales(pathlib.Path(__file__).parent / 'translations')
