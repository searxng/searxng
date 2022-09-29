#!/usr/bin/env python
# lint: pylint
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Update :py:obj:`searx.enginelib.traits.EngineTraitsMap` and :origin:`searx/languages.py`

:py:obj:`searx.enginelib.traits.EngineTraitsMap.ENGINE_TRAITS_FILE`:
  Persistence of engines traits, fetched from the engines.

:origin:`searx/languages.py`
  Is generated  from intersecting each engine's supported traits.

The script :origin:`searxng_extra/update/update_engine_traits.py` is called in
the :origin:`CI Update data ... <.github/workflows/data-update.yml>`

"""

# pylint: disable=invalid-name
from unicodedata import lookup
from pathlib import Path
from pprint import pformat
from babel import Locale, UnknownLocaleError
from babel.languages import get_global
from babel.core import parse_locale

from searx import settings, searx_dir
from searx import network
from searx.engines import load_engines, engines
from searx.enginelib.traits import EngineTraitsMap

# Output files.
languages_file = Path(searx_dir) / 'languages.py'


def fetch_traits_map():
    """Fetchs supported languages for each engine and writes json file with those."""
    network.set_timeout_for_thread(10.0)

    def log(msg):
        print(msg)

    traits_map = EngineTraitsMap.fetch_traits(log=log)
    print("fetched properties from %s engines" % len(traits_map))
    print("write json file: %s" % traits_map.ENGINE_TRAITS_FILE)
    traits_map.save_data()
    return traits_map


# Get babel Locale object from lang_code if possible.
def get_locale(lang_code):
    try:
        locale = Locale.parse(lang_code, sep='-')
        return locale
    except (UnknownLocaleError, ValueError):
        return None


lang2emoji = {
    'ha': '\U0001F1F3\U0001F1EA',  # Hausa / Niger
    'bs': '\U0001F1E7\U0001F1E6',  # Bosnian / Bosnia & Herzegovina
    'jp': '\U0001F1EF\U0001F1F5',  # Japanese
    'ua': '\U0001F1FA\U0001F1E6',  # Ukrainian
    'he': '\U0001F1EE\U0001F1F7',  # Hebrew
}


def get_unicode_flag(lang_code):
    """Determine a unicode flag (emoji) that fits to the ``lang_code``"""

    emoji = lang2emoji.get(lang_code.lower())
    if emoji:
        return emoji

    if len(lang_code) == 2:
        return '\U0001F310'

    language = territory = script = variant = ''
    try:
        language, territory, script, variant = parse_locale(lang_code, '-')
    except ValueError as exc:
        print(exc)

    # https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
    if not territory:
        # https://www.unicode.org/emoji/charts/emoji-list.html#country-flag
        emoji = lang2emoji.get(language)
        if not emoji:
            print(
                "%s --> language: %s / territory: %s / script: %s / variant: %s"
                % (lang_code, language, territory, script, variant)
            )
        return emoji

    emoji = lang2emoji.get(territory.lower())
    if emoji:
        return emoji

    try:
        c1 = lookup('REGIONAL INDICATOR SYMBOL LETTER ' + territory[0])
        c2 = lookup('REGIONAL INDICATOR SYMBOL LETTER ' + territory[1])
        # print("%s --> territory: %s --> %s%s" %(lang_code, territory, c1, c2 ))
    except KeyError as exc:
        print("%s --> territory: %s --> %s" % (lang_code, territory, exc))
        return None

    return c1 + c2


def get_territory_name(lang_code):
    country_name = None
    locale = get_locale(lang_code)
    try:
        if locale is not None:
            country_name = locale.get_territory_name()
    except FileNotFoundError as exc:
        print("ERROR: %s --> %s" % (locale, exc))
    return country_name


def join_language_lists(traits_map: EngineTraitsMap):
    """Join all languages of the engines into one list.  The returned language list
    contains language codes (``zh``) and region codes (``zh-TW``).  The codes can
    be parsed by babel::

      babel.Locale.parse(language_list[n])
    """
    # pylint: disable=too-many-branches
    language_list = {}

    for eng_name, eng_traits in traits_map.items():
        eng = engines[eng_name]
        eng_codes = set()

        if eng_traits.data_type == 'traits_v1':
            # items of type 'engine_traits' do have regions & languages, the
            # list of eng_codes should contain both.
            eng_codes.update(eng_traits.regions.keys())
            eng_codes.update(eng_traits.languages.keys())

        elif eng_traits.data_type == 'supported_languages':
            # vintage / deprecated
            _codes = set()
            if isinstance(eng_traits.supported_languages, dict):
                _codes.update(eng_traits.supported_languages.keys())
            elif isinstance(eng_traits.supported_languages, list):
                _codes.update(eng_traits.supported_languages)
            else:
                raise TypeError('engine.supported_languages type %s is unknown' % type(eng_traits.supported_languages))

            for lang_code in _codes:
                # apply custom fixes if necessary
                if lang_code in getattr(eng, 'language_aliases', {}).values():
                    lang_code = next(lc for lc, alias in eng.language_aliases.items() if lang_code == alias)
                eng_codes.add(lang_code)

        for lang_code in eng_codes:

            locale = get_locale(lang_code)

            # ensure that lang_code uses standard language and country codes
            if locale and locale.territory:
                lang_code = "{lang}-{country}".format(lang=locale.language, country=locale.territory)
            short_code = lang_code.split('-')[0]

            # add language without country if not in list
            if short_code not in language_list:
                if locale:
                    # get language's data from babel's Locale object
                    language_name = locale.get_language_name().title()
                    english_name = locale.english_name.split(' (')[0]
                elif short_code in traits_map['wikipedia'].supported_languages:
                    # get language's data from wikipedia if not known by babel
                    language_name = traits_map['wikipedia'].supported_languages[short_code]['name']
                    english_name = traits_map['wikipedia'].supported_languages[short_code]['english_name']
                else:
                    language_name = None
                    english_name = None

                # add language to list
                language_list[short_code] = {
                    'name': language_name,
                    'english_name': english_name,
                    'counter': set(),
                    'countries': {},
                }

            # add language with country if not in list
            if lang_code != short_code and lang_code not in language_list[short_code]['countries']:
                country_name = ''
                if locale:
                    # get country name from babel's Locale object
                    try:
                        country_name = locale.get_territory_name()
                    except FileNotFoundError as exc:
                        print("ERROR: %s --> %s" % (locale, exc))
                        locale = None

                language_list[short_code]['countries'][lang_code] = {
                    'country_name': country_name,
                    'counter': set(),
                }

            # count engine for both language_country combination and language alone
            language_list[short_code]['counter'].add(eng_name)
            if lang_code != short_code:
                language_list[short_code]['countries'][lang_code]['counter'].add(eng_name)

    return language_list


# Filter language list so it only includes the most supported languages and countries
def filter_language_list(joined_languages_map):
    min_engines_per_lang = 12
    min_engines_per_country = 7
    # pylint: disable=consider-using-dict-items, consider-iterating-dictionary
    main_engines = [
        engine_name
        for engine_name in engines.keys()
        if 'general' in engines[engine_name].categories
        and hasattr(engines[engine_name], 'supported_languages')
        and engines[engine_name].supported_languages
        and not engines[engine_name].disabled
    ]

    # filter list to include only languages supported by most engines or all default general engines
    filtered_languages = {
        code: lang
        for code, lang in joined_languages_map.items()
        if (
            len(lang['counter']) >= min_engines_per_lang
            or all(main_engine in lang['counter'] for main_engine in main_engines)
        )
    }

    def _copy_lang_data(lang, country_name=None):
        new_dict = {}
        new_dict['name'] = joined_languages_map[lang]['name']
        new_dict['english_name'] = joined_languages_map[lang]['english_name']
        if country_name:
            new_dict['country_name'] = country_name
        return new_dict

    # for each language get country codes supported by most engines or at least one country code
    filtered_languages_with_countries = {}
    for lang, lang_data in filtered_languages.items():
        countries = lang_data['countries']
        filtered_countries = {}

        # get language's country codes with enough supported engines
        for lang_country, country_data in countries.items():
            if len(country_data['counter']) >= min_engines_per_country:
                filtered_countries[lang_country] = _copy_lang_data(lang, country_data['country_name'])

        # add language without countries too if there's more than one country to choose from
        if len(filtered_countries) > 1:
            filtered_countries[lang] = _copy_lang_data(lang, None)
        elif len(filtered_countries) == 1:
            lang_country = next(iter(filtered_countries))

        # if no country has enough engines try to get most likely country code from babel
        if not filtered_countries:
            lang_country = None
            subtags = get_global('likely_subtags').get(lang)
            if subtags:
                country_code = subtags.split('_')[-1]
                if len(country_code) == 2:
                    lang_country = "{lang}-{country}".format(lang=lang, country=country_code)

            if lang_country:
                filtered_countries[lang_country] = _copy_lang_data(lang, None)
            else:
                filtered_countries[lang] = _copy_lang_data(lang, None)

        filtered_languages_with_countries.update(filtered_countries)

    return filtered_languages_with_countries


class UnicodeEscape(str):
    """Escape unicode string in :py:obj:`pprint.pformat`"""

    def __repr__(self):
        return "'" + "".join([chr(c) for c in self.encode('unicode-escape')]) + "'"


# Write languages.py.
def write_languages_file(languages):
    file_headers = (
        "# -*- coding: utf-8 -*-",
        "# list of language codes",
        "# this file is generated automatically by utils/fetch_languages.py",
        "language_codes = (\n",
    )

    language_codes = []

    for code in sorted(languages):

        name = languages[code]['name']
        if name is None:
            print("ERROR: languages['%s'] --> %s" % (code, languages[code]))
            continue

        flag = get_unicode_flag(code) or ''
        item = (
            code,
            languages[code]['name'].split(' (')[0],
            get_territory_name(code) or '',
            languages[code].get('english_name') or '',
            UnicodeEscape(flag),
        )

        language_codes.append(item)

    language_codes = tuple(language_codes)

    with open(languages_file, 'w', encoding='utf-8') as new_file:
        file_content = "{file_headers} {language_codes},\n)\n".format(
            # fmt: off
            file_headers = '\n'.join(file_headers),
            language_codes = pformat(language_codes, indent=4)[1:-1]
            # fmt: on
        )
        new_file.write(file_content)
        new_file.close()


def main():
    load_engines(settings['engines'])
    traits_map = fetch_traits_map()
    joined_languages_map = join_language_lists(traits_map)
    filtered_languages = filter_language_list(joined_languages_map)
    write_languages_file(filtered_languages)


if __name__ == "__main__":
    main()
