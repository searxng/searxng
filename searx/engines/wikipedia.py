# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Wikipedia (Web)
"""

from urllib.parse import quote
from json import loads
from lxml import html
from searx.utils import match_language, searx_useragent
from searx import network
from searx.enginelib.traits import EngineTraits

engine_traits: EngineTraits

# about
about = {
    "website": 'https://www.wikipedia.org/',
    "wikidata_id": 'Q52',
    "official_api_documentation": 'https://en.wikipedia.org/api/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}


send_accept_language_header = True

# search-url
search_url = 'https://{language}.wikipedia.org/api/rest_v1/page/summary/{title}'
supported_languages_url = 'https://meta.wikimedia.org/wiki/List_of_Wikipedias'
language_variants = {"zh": ("zh-cn", "zh-hk", "zh-mo", "zh-my", "zh-sg", "zh-tw")}


# set language in base_url
def url_lang(lang):
    lang_pre = lang.split('-')[0]
    if lang_pre == 'all' or lang_pre not in supported_languages and lang_pre not in language_aliases:
        return 'en'
    return match_language(lang, supported_languages, language_aliases).split('-')[0]


# do search-request
def request(query, params):
    if query.islower():
        query = query.title()

    language = url_lang(params['language'])
    params['url'] = search_url.format(title=quote(query), language=language)

    params['headers']['User-Agent'] = searx_useragent()
    params['raise_for_httperror'] = False
    params['soft_max_redirects'] = 2

    return params


# get response from search-request
def response(resp):
    if resp.status_code == 404:
        return []

    if resp.status_code == 400:
        try:
            api_result = loads(resp.text)
        except:
            pass
        else:
            if (
                api_result['type'] == 'https://mediawiki.org/wiki/HyperSwitch/errors/bad_request'
                and api_result['detail'] == 'title-invalid-characters'
            ):
                return []

    network.raise_for_httperror(resp)

    results = []
    api_result = loads(resp.text)

    # skip disambiguation pages
    if api_result.get('type') != 'standard':
        return []

    title = api_result['title']
    wikipedia_link = api_result['content_urls']['desktop']['page']

    results.append({'url': wikipedia_link, 'title': title})

    results.append(
        {
            'infobox': title,
            'id': wikipedia_link,
            'content': api_result.get('extract', ''),
            'img_src': api_result.get('thumbnail', {}).get('source'),
            'urls': [{'title': 'Wikipedia', 'url': wikipedia_link}],
        }
    )

    return results


# get supported languages from their site
def _fetch_supported_languages(resp):
    supported_languages = {}
    dom = html.fromstring(resp.text)
    tables = dom.xpath('//table[contains(@class,"sortable")]')
    for table in tables:
        # exclude header row
        trs = table.xpath('.//tr')[1:]
        for tr in trs:
            td = tr.xpath('./td')
            code = td[3].xpath('./a')[0].text
            name = td[1].xpath('./a')[0].text
            english_name = td[1].xpath('./a')[0].text
            articles = int(td[4].xpath('./a')[0].text.replace(',', ''))
            # exclude languages with too few articles
            if articles >= 100:
                supported_languages[code] = {"name": name, "english_name": english_name}

    return supported_languages


# Nonstandard language codes
#
# These Wikipedias use language codes that do not conform to the ISO 639
# standard (which is how wiki subdomains are chosen nowadays).

lang_map = {
    'be-tarask': 'bel',
    'ak': 'aka',
    'als': 'gsw',
    'bat-smg': 'sgs',
    'cbk-zam': 'cbk',
    'fiu-vro': 'vro',
    'map-bms': 'map',
    'nrm': 'nrf',
    'roa-rup': 'rup',
    'nds-nl': 'nds',
    #'roa-tara: – invented code used for the Tarantino Wikipedia (again, roa is the standard code for the large family of Romance languages that the Tarantino dialect falls within)
    #'simple: – invented code used for the Simple English Wikipedia (not the official IETF code en-simple)
    'zh-classical': 'zh_Hant',
    'zh-min-nan': 'nan',
    'zh-yue': 'yue',
    'an': 'arg',
}

unknown_langs = [
    'ab',  # Abkhazian
    'alt',  # Southern Altai
    'an',  # Aragonese
    'ang',  # Anglo-Saxon
    'arc',  # Aramaic
    'ary',  # Moroccan Arabic
    'av',  # Avar
    'ba',  # Bashkir
    'be-tarask',
    'bar',  # Bavarian
    'bcl',  # Central Bicolano
    'bh',  # Bhojpuri
    'bi',  # Bislama
    'bjn',  # Banjar
    'blk',  # Pa'O
    'bpy',  # Bishnupriya Manipuri
    'bxr',  # Buryat
    'cbk-zam',  # Zamboanga Chavacano
    'co',  # Corsican
    'cu',  # Old Church Slavonic
    'dty',  # Doteli
    'dv',  # Divehi
    'ext',  # Extremaduran
    'fj',  # Fijian
    'frp',  # Franco-Provençal
    'gan',  # Gan
    'gom',  # Goan Konkani
    'hif',  # Fiji Hindi
    'ilo',  # Ilokano
    'inh',  # Ingush
    'jbo',  # Lojban
    'kaa',  # Karakalpak
    'kbd',  # Kabardian Circassian
    'kg',  # Kongo
    'koi',  # Komi-Permyak
    'krc',  # Karachay-Balkar
    'kv',  # Komi
    'lad',  # Ladino
    'lbe',  # Lak
    'lez',  # Lezgian
    'li',  # Limburgish
    'ltg',  # Latgalian
    'mdf',  # Moksha
    'mnw',  # Mon
    'mwl',  # Mirandese
    'myv',  # Erzya
    'na',  # Nauruan
    'nah',  # Nahuatl
    'nov',  # Novial
    'nrm',  # Norman
    'pag',  # Pangasinan
    'pam',  # Kapampangan
    'pap',  # Papiamentu
    'pdc',  # Pennsylvania German
    'pfl',  # Palatinate German
    'roa-rup',  # Aromanian
    'sco',  # Scots
    'sco',  # Scots (https://sco.wikipedia.org) is not known by babel, Scottish Gaelic (https://gd.wikipedia.org) is known by babel
    'sh',  # Serbo-Croatian
    'simple',  # simple english is not know as a natural language different to english (babel)
    'sm',  # Samoan
    'srn',  # Sranan
    'stq',  # Saterland Frisian
    'szy',  # Sakizaya
    'tcy',  # Tulu
    'tet',  # Tetum
    'tpi',  # Tok Pisin
    'trv',  # Seediq
    'ty',  # Tahitian
    'tyv',  # Tuvan
    'udm',  # Udmurt
    'vep',  # Vepsian
    'vls',  # West Flemish
    'vo',  # Volapük
    'wa',  # Walloon
    'xal',  # Kalmyk
]


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages from Wikipedia"""
    # pylint: disable=import-outside-toplevel

    engine_traits.data_type = 'supported_languages'  # deprecated

    import babel
    from searx.locales import language_tag

    resp = network.get('https://meta.wikimedia.org/wiki/List_of_Wikipedias')
    if not resp.ok:
        print("ERROR: response from Wikipedia is not OK.")

    dom = html.fromstring(resp.text)
    for row in dom.xpath('//table[contains(@class,"sortable")]//tbody/tr'):

        cols = row.xpath('./td')
        if not cols:
            continue

        cols = [c.text_content().strip() for c in cols]
        articles = int(cols[4].replace(',', '').replace('-', '0'))
        users = int(cols[8].replace(',', '').replace('-', '0'))
        depth = cols[11].strip('-')

        if articles < 1000:
            # exclude languages with too few articles
            continue

        # depth: rough indicator of a Wikipedia’s quality, showing how
        #        frequently its articles are updated.
        if depth == '':
            if users < 1000:
                # depth is not calculated --> at least 1000 user should registered
                continue
        elif int(depth) < 20:
            continue

        eng_tag = cols[3]

        if eng_tag in unknown_langs:
            continue

        try:
            sxng_tag = language_tag(babel.Locale.parse(lang_map.get(eng_tag, eng_tag)))
        except babel.UnknownLocaleError:
            print("ERROR: %s -> %s is unknown by babel" % (cols[1], eng_tag))
            continue

        conflict = engine_traits.languages.get(sxng_tag)
        if conflict:
            if conflict != eng_tag:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, eng_tag))
            continue
        engine_traits.languages[sxng_tag] = eng_tag

    engine_traits.languages['zh_Hans'] = 'zh'
