# SPDX-License-Identifier: AGPL-3.0-or-later
"""MyMemory Translated

"""

# about
about = {
    "website": 'https://mymemory.translated.net/',
    "wikidata_id": None,
    "official_api_documentation": 'https://mymemory.translated.net/doc/spec.php',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

engine_type = 'online_dictionary'
categories = ['general', 'translate']
url = 'https://api.mymemory.translated.net/get?q={query}&langpair={from_lang}|{to_lang}{key}'
web_url = 'https://mymemory.translated.net/en/{from_lang}/{to_lang}/{query}'
weight = 100
https_support = True

api_key = ''


def request(query, params):  # pylint: disable=unused-argument
    if api_key:
        key_form = '&key=' + api_key
    else:
        key_form = ''
    params['url'] = url.format(
        from_lang=params['from_lang'][1], to_lang=params['to_lang'][1], query=params['query'], key=key_form
    )
    return params


def response(resp):
    json_resp = resp.json()
    text = json_resp['responseData']['translatedText']

    alternatives = [match['translation'] for match in json_resp['matches'] if match['translation'] != text]
    translations = [{'text': translation} for translation in [text] + alternatives]

    result = {
        'answer': translations[0]['text'],
        'answer_type': 'translations',
        'translations': translations,
    }

    return [result]
