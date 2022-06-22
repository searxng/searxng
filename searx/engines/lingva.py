# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Lingva (alternative Google Translate frontend)"""

from json import loads

about = {
    "website": 'https://lingva.ml',
    "wikidata_id": None,
    "official_api_documentation": 'https://github.com/thedaviddelta/lingva-translate#public-apis',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

engine_type = 'online_dictionary'
categories = ['general']

url = "https://lingva.ml"
search_url = "{url}/api/v1/{from_lang}/{to_lang}/{query}"


def request(_query, params):
    params['url'] = search_url.format(
        url=url, from_lang=params['from_lang'][1], to_lang=params['to_lang'][1], query=params['query']
    )
    return params


def response(resp):
    results = []

    result = loads(resp.text)
    info = result["info"]
    from_to_prefix = "%s-%s " % (resp.search_params['from_lang'][1], resp.search_params['to_lang'][1])

    if "typo" in info:
        results.append({"suggestion": from_to_prefix + info["typo"]})

    if 'definitions' in info:  # pylint: disable=too-many-nested-blocks
        for definition in info['definitions']:
            if 'list' in definition:
                for item in definition['list']:
                    if 'synonyms' in item:
                        for synonym in item['synonyms']:
                            results.append({"suggestion": from_to_prefix + synonym})

    infobox = ""

    for translation in info["extraTranslations"]:
        infobox += f"<b>{translation['type']}</b>"

        for word in translation["list"]:
            infobox += f"<dl><dt>{word['word']}</dt>"

            for meaning in word["meanings"]:
                infobox += f"<dd>{meaning}</dd>"

            infobox += "</dl>"

    results.append(
        {
            'infobox': result["translation"],
            'content': infobox,
        }
    )

    return results
