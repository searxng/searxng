#!/usr/bin/env python

# This script generates languages.py from intersecting each engine's supported languages.
#
# Output files: searx/data/engines_languages.json and searx/languages.py

import json
from pathlib import Path
from pprint import pformat
from babel import Locale, UnknownLocaleError
from babel.languages import get_global

from searx import settings, searx_dir
from searx.engines import load_engines, engines
from searx.network import set_timeout_for_thread

# Output files.
engines_languages_file = Path(searx_dir) / 'data' / 'engines_languages.json'
languages_file = Path(searx_dir) / 'languages.py'


# Fetchs supported languages for each engine and writes json file with those.
def fetch_supported_languages():
    set_timeout_for_thread(10.0)

    engines_languages = dict()
    names = list(engines)
    names.sort()

    for engine_name in names:
        if hasattr(engines[engine_name], 'fetch_supported_languages'):
            engines_languages[engine_name] = engines[engine_name].fetch_supported_languages()
            print("fetched %s languages from engine %s" % (
                len(engines_languages[engine_name]), engine_name))
            if type(engines_languages[engine_name]) == list:
                engines_languages[engine_name] = sorted(engines_languages[engine_name])

    # write json file
    with open(engines_languages_file, 'w', encoding='utf-8') as f:
        json.dump(engines_languages, f, indent=2, sort_keys=True)

    return engines_languages


# Get babel Locale object from lang_code if possible.
def get_locale(lang_code):
    try:
        locale = Locale.parse(lang_code, sep='-')
        return locale
    except (UnknownLocaleError, ValueError):
        return None


# Join all language lists.
def join_language_lists(engines_languages):
    language_list = dict()
    for engine_name in engines_languages:
        for lang_code in engines_languages[engine_name]:

            # apply custom fixes if necessary
            if lang_code in getattr(engines[engine_name], 'language_aliases', {}).values():
                lang_code = next(lc for lc, alias in engines[engine_name].language_aliases.items()
                                 if lang_code == alias)

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
                elif short_code in engines_languages['wikipedia']:
                    # get language's data from wikipedia if not known by babel
                    language_name = engines_languages['wikipedia'][short_code]['name']
                    english_name = engines_languages['wikipedia'][short_code]['english_name']
                else:
                    language_name = None
                    english_name = None

                # add language to list
                language_list[short_code] = {'name': language_name,
                                             'english_name': english_name,
                                             'counter': set(),
                                             'countries': dict()}

            # add language with country if not in list
            if lang_code != short_code and lang_code not in language_list[short_code]['countries']:
                country_name = ''
                if locale:
                    # get country name from babel's Locale object
                    country_name = locale.get_territory_name()

                language_list[short_code]['countries'][lang_code] = {'country_name': country_name,
                                                                     'counter': set()}

            # count engine for both language_country combination and language alone
            language_list[short_code]['counter'].add(engine_name)
            if lang_code != short_code:
                language_list[short_code]['countries'][lang_code]['counter'].add(engine_name)

    return language_list


# Filter language list so it only includes the most supported languages and countries
def filter_language_list(all_languages):
    min_engines_per_lang = 15
    min_engines_per_country = 10
    main_engines = [engine_name for engine_name in engines.keys()
                    if 'general' in engines[engine_name].categories and
                       engines[engine_name].supported_languages and
                       not engines[engine_name].disabled]

    # filter list to include only languages supported by most engines or all default general engines
    filtered_languages = {code: lang for code, lang
                          in all_languages.items()
                          if (len(lang['counter']) >= min_engines_per_lang or
                              all(main_engine in lang['counter']
                                  for main_engine in main_engines))}

    def _copy_lang_data(lang, country_name=None):
        new_dict = dict()
        new_dict['name'] = all_languages[lang]['name']
        new_dict['english_name'] = all_languages[lang]['english_name']
        if country_name:
            new_dict['country_name'] = country_name
        return new_dict

    # for each language get country codes supported by most engines or at least one country code
    filtered_languages_with_countries = dict()
    for lang, lang_data in filtered_languages.items():
        countries = lang_data['countries']
        filtered_countries = dict()

        # get language's country codes with enough supported engines
        for lang_country, country_data in countries.items():
            if len(country_data['counter']) >= min_engines_per_country:
                filtered_countries[lang_country] = _copy_lang_data(lang, country_data['country_name'])

        # add language without countries too if there's more than one country to choose from
        if len(filtered_countries) > 1:
            filtered_countries[lang] = _copy_lang_data(lang)
        elif len(filtered_countries) == 1:
            # if there's only one country per language, it's not necessary to show country name
            lang_country = next(iter(filtered_countries))
            filtered_countries[lang_country]['country_name'] = None

        # if no country has enough engines try to get most likely country code from babel
        if not filtered_countries:
            lang_country = None
            subtags = get_global('likely_subtags').get(lang)
            if subtags:
                country_code = subtags.split('_')[-1]
                if len(country_code) == 2:
                    lang_country = "{lang}-{country}".format(lang=lang, country=country_code)

            if lang_country:
                filtered_countries[lang_country] = _copy_lang_data(lang)
            else:
                filtered_countries[lang] = _copy_lang_data(lang)

        filtered_languages_with_countries.update(filtered_countries)

    return filtered_languages_with_countries


# Write languages.py.
def write_languages_file(languages):
    file_headers = (
        "# -*- coding: utf-8 -*-",
        "# list of language codes",
        "# this file is generated automatically by utils/fetch_languages.py",
        "language_codes ="
    )

    language_codes = tuple([
        (
            code,
            languages[code]['name'].split(' (')[0],
            languages[code].get('country_name') or '',
            languages[code].get('english_name') or ''
        ) for code in sorted(languages)
    ])

    with open(languages_file, 'w') as new_file:
        file_content = "{file_headers} \\\n{language_codes}".format(
            file_headers='\n'.join(file_headers),
            language_codes=pformat(language_codes, indent=4)
        )
        new_file.write(file_content)
        new_file.close()


if __name__ == "__main__":
    load_engines(settings['engines'])
    engines_languages = fetch_supported_languages()
    all_languages = join_language_lists(engines_languages)
    filtered_languages = filter_language_list(all_languages)
    write_languages_file(filtered_languages)
