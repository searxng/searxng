#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pyright: basic
"""This script fetches engine data from engines `engine_data_url`` and updates:

- :py:obj:`write_languages_file` updates :origin:`searx/languages.py`
- :py:obj:`fetch_engine_data` updates :origin:`searx/data/engines_datas.json`

This script is triggered by CI in job :origin:`updateData
<.github/workflows/data-update.yml>`.
"""

# pylint: disable=invalid-name
import json
from unicodedata import lookup
from pprint import pformat
from pathlib import Path
from typing import Dict, Generator, List, Set, Tuple, Union, Optional
from typing_extensions import TypedDict, NotRequired

from babel import Locale, UnknownLocaleError
from babel.languages import get_global  # type: ignore
from babel.core import parse_locale

from searx import settings, searx_dir
from searx import network
from searx.data import data_dir
from searx.engines import (
    load_engines,
    engines,
    EngineLocales,
)
from searx.utils import gen_useragent


class EngineLanguageDescDict(TypedDict):
    """In data/engines_languages.json, for google, wikipedia and wikidata engines:
    value of the dictionnaries"""

    name: str
    english_name: NotRequired[str]


EngineLanguageDesc = Union[List[str], Dict[str, EngineLanguageDescDict]]
"""In data/engines_languages.json, type for a engine:

* either it is a list
* or a dictionnary"""

EngineLanguageDict = Dict[str, EngineLanguageDesc]
"""Type description for data/engines_languages.json"""

EngineLocalesDict = Dict[str, EngineLocales]
"""Type description for data/engine_data.json"""


def fetch_engine_locales() -> Tuple[EngineLocalesDict, EngineLanguageDict]:
    """Fetch :class:`EngineData` for each engine and persist JSON in file.

    The script checks all engines about a function::

      def _fetch_engine_data(resp, engine_data):
          ...

    and a variable named ``engine_locales_url``.  The HTTP GET response of
    ``engine_locales_url`` is passed to the ``_fetch_engine_data`` function including a
    instance of :py:obj:`searx.engines.EngineData`.

    .. hint::

      This implementation is backward compatible and supports the (depricated)
      ``_fetch_supported_languages`` interface.

      On the long term the depricated implementations in the engines will be
      replaced by ``_fetch_engine_data``."""

    network.set_timeout_for_thread(10.0)
    engine_locales_dict: EngineLocalesDict = {}
    engines_languages: EngineLanguageDict = {}
    names = list(engines)
    names.sort()

    # The headers has been moved here from commit 9b6ffed06: Some engines (at
    # least bing and startpage) return a different result list of supported
    # languages depending on the IP location where the HTTP request comes from.
    # The IP based results (from bing) can be avoided by setting a
    # 'Accept-Language' in the HTTP request.

    headers = {
        'User-Agent': gen_useragent(),
        'Accept-Language': "en-US,en;q=0.5",  # bing needs to set the English language
    }

    for engine_name in names:
        engine = engines[engine_name]

        fetch_locales = getattr(engine, '_fetch_engine_locales', None)
        # deprecated: _fetch_supported_languages
        fetch_languages = getattr(engine, '_fetch_supported_languages', None)

        if fetch_locales is not None:
            resp = network.get(engine.engine_locales_url, headers=headers)  # type: ignore
            engine_data = EngineLocales()
            fetch_locales(resp, engine_data)
            engine_locales_dict[engine_name] = engine_data
            print(
                "%-20s: %3s language(s), %3s region(s)"
                % (engine_name, len(engine_data.languages), len(engine_data.regions))
            )
        elif fetch_languages is not None:
            print(engine_name)
            resp = network.get(engine.supported_languages_url, headers=headers)  # type: ignore
            engines_languages[engine_name] = fetch_languages(resp)
            print(
                "%-20s: %3s languages using deprecated _fetch_supported_languages"
                % (engine_name, len(engines_languages[engine_name]))
            )
            if type(engines_languages[engine_name]) == list:  # pylint: disable=unidiomatic-typecheck
                engines_languages[engine_name] = sorted(engines_languages[engine_name])

    return engine_locales_dict, engines_languages


# Get babel Locale object from lang_code if possible.
def get_locale(lang_code: str) -> Optional[Locale]:
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


def get_unicode_flag(lang_code: str) -> Optional[str]:
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


def get_territory_name(lang_code: str) -> Optional[str]:
    country_name = None
    locale = get_locale(lang_code)
    try:
        if locale is not None:
            country_name = locale.get_territory_name()
    except FileNotFoundError as exc:
        print("ERROR: %s --> %s" % (locale, exc))
    return country_name


def iter_engine_codes(
    engine_data_dict: EngineLocalesDict, engines_languages: EngineLanguageDict
) -> Generator[Tuple[str, List[str]], None, None]:
    """Iterator returning tuples:

    -  first element is the engine name
    -  second element is a list of language code (the one from the engines)

    The function iterates first on the engine from engine_data_dict,
    then it iterates over the engine from engines_languages.
    """
    for engine_name in engine_data_dict:
        engine = engines[engine_name]
        engine_data = engine_data_dict[engine_name]

        # items of type 'engine_data' do have regions & languages, the list
        # of engine_codes should contain both.

        engine_codes = list(engine_data.regions.keys())
        engine_codes.extend(engine_data.languages.keys())
        yield engine_name, engine_codes

    for engine_name, engine_languages in engines_languages.items():
        engine = engines[engine_name]
        language_aliases_values = getattr(engine, 'language_aliases', {}).values()
        engine_codes: List[str] = []
        for lang_code in engine_languages:
            if lang_code in language_aliases_values:
                # pylint: disable=stop-iteration-return
                # we are sure that next(...) won't raise a StopIteration exception
                # because of the "if" statement just above
                lang_code = next(lc for lc, alias in engine.language_aliases.items() if lang_code == alias)
                # pylint: enable=stop-iteration-return
            engine_codes.append(lang_code)
        yield engine_name, engine_codes


class CountryInfo(TypedDict):
    """Country name with a set of engine names.
    Use exclusivly in JoinLanguageResult"""

    country_name: str
    """Name of the country"""

    engine_names: Set[str]
    """Engine names which use the language & country"""


class JoinLanguageResult(TypedDict):
    """Result of join_language_lists"""

    name: Optional[str]
    """Native name of the language"""

    english_name: Optional[str]
    """English name of the language"""

    engine_names: Set
    """Engine names which use this language"""

    countries: Dict[str, CountryInfo]
    """Possible country codes for this language"""


def join_language_lists(
    engine_data_dict: EngineLocalesDict, engines_languages: EngineLanguageDict
) -> Dict[str, JoinLanguageResult]:
    """Join all languages of the engines into one list.  The returned language list
    contains language codes (``zh``) and region codes (``zh-TW``).  The codes can
    be parsed by babel::

      babel.Locale.parse(language_list[n])

    """
    language_list: Dict[str, JoinLanguageResult] = {}
    name_from_babel = set()
    name_from_wikipedia = set()
    name_not_found = set()

    for engine_name, engine_codes in iter_engine_codes(engine_data_dict, engines_languages):
        for lang_code in engine_codes:

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
                    name_from_babel.add(short_code)
                elif short_code in engines_languages['wikipedia'] and isinstance(engines_languages['wikipedia'], dict):
                    # get language's data from wikipedia if not known by babel
                    language_name = engines_languages['wikipedia'][short_code]['name']
                    english_name = engines_languages['wikipedia'][short_code].get('english_name')
                    name_from_wikipedia.add(short_code)
                else:
                    language_name = None
                    english_name = None
                    name_not_found.add(short_code)

                # add language to list
                language_list[short_code] = {
                    'name': language_name,
                    'english_name': english_name,
                    'engine_names': set(),
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
                    'engine_names': set(),
                }

            # count engine for both language_country combination and language alone
            language_list[short_code]['engine_names'].add(engine_name)
            if lang_code != short_code:
                language_list[short_code]['countries'][lang_code]['engine_names'].add(engine_name)

    def set_to_list(engine_name_set: Set) -> str:
        return ', '.join(sorted(list(engine_name_set)))

    print('')
    print('%s name(s) found with Babel: %s\n' % (len(name_from_babel), set_to_list(name_from_babel)))
    print('%s name(s) found with Wikipedia: %s\n' % (len(name_from_wikipedia), set_to_list(name_from_wikipedia)))
    print('%s name(s) not found: %s\n' % (len(name_not_found), set_to_list(name_not_found)))

    return language_list


class LanguageCountryName(TypedDict):
    """filter_language_list returns a dictionnary:
    * the key are the language code
    * the value is described in this type
    """

    name: Optional[str]
    english_name: Optional[str]
    country_name: NotRequired[str]


def filter_language_list(all_languages: Dict[str, JoinLanguageResult]) -> Dict[str, LanguageCountryName]:
    """Filter language list so it only includes the most supported languages and
    countries.
    """
    min_engines_per_lang = 12
    min_engines_per_country = 7
    main_engines = [
        engine_name
        for engine_name, engine in engines.items()
        if 'general' in engine.categories
        and hasattr(engine, 'supported_languages')
        and engine.supported_languages
        and not engine.disabled
    ]

    # filter list to include only languages supported by most engines or all default general engines
    filtered_languages = {
        code: join_result
        for code, join_result in all_languages.items()
        if (
            len(join_result['engine_names']) >= min_engines_per_lang
            or all(main_engine in join_result['engine_names'] for main_engine in main_engines)
        )
    }

    def _new_language_country_name(lang: str, country_name: Optional[str]) -> LanguageCountryName:
        new_dict: LanguageCountryName = {
            'name': all_languages[lang]['name'],
            'english_name': all_languages[lang]['english_name'],
        }
        if country_name:
            new_dict['country_name'] = country_name
        return new_dict

    # for each language get country codes supported by most engines or at least one country code
    filtered_languages_with_countries: Dict[str, LanguageCountryName] = {}
    for lang, lang_data in filtered_languages.items():
        countries = lang_data['countries']
        filtered_countries: Dict[str, LanguageCountryName] = {}

        # get language's country codes with enough supported engines
        for lang_country, country_data in countries.items():
            if len(country_data['engine_names']) >= min_engines_per_country:
                filtered_countries[lang_country] = _new_language_country_name(lang, country_data['country_name'])

        # add language without countries too if there's more than one country to choose from
        if len(filtered_countries) > 1:
            filtered_countries[lang] = _new_language_country_name(lang, None)
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
                filtered_countries[lang_country] = _new_language_country_name(lang, None)
            else:
                filtered_countries[lang] = _new_language_country_name(lang, None)

        filtered_languages_with_countries.update(filtered_countries)

    return filtered_languages_with_countries


def write_engine_data(file_name, engine_data_dict: EngineLocalesDict):
    raw = {
        engine_name: {
            'regions': engine_data.regions,
            'languages': engine_data.languages,
        }
        for engine_name, engine_data in engine_data_dict.items()
    }
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(raw, f, indent=2, sort_keys=True)


def write_engines_languages(file_name, engines_languages: EngineLanguageDict):
    # write json file
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(engines_languages, f, indent=2, sort_keys=True)


class UnicodeEscape(str):
    """Escape unicode string in :py:obj:`pprint.pformat`"""

    def __repr__(self):
        return "'" + "".join([chr(c) for c in self.encode('unicode-escape')]) + "'"


# Write languages.py.
def write_languages_file(language_file, languages: Dict[str, LanguageCountryName]):
    """Generates :origin:`searx/languages.py`."""

    file_headers = (
        "# -*- coding: utf-8 -*-",
        "# list of language codes",
        "# this file is generated automatically by:",
        "#",
        "#   ./manage pyenv.cmd searxng_extra/update/update_languages.py",
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
            name.split(' (')[0],
            get_territory_name(code) or '',
            languages[code].get('english_name') or '',
            UnicodeEscape(flag),
        )

        language_codes.append(item)

    language_codes = tuple(language_codes)

    with open(language_file, 'w', encoding='utf-8') as new_file:
        file_content = "{file_headers} {language_codes},\n)\n".format(
            # fmt: off
            file_headers = '\n'.join(file_headers),
            language_codes = pformat(language_codes, indent=4)[1:-1]
            # fmt: on
        )
        new_file.write(file_content)


if __name__ == "__main__":
    load_engines(settings['engines'])
    _engine_locales_dict, _engines_languages = fetch_engine_locales()
    _all_languages = join_language_lists(_engine_locales_dict, _engines_languages)
    _filtered_languages = filter_language_list(_all_languages)
    write_engine_data(data_dir / 'engine_locales.json', _engine_locales_dict)
    write_engines_languages(data_dir / 'engines_languages.json', _engines_languages)
    write_languages_file(Path(searx_dir) / 'languages.py', _filtered_languages)
