#!/usr/bin/env python
# lint: pylint
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Fetch website description from websites and from
:origin:`searx/engines/wikidata.py` engine.

Output file: :origin:`searx/data/engine_descriptions.json`.

"""

# pylint: disable=invalid-name, global-statement

import json
from urllib.parse import urlparse
from os.path import join

from lxml.html import fromstring

from langdetect import detect_langs
from langdetect.lang_detect_exception import LangDetectException

from searx.engines import wikidata, set_loggers
from searx.utils import extract_text, match_language
from searx.locales import LOCALE_NAMES
from searx import searx_dir
from searx.utils import gen_useragent
import searx.search
import searx.network

set_loggers(wikidata, 'wikidata')

SPARQL_WIKIPEDIA_ARTICLE = """
SELECT DISTINCT ?item ?name
WHERE {
  hint:Query hint:optimizer "None".
  VALUES ?item { %IDS% }
  ?article schema:about ?item ;
              schema:inLanguage ?lang ;
              schema:name ?name ;
              schema:isPartOf [ wikibase:wikiGroup "wikipedia" ] .
  FILTER(?lang in (%LANGUAGES_SPARQL%)) .
  FILTER (!CONTAINS(?name, ':')) .
}
"""

SPARQL_DESCRIPTION = """
SELECT DISTINCT ?item ?itemDescription
WHERE {
  VALUES ?item { %IDS% }
  ?item schema:description ?itemDescription .
  FILTER (lang(?itemDescription) in (%LANGUAGES_SPARQL%))
}
ORDER BY ?itemLang
"""

NOT_A_DESCRIPTION = [
    'web site',
    'site web',
    'komputa serĉilo',
    'interreta serĉilo',
    'bilaketa motor',
    'web search engine',
    'wikimedia täpsustuslehekülg',
]

SKIP_ENGINE_SOURCE = [
    # fmt: off
    ('gitlab', 'wikidata')
    # descriptions are about wikipedia disambiguation pages
    # fmt: on
]

LANGUAGES = LOCALE_NAMES.keys()
WIKIPEDIA_LANGUAGES = {'language': 'wikipedia_language'}
LANGUAGES_SPARQL = ''
IDS = None

descriptions = {}
wd_to_engine_name = {}


def normalize_description(description):
    for c in [chr(c) for c in range(0, 31)]:
        description = description.replace(c, ' ')
    description = ' '.join(description.strip().split())
    return description


def update_description(engine_name, lang, description, source, replace=True):
    if not isinstance(description, str):
        return
    description = normalize_description(description)
    if description.lower() == engine_name.lower():
        return
    if description.lower() in NOT_A_DESCRIPTION:
        return
    if (engine_name, source) in SKIP_ENGINE_SOURCE:
        return
    if ' ' not in description:
        # skip unique word description (like "website")
        return
    if replace or lang not in descriptions[engine_name]:
        descriptions[engine_name][lang] = [description, source]


def get_wikipedia_summary(lang, pageid):
    params = {'language': lang.replace('_', '-'), 'headers': {}}
    searx.engines.engines['wikipedia'].request(pageid, params)
    try:
        response = searx.network.get(params['url'], headers=params['headers'], timeout=10)
        response.raise_for_status()
        api_result = json.loads(response.text)
        return api_result.get('extract')
    except Exception:  # pylint: disable=broad-except
        return None


def detect_language(text):
    try:
        r = detect_langs(str(text))  # pylint: disable=E1101
    except LangDetectException:
        return None

    if len(r) > 0 and r[0].prob > 0.95:
        return r[0].lang
    return None


def get_website_description(url, lang1, lang2=None):
    headers = {
        'User-Agent': gen_useragent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
        'Sec-GPC': '1',
        'Cache-Control': 'max-age=0',
    }
    if lang1 is not None:
        lang_list = [lang1]
        if lang2 is not None:
            lang_list.append(lang2)
        headers['Accept-Language'] = f'{",".join(lang_list)};q=0.8'
    try:
        response = searx.network.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception:  # pylint: disable=broad-except
        return (None, None)

    try:
        html = fromstring(response.text)
    except ValueError:
        html = fromstring(response.content)

    description = extract_text(html.xpath('/html/head/meta[@name="description"]/@content'))
    if not description:
        description = extract_text(html.xpath('/html/head/meta[@property="og:description"]/@content'))
    if not description:
        description = extract_text(html.xpath('/html/head/title'))
    lang = extract_text(html.xpath('/html/@lang'))
    if lang is None and len(lang1) > 0:
        lang = lang1
    lang = detect_language(description) or lang or 'en'
    lang = lang.split('_')[0]
    lang = lang.split('-')[0]
    return (lang, description)


def initialize():
    global IDS, WIKIPEDIA_LANGUAGES, LANGUAGES_SPARQL
    searx.search.initialize()
    wikipedia_engine = searx.engines.engines['wikipedia']
    WIKIPEDIA_LANGUAGES = {language: wikipedia_engine.url_lang(language.replace('_', '-')) for language in LANGUAGES}
    WIKIPEDIA_LANGUAGES['nb_NO'] = 'no'
    LANGUAGES_SPARQL = ', '.join(f"'{l}'" for l in set(WIKIPEDIA_LANGUAGES.values()))
    for engine_name, engine in searx.engines.engines.items():
        descriptions[engine_name] = {}
        wikidata_id = getattr(engine, "about", {}).get('wikidata_id')
        if wikidata_id is not None:
            wd_to_engine_name.setdefault(wikidata_id, set()).add(engine_name)

    IDS = ' '.join(list(map(lambda wd_id: 'wd:' + wd_id, wd_to_engine_name.keys())))


def fetch_wikidata_descriptions():
    searx.network.set_timeout_for_thread(60)
    result = wikidata.send_wikidata_query(
        SPARQL_DESCRIPTION.replace('%IDS%', IDS).replace('%LANGUAGES_SPARQL%', LANGUAGES_SPARQL)
    )
    if result is not None:
        for binding in result['results']['bindings']:
            wikidata_id = binding['item']['value'].replace('http://www.wikidata.org/entity/', '')
            wikidata_lang = binding['itemDescription']['xml:lang']
            description = binding['itemDescription']['value']
            for engine_name in wd_to_engine_name[wikidata_id]:
                for lang in LANGUAGES:
                    if WIKIPEDIA_LANGUAGES[lang] == wikidata_lang:
                        update_description(engine_name, lang, description, 'wikidata')


def fetch_wikipedia_descriptions():
    result = wikidata.send_wikidata_query(
        SPARQL_WIKIPEDIA_ARTICLE.replace('%IDS%', IDS).replace('%LANGUAGES_SPARQL%', LANGUAGES_SPARQL)
    )
    if result is not None:
        for binding in result['results']['bindings']:
            wikidata_id = binding['item']['value'].replace('http://www.wikidata.org/entity/', '')
            wikidata_lang = binding['name']['xml:lang']
            pageid = binding['name']['value']
            for engine_name in wd_to_engine_name[wikidata_id]:
                for lang in LANGUAGES:
                    if WIKIPEDIA_LANGUAGES[lang] == wikidata_lang:
                        description = get_wikipedia_summary(lang, pageid)
                        update_description(engine_name, lang, description, 'wikipedia')


def normalize_url(url):
    url = url.replace('{language}', 'en')
    url = urlparse(url)._replace(path='/', params='', query='', fragment='').geturl()
    url = url.replace('https://api.', 'https://')
    return url


def fetch_website_description(engine_name, website):
    default_lang, default_description = get_website_description(website, None, None)
    if default_lang is None or default_description is None:
        # the front page can't be fetched: skip this engine
        return

    wikipedia_languages_r = {V: K for K, V in WIKIPEDIA_LANGUAGES.items()}
    languages = ['en', 'es', 'pt', 'ru', 'tr', 'fr']
    languages = languages + [l for l in LANGUAGES if l not in languages]

    previous_matched_lang = None
    previous_count = 0
    for lang in languages:
        if lang not in descriptions[engine_name]:
            fetched_lang, desc = get_website_description(website, lang, WIKIPEDIA_LANGUAGES[lang])
            if fetched_lang is None or desc is None:
                continue
            matched_lang = match_language(fetched_lang, LANGUAGES, fallback=None)
            if matched_lang is None:
                fetched_wikipedia_lang = match_language(fetched_lang, WIKIPEDIA_LANGUAGES.values(), fallback=None)
                matched_lang = wikipedia_languages_r.get(fetched_wikipedia_lang)
            if matched_lang is not None:
                update_description(engine_name, matched_lang, desc, website, replace=False)
            # check if desc changed with the different lang values
            if matched_lang == previous_matched_lang:
                previous_count += 1
                if previous_count == 6:
                    # the website has returned the same description for 6 different languages in Accept-Language header
                    # stop now
                    break
            else:
                previous_matched_lang = matched_lang
                previous_count = 0


def fetch_website_descriptions():
    for engine_name, engine in searx.engines.engines.items():
        website = getattr(engine, "about", {}).get('website')
        if website is None and hasattr(engine, "search_url"):
            website = normalize_url(getattr(engine, "search_url"))
        if website is None and hasattr(engine, "base_url"):
            website = normalize_url(getattr(engine, "base_url"))
        if website is not None:
            fetch_website_description(engine_name, website)


def get_engine_descriptions_filename():
    return join(join(searx_dir, "data"), "engine_descriptions.json")


def get_output():
    """
    From descriptions[engine][language] = [description, source]
    To

    * output[language][engine] = description_and_source
    * description_and_source can be:
       * [description, source]
       * description (if source = "wikipedia")
       * [f"engine:lang", "ref"] (reference to another existing description)
    """
    output = {locale: {} for locale in LOCALE_NAMES}

    seen_descriptions = {}

    for engine_name, lang_descriptions in descriptions.items():
        for language, description in lang_descriptions.items():
            if description[0] in seen_descriptions:
                ref = seen_descriptions[description[0]]
                description = [f'{ref[0]}:{ref[1]}', 'ref']
            else:
                seen_descriptions[description[0]] = (engine_name, language)
                if description[1] == 'wikipedia':
                    description = description[0]
            output.setdefault(language, {}).setdefault(engine_name, description)

    return output


def main():
    initialize()
    print('Fetching wikidata descriptions')
    fetch_wikidata_descriptions()
    print('Fetching wikipedia descriptions')
    fetch_wikipedia_descriptions()
    print('Fetching website descriptions')
    fetch_website_descriptions()

    output = get_output()
    with open(get_engine_descriptions_filename(), 'w', encoding='utf8') as f:
        f.write(json.dumps(output, indent=1, separators=(',', ':'), ensure_ascii=False))


if __name__ == "__main__":
    main()
