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
import babel

from searx import settings, searx_dir
from searx import network
from searx.engines import load_engines
from searx.enginelib.traits import EngineTraitsMap

# Output files.
languages_file = Path(searx_dir) / 'sxng_locales.py'
languages_file_header = """\
# -*- coding: utf-8 -*-
'''List of SearXNG's locale codes.

This file is generated automatically by::

   ./manage pyenv.cmd searxng_extra/update/update_engine_traits.py
'''

sxng_locales = (
"""
languages_file_footer = """,
)
'''
A list of five-digit tuples:

0. SearXNG's internal locale tag (a language or region tag)
1. Name of the language (:py:obj:`babel.core.Locale.get_language_name`)
2. For region tags the name of the region (:py:obj:`babel.core.Locale.get_territory_name`).
   Empty string for language tags.
3. English language name (from :py:obj:`babel.core.Locale.english_name`)
4. Unicode flag (emoji) that fits to SearXNG's internal region tag. Languages
   are represented by a globe (\U0001F310)

.. code:: python

   ('en',    'English', '',              'English', '\U0001f310'),
   ('en-CA', 'English', 'Canada',        'English', '\U0001f1e8\U0001f1e6'),
   ('en-US', 'English', 'United States', 'English', '\U0001f1fa\U0001f1f8'),
   ..
   ('fr',    'Français', '',             'French',  '\U0001f310'),
   ('fr-BE', 'Français', 'Belgique',     'French',  '\U0001f1e7\U0001f1ea'),
   ('fr-CA', 'Français', 'Canada',       'French',  '\U0001f1e8\U0001f1e6'),

:meta hide-value:
'''
"""


lang2emoji = {
    'ha': '\U0001F1F3\U0001F1EA',  # Hausa / Niger
    'bs': '\U0001F1E7\U0001F1E6',  # Bosnian / Bosnia & Herzegovina
    'jp': '\U0001F1EF\U0001F1F5',  # Japanese
    'ua': '\U0001F1FA\U0001F1E6',  # Ukrainian
    'he': '\U0001F1EE\U0001F1F1',  # Hebrew
}


def main():
    load_engines(settings['engines'])
    # traits_map = EngineTraitsMap.from_data()
    traits_map = fetch_traits_map()
    sxng_tag_list = filter_locales(traits_map)
    write_languages_file(sxng_tag_list)


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


def filter_locales(traits_map: EngineTraitsMap):
    """Filter language & region tags by a threshold."""

    min_eng_per_region = 11
    min_eng_per_lang = 13

    _ = {}
    for eng in traits_map.values():
        for reg in eng.regions.keys():
            _[reg] = _.get(reg, 0) + 1

    regions = set(k for k, v in _.items() if v >= min_eng_per_region)
    lang_from_region = set(k.split('-')[0] for k in regions)

    _ = {}
    for eng in traits_map.values():
        for lang in eng.languages.keys():
            # ignore script types like zh_Hant, zh_Hans or sr_Latin, pa_Arab (they
            # already counted by existence of 'zh' or 'sr', 'pa')
            if '_' in lang:
                # print("ignore %s" % lang)
                continue
            _[lang] = _.get(lang, 0) + 1

    languages = set(k for k, v in _.items() if v >= min_eng_per_lang)

    sxng_tag_list = set()
    sxng_tag_list.update(regions)
    sxng_tag_list.update(lang_from_region)
    sxng_tag_list.update(languages)

    return sxng_tag_list


def write_languages_file(sxng_tag_list):

    language_codes = []

    for sxng_tag in sorted(sxng_tag_list):
        sxng_locale: babel.Locale = babel.Locale.parse(sxng_tag, sep='-')

        flag = get_unicode_flag(sxng_locale) or ''

        item = (
            sxng_tag,
            sxng_locale.get_language_name().title(),
            sxng_locale.get_territory_name() or '',
            sxng_locale.english_name.split(' (')[0],
            UnicodeEscape(flag),
        )

        language_codes.append(item)

    language_codes = tuple(language_codes)

    with open(languages_file, 'w', encoding='utf-8') as new_file:
        file_content = "{header} {language_codes}{footer}".format(
            header=languages_file_header,
            language_codes=pformat(language_codes, width=120, indent=4)[1:-1],
            footer=languages_file_footer,
        )
        new_file.write(file_content)
        new_file.close()


class UnicodeEscape(str):
    """Escape unicode string in :py:obj:`pprint.pformat`"""

    def __repr__(self):
        return "'" + "".join([chr(c) for c in self.encode('unicode-escape')]) + "'"


def get_unicode_flag(locale: babel.Locale):
    """Determine a unicode flag (emoji) that fits to the ``locale``"""

    emoji = lang2emoji.get(locale.language)
    if emoji:
        return emoji

    if not locale.territory:
        return '\U0001F310'

    emoji = lang2emoji.get(locale.territory.lower())
    if emoji:
        return emoji

    try:
        c1 = lookup('REGIONAL INDICATOR SYMBOL LETTER ' + locale.territory[0])
        c2 = lookup('REGIONAL INDICATOR SYMBOL LETTER ' + locale.territory[1])
        # print("OK   : %s --> %s%s" % (locale, c1, c2))
    except KeyError as exc:
        print("ERROR: %s --> %s" % (locale, exc))
        return None

    return c1 + c2


if __name__ == "__main__":
    main()