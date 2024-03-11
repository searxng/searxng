# SPDX-License-Identifier: AGPL-3.0-or-later
"""Mozhi (alternative frontend for popular translation engines)"""

import random
import re
from urllib.parse import urlencode

about = {
    "website": 'https://codeberg.org/aryak/mozhi',
    "wikidata_id": None,
    "official_api_documentation": 'https://mozhi.aryak.me/api/swagger/index.html',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

engine_type = 'online_dictionary'
categories = ['general']

base_url = "https://mozhi.aryak.me"
mozhi_engine = "google"

re_transliteration_unsupported = "Direction '.*' is not supported"


def request(_query, params):
    request_url = random.choice(base_url) if isinstance(base_url, list) else base_url

    args = {'from': params['from_lang'][1], 'to': params['to_lang'][1], 'text': params['query'], 'engine': mozhi_engine}
    params['url'] = f"{request_url}/api/translate?{urlencode(args)}"
    return params


def response(resp):
    translation = resp.json()

    infobox = ""

    if translation['target_transliteration'] and not re.match(
        re_transliteration_unsupported, translation['target_transliteration']
    ):
        infobox = f"<b>{translation['target_transliteration']}</b>"

    if translation['word_choices']:
        for word in translation['word_choices']:
            infobox += f"<dl><dt>{word['word']}</dt>"

            for example in word['examples_target']:
                infobox += f"<dd>{re.sub(r'<|>', '', example)}</dd>"

            infobox += "</dl>"

    result = {
        'infobox': translation['translated-text'],
        'content': infobox,
    }

    return [result]
