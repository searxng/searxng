#!/usr/bin/env python

import sys
import json
from urllib.parse import quote, urlparse
import detect_language
from lxml.html import fromstring

from searx.engines.wikidata import send_wikidata_query
from searx.utils import extract_text
from searx.locales import LOCALE_NAMES
import searx
import searx.search
import searx.network

SPARQL_WIKIPEDIA_ARTICLE = """
SELECT DISTINCT ?item ?name
WHERE {
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

LANGUAGES = LOCALE_NAMES.keys()
LANGUAGES_SPARQL = ', '.join(set(map(lambda l: repr(l.split('_')[0]), LANGUAGES)))
IDS = None

descriptions = {}
wd_to_engine_name = {}


def normalize_description(description):
    for c in [chr(c) for c in range(0, 31)]:
        description = description.replace(c, ' ')
    description = ' '.join(description.strip().split())
    return description


def update_description(engine_name, lang, description, source, replace=True):
    if replace or lang not in descriptions[engine_name]:
        descriptions[engine_name][lang] = [normalize_description(description), source]


def get_wikipedia_summary(language, pageid):
    search_url = 'https://{language}.wikipedia.org/api/rest_v1/page/summary/{title}'
    url = search_url.format(title=quote(pageid), language=language)
    try:
        response = searx.network.get(url)
        response.raise_for_status()
        api_result = json.loads(response.text)
        return api_result.get('extract')
    except:
        return None


def detect_language(text):
    r = cld3.get_language(str(text))  # pylint: disable=E1101
    if r is not None and r.probability >= 0.98 and r.is_reliable:
        return r.language
    return None


def get_website_description(url, lang1, lang2=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0',
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
    except Exception:
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
    global descriptions, wd_to_engine_name, IDS
    searx.search.initialize()
    for engine_name, engine in searx.engines.engines.items():
        descriptions[engine_name] = {}
        wikidata_id = getattr(engine, "about", {}).get('wikidata_id')
        if wikidata_id is not None:
            wd_to_engine_name.setdefault(wikidata_id, set()).add(engine_name)

    IDS = ' '.join(list(map(lambda wd_id: 'wd:' + wd_id, wd_to_engine_name.keys())))


def fetch_wikidata_descriptions():
    global IDS
    result = send_wikidata_query(SPARQL_DESCRIPTION
                                 .replace('%IDS%', IDS)
                                 .replace('%LANGUAGES_SPARQL%', LANGUAGES_SPARQL))
    if result is not None:
        for binding in result['results']['bindings']:
            wikidata_id = binding['item']['value'].replace('http://www.wikidata.org/entity/', '')
            lang = binding['itemDescription']['xml:lang']
            description = binding['itemDescription']['value']
            if ' ' in description:  # skip unique word description (like "website")
                for engine_name in wd_to_engine_name[wikidata_id]:
                    update_description(engine_name, lang, description, 'wikidata')


def fetch_wikipedia_descriptions():
    global IDS
    result = send_wikidata_query(SPARQL_WIKIPEDIA_ARTICLE
                                 .replace('%IDS%', IDS)
                                 .replace('%LANGUAGES_SPARQL%', LANGUAGES_SPARQL))
    if result is not None:
        for binding in result['results']['bindings']:
            wikidata_id = binding['item']['value'].replace('http://www.wikidata.org/entity/', '')
            lang = binding['name']['xml:lang']
            pageid = binding['name']['value']
            description = get_wikipedia_summary(lang, pageid)
            if description is not None and ' ' in description:
                for engine_name in wd_to_engine_name[wikidata_id]:
                    update_description(engine_name, lang, description, 'wikipedia')


def normalize_url(url):
    url = url.replace('{language}', 'en')
    url = urlparse(url)._replace(path='/', params='', query='', fragment='').geturl()
    url = url.replace('https://api.', 'https://')
    return url


def fetch_website_description(engine_name, website):
    default_lang, default_description = get_website_description(website, None, None)
    if default_lang is None or default_description is None:
        return
    if default_lang not in descriptions[engine_name]:
        descriptions[engine_name][default_lang] = [normalize_description(default_description), website]
    for request_lang in ('en-US', 'es-US', 'fr-FR', 'zh', 'ja', 'ru', 'ar', 'ko'):
        if request_lang.split('-')[0] not in descriptions[engine_name]:
            lang, desc = get_website_description(website, request_lang, request_lang.split('-')[0])
            if desc is not None and desc != default_description:
                update_description(engine_name, lang, desc, website, replace=False)
            else:
                break


def fetch_website_descriptions():
    for engine_name, engine in searx.engines.engines.items():
        website = getattr(engine, "about", {}).get('website')
        if website is None:
            website = normalize_url(getattr(engine, "search_url"))
        if website is None:
            website = normalize_url(getattr(engine, "base_url"))
        if website is not None:
            fetch_website_description(engine_name, website)


def main():
    initialize()
    fetch_wikidata_descriptions()
    fetch_wikipedia_descriptions()
    fetch_website_descriptions()

    sys.stdout.write(json.dumps(descriptions, indent=1, separators=(',', ':'), ensure_ascii=False))


if __name__ == "__main__":
    main()
