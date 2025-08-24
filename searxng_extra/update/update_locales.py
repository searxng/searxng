#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Update locale names in :origin:`searx/data/locales.json` used by
:ref:`searx.locales`

- :py:obj:`searx.locales.RTL_LOCALES`
- :py:obj:`searx.locales.LOCALE_NAMES`
"""
# pylint: disable=invalid-name

from typing import Set
import json
from pathlib import Path

import babel
import babel.languages
import babel.core

from searx import searx_dir
from searx.locales import (
    ADDITIONAL_TRANSLATIONS,
    LOCALE_BEST_MATCH,
    get_translation_locales,
)

LOCALE_DATA_FILE = Path(searx_dir) / 'data' / 'locales.json'
TRANSLATIONS_FOLDER = Path(searx_dir) / 'translations'


def main():

    LOCALE_NAMES = {}
    RTL_LOCALES: Set[str] = set()

    for tag, descr in ADDITIONAL_TRANSLATIONS.items():
        locale = babel.Locale.parse(LOCALE_BEST_MATCH[tag], sep='-')
        LOCALE_NAMES[tag] = descr
        if locale.text_direction == 'rtl':
            RTL_LOCALES.add(tag)

    for tag in LOCALE_BEST_MATCH:
        descr = LOCALE_NAMES.get(tag)
        if not descr:
            locale = babel.Locale.parse(tag, sep='-')
            LOCALE_NAMES[tag] = get_locale_descr(locale, tag.replace('-', '_'))
            if locale.text_direction == 'rtl':
                RTL_LOCALES.add(tag)

    for tr_locale in get_translation_locales():
        sxng_tag = tr_locale.replace('_', '-')
        descr = LOCALE_NAMES.get(sxng_tag)
        if not descr:
            locale = babel.Locale.parse(tr_locale)
            LOCALE_NAMES[sxng_tag] = get_locale_descr(locale, tr_locale)
            if locale.text_direction == 'rtl':
                RTL_LOCALES.add(sxng_tag)

    content = {
        "LOCALE_NAMES": LOCALE_NAMES,
        "RTL_LOCALES": sorted(RTL_LOCALES),
    }

    with LOCALE_DATA_FILE.open('w', encoding='utf-8') as f:
        json.dump(content, f, indent=2, sort_keys=True, ensure_ascii=False)


def get_locale_descr(locale: babel.Locale, tr_locale):
    """Get locale name e.g. 'Français - fr' or 'Português (Brasil) - pt-BR'

    :param locale: instance of :py:class:`Locale`
    :param tr_locale: name e.g. 'fr'  or 'pt_BR' (delimiter is *underscore*)
    """

    native_language, native_territory = _get_locale_descr(locale, tr_locale)
    english_language, english_territory = _get_locale_descr(locale, 'en')

    if native_territory == english_territory:
        english_territory = None

    if not native_territory and not english_territory:
        # none territory name
        if native_language == english_language:
            return native_language
        return native_language + ' (' + english_language + ')'

    result = native_language + ', ' + native_territory + ' (' + english_language
    if english_territory:
        return result + ', ' + english_territory + ')'
    return result + ')'


def _get_locale_descr(locale: babel.Locale, tr_locale: str) -> tuple[str, str]:
    language_name = locale.get_language_name(tr_locale).capitalize()  # type: ignore
    if language_name and ('a' <= language_name[0] <= 'z'):
        language_name = language_name.capitalize()
    territory_name: str = locale.get_territory_name(tr_locale)  # type: ignore
    return language_name, territory_name


if __name__ == "__main__":
    main()
