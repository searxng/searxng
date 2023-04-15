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

from searx.engines import wikidata, set_loggers
from searx.utils import extract_text, searx_useragent
from searx.locales import LOCALE_NAMES, locales_initialize, match_locale
from searx import searx_dir
from searx.utils import gen_useragent, detect_language
import searx.search
import searx.network

set_loggers(wikidata, 'wikidata')
locales_initialize()

# you can run the query in https://query.wikidata.org
# replace %IDS% by Wikidata entities separated by spaces with the prefix wd:
# for example wd:Q182496 wd:Q1540899
# replace %LANGUAGES_SPARQL% by languages
SPARQL_WIKIPEDIA_ARTICLE = """
SELECT DISTINCT ?item ?name ?article ?lang
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
ORDER BY ?item ?lang
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

WIKIPEDIA_LANGUAGES = {}
LANGUAGES_SPARQL = ''
IDS = None
WIKIPEDIA_LANGUAGE_VARIANTS = {'zh_Hant': 'zh-tw'}


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


def get_wikipedia_summary(wikipedia_url, searxng_locale):
    # get the REST API URL from the HTML URL

    # Headers
    headers = {'User-Agent': searx_useragent()}

    if searxng_locale in WIKIPEDIA_LANGUAGE_VARIANTS:
        headers['Accept-Language'] = WIKIPEDIA_LANGUAGE_VARIANTS.get(searxng_locale)

    # URL path : from HTML URL to REST API URL
    parsed_url = urlparse(wikipedia_url)
    # remove the /wiki/ prefix
    article_name = parsed_url.path.split('/wiki/')[1]
    # article_name is already encoded but not the / which is required for the REST API call
    encoded_article_name = article_name.replace('/', '%2F')
    path = '/api/rest_v1/page/summary/' + encoded_article_name
    wikipedia_rest_url = parsed_url._replace(path=path).geturl()
    try:
        response = searx.network.get(wikipedia_rest_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:  # pylint: disable=broad-except
        print("     ", wikipedia_url, e)
        return None
    api_result = json.loads(response.text)
    return api_result.get('extract')


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
    global IDS, LANGUAGES_SPARQL
    searx.search.initialize()
    wikipedia_engine = searx.engines.engines['wikipedia']

    locale2lang = {'nl-BE': 'nl'}
    for sxng_ui_lang in LOCALE_NAMES:

        sxng_ui_alias = locale2lang.get(sxng_ui_lang, sxng_ui_lang)
        wiki_lang = None

        if sxng_ui_alias in wikipedia_engine.traits.custom['WIKIPEDIA_LANGUAGES']:
            wiki_lang = sxng_ui_alias
        if not wiki_lang:
            wiki_lang = wikipedia_engine.traits.get_language(sxng_ui_alias)
        if not wiki_lang:
            print(f"WIKIPEDIA_LANGUAGES missing {sxng_ui_lang}")
            continue
        WIKIPEDIA_LANGUAGES[sxng_ui_lang] = wiki_lang

    LANGUAGES_SPARQL = ', '.join(f"'{l}'" for l in set(WIKIPEDIA_LANGUAGES.values()))
    for engine_name, engine in searx.engines.engines.items():
        descriptions[engine_name] = {}
        wikidata_id = getattr(engine, "about", {}).get('wikidata_id')
        if wikidata_id is not None:
            wd_to_engine_name.setdefault(wikidata_id, set()).add(engine_name)

    IDS = ' '.join(list(map(lambda wd_id: 'wd:' + wd_id, wd_to_engine_name.keys())))


def fetch_wikidata_descriptions():
    print('Fetching wikidata descriptions')
    searx.network.set_timeout_for_thread(60)
    result = wikidata.send_wikidata_query(
        SPARQL_DESCRIPTION.replace('%IDS%', IDS).replace('%LANGUAGES_SPARQL%', LANGUAGES_SPARQL)
    )
    if result is not None:
        for binding in result['results']['bindings']:
            wikidata_id = binding['item']['value'].replace('http://www.wikidata.org/entity/', '')
            wikidata_lang = binding['itemDescription']['xml:lang']
            desc = binding['itemDescription']['value']
            for engine_name in wd_to_engine_name[wikidata_id]:
                for searxng_locale in LOCALE_NAMES:
                    if WIKIPEDIA_LANGUAGES[searxng_locale] != wikidata_lang:
                        continue
                    print(
                        f"    engine: {engine_name:20} / wikidata_lang: {wikidata_lang:5}",
                        f"/ len(wikidata_desc): {len(desc)}",
                    )
                    update_description(engine_name, searxng_locale, desc, 'wikidata')


def fetch_wikipedia_descriptions():
    print('Fetching wikipedia descriptions')
    result = wikidata.send_wikidata_query(
        SPARQL_WIKIPEDIA_ARTICLE.replace('%IDS%', IDS).replace('%LANGUAGES_SPARQL%', LANGUAGES_SPARQL)
    )
    if result is not None:
        for binding in result['results']['bindings']:
            wikidata_id = binding['item']['value'].replace('http://www.wikidata.org/entity/', '')
            wikidata_lang = binding['name']['xml:lang']
            wikipedia_url = binding['article']['value']  # for example the URL https://de.wikipedia.org/wiki/PubMed
            for engine_name in wd_to_engine_name[wikidata_id]:
                for searxng_locale in LOCALE_NAMES:
                    if WIKIPEDIA_LANGUAGES[searxng_locale] != wikidata_lang:
                        continue
                    desc = get_wikipedia_summary(wikipedia_url, searxng_locale)
                    if not desc:
                        continue
                    print(
                        f"    engine: {engine_name:20} / wikidata_lang: {wikidata_lang:5}",
                        f"/ len(wikipedia_desc): {len(desc)}",
                    )
                    update_description(engine_name, searxng_locale, desc, 'wikipedia')


def normalize_url(url):
    url = url.replace('{language}', 'en')
    url = urlparse(url)._replace(path='/', params='', query='', fragment='').geturl()
    url = url.replace('https://api.', 'https://')
    return url


def fetch_website_description(engine_name, website):
    print(f"- fetch website descr: {engine_name} / {website}")
    default_lang, default_description = get_website_description(website, None, None)

    if default_lang is None or default_description is None:
        # the front page can't be fetched: skip this engine
        return

    # to specify an order in where the most common languages are in front of the
    # language list ..
    languages = ['en', 'es', 'pt', 'ru', 'tr', 'fr']
    languages = languages + [l for l in LOCALE_NAMES if l not in languages]

    previous_matched_lang = None
    previous_count = 0

    for lang in languages:

        if lang in descriptions[engine_name]:
            continue

        fetched_lang, desc = get_website_description(website, lang, WIKIPEDIA_LANGUAGES[lang])
        if fetched_lang is None or desc is None:
            continue

        # check if desc changed with the different lang values

        if fetched_lang == previous_matched_lang:
            previous_count += 1
            if previous_count == 6:
                # the website has returned the same description for 6 different languages in Accept-Language header
                # stop now
                break
        else:
            previous_matched_lang = fetched_lang
            previous_count = 0

        # Don't trust in the value of fetched_lang, some websites return
        # for some inappropriate values, by example bing-images::
        #
        #   requested lang: zh-Hans-CN / fetched lang: ceb / desc: 查看根据您的兴趣量身定制的提要
        #
        # The lang ceb is "Cebuano" but the description is given in zh-Hans-CN

        print(
            f"    engine: {engine_name:20} / requested lang:{lang:7}"
            f" / fetched lang: {fetched_lang:7} / len(desc): {len(desc)}"
        )

        matched_lang = match_locale(fetched_lang, LOCALE_NAMES.keys(), fallback=lang)
        update_description(engine_name, matched_lang, desc, website, replace=False)


def fetch_website_descriptions():
    print('Fetching website descriptions')
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
    fetch_wikidata_descriptions()
    fetch_wikipedia_descriptions()
    fetch_website_descriptions()

    output = get_output()
    with open(get_engine_descriptions_filename(), 'w', encoding='utf8') as f:
        f.write(json.dumps(output, indent=1, separators=(',', ':'), ensure_ascii=False))


if __name__ == "__main__":
    main()
