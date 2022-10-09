# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
  Google Custom Search API engine

  This engine use Google's paid search API, which requires an API key and do not subject to CAPTCHA.
  The search API has 100 queries/day free tier, and an initial cap of 10k search/day which can be raised by submitting
  a request. The search will use a different algorithm than what Google.com provides.

  Setting up
  ----------

  1. Create a `Google Cloud project <https://console.cloud.google.com/projectcreate>`_
  2. *(optional)* Attach a billing account to the project to enable search quota above the free tier
  3. Enable the `Custom Search API <https://console.cloud.google.com/apis/library/customsearch.googleapis.com>`_
  4. Create an `API key <https://console.cloud.google.com/apis/credentials>`_
  5. *(optional)* Limit the API key to :guilabel:`Custom Search API` and public IP address of the Searx server
  6. Create a `custom search engine <https://programmablesearchengine.google.com>`_.

     * Enable :guilabel:`Image search`
     * Enable :guilabel:`Search the entire web`
     * Other options are not required, including paid element API key

  7. Add the information to :file:`searx.yml`

     .. code-block:: yaml

       engines:
         - name: google custom search
           engine: google_cs
           shortcut: gocs
           api_key: Enter API key from step 4
           cx: Enter search engine ID from step 6

  8. *(optional)* Protect the engine with :doc:`/admin/engines/private-engines` to prevent costly mistakes

"""
from urllib.parse import urlencode

from dateutil.parser import isoparse

from searx.engines.google import get_lang_info

about = {
    "website": 'https://www.google.com',
    "wikidata_id": 'Q9366',
    "official_api_documentation": 'https://developers.google.com/custom-search/v1/overview',
    "use_official_api": True,
    "require_api_key": True,
    "results": 'JSON',
}

# engine dependent config
categories = ['general', 'web', 'images']
paging = True
time_range_support = True
safesearch = True
send_accept_language_header = True

# search-url
base_url = "https://customsearch.googleapis.com/customsearch/v1?{query}"
api_key = None
cx = None
number_of_results = 10  # 1 - 10

MAX_SEARCH_RESULT = 100

time_range_map = {
    'day': 'd[1]',
    'week': 'w[1]',
    'month': 'm[1]',
    'year': 'y[1]',
}

# https://developers.google.com/custom-search/docs/json_api_reference#international-values
supported_languages = {
    "af": {"Name": "Afrikaans"},
    "sq": {"Name": "Albanian"},
    "sm": {"Name": "Amharic"},
    "ar": {"Name": "Arabic"},
    "az": {"Name": "Azerbaijani"},
    "eu": {"Name": "Basque"},
    "be": {"Name": "Belarusian"},
    "bn": {"Name": "Bengali"},
    "bh": {"Name": "Bihari"},
    "bs": {"Name": "Bosnian"},
    "bg": {"Name": "Bulgarian"},
    "ca": {"Name": "Catalan"},
    "zh-CN": {"Name": "Chinese (Simplified)"},
    "zh-TW": {"Name": "Chinese (Traditional)"},
    "hr": {"Name": "Croatian"},
    "cs": {"Name": "Czech"},
    "da": {"Name": "Danish"},
    "nl": {"Name": "Dutch"},
    "en": {"Name": "English"},
    "eo": {"Name": "Esperanto"},
    "et": {"Name": "Estonian"},
    "fo": {"Name": "Faroese"},
    "fi": {"Name": "Finnish"},
    "fr": {"Name": "French"},
    "fy": {"Name": "Frisian"},
    "gl": {"Name": "Galician"},
    "ka": {"Name": "Georgian"},
    "de": {"Name": "German"},
    "el": {"Name": "Greek"},
    "gu": {"Name": "Gujarati"},
    "iw": {"Name": "Hebrew"},
    "hi": {"Name": "Hindi"},
    "hu": {"Name": "Hungarian"},
    "is": {"Name": "Icelandic"},
    "id": {"Name": "Indonesian"},
    "ia": {"Name": "Interlingua"},
    "ga": {"Name": "Irish"},
    "it": {"Name": "Italian"},
    "ja": {"Name": "Japanese"},
    "jw": {"Name": "Javanese"},
    "kn": {"Name": "Kannada"},
    "ko": {"Name": "Korean"},
    "la": {"Name": "Latin"},
    "lv": {"Name": "Latvian"},
    "lt": {"Name": "Lithuanian"},
    "mk": {"Name": "Macedonian"},
    "ms": {"Name": "Malay"},
    "ml": {"Name": "Malayam"},
    "mt": {"Name": "Maltese"},
    "mr": {"Name": "Marathi"},
    "ne": {"Name": "Nepali"},
    "no": {"Name": "Norwegian"},
    "nn": {"Name": "Norwegian (Nynorsk)"},
    "oc": {"Name": "Occitan"},
    "fa": {"Name": "Persian"},
    "pl": {"Name": "Polish"},
    "pt-BR": {"Name": "Portuguese (Brazil)"},
    "pt-PT": {"Name": "Portuguese (Portugal)"},
    "pa": {"Name": "Punjabi"},
    "ro": {"Name": "Romanian"},
    "ru": {"Name": "Russian"},
    "gd": {"Name": "Scots Gaelic"},
    "sr": {"Name": "Serbian"},
    "si": {"Name": "Sinhalese"},
    "sk": {"Name": "Slovak"},
    "sl": {"Name": "Slovenian"},
    "es": {"Name": "Spanish"},
    "su": {"Name": "Sudanese"},
    "sw": {"Name": "Swahili"},
    "sv": {"Name": "Swedish"},
    "tl": {"Name": "Tagalog"},
    "ta": {"Name": "Tamil"},
    "te": {"Name": "Telugu"},
    "th": {"Name": "Thai"},
    "ti": {"Name": "Tigrinya"},
    "tr": {"Name": "Turkish"},
    "uk": {"Name": "Ukrainian"},
    "ur": {"Name": "Urdu"},
    "uz": {"Name": "Uzbek"},
    "vi": {"Name": "Vietnamese"},
    "cy": {"Name": "Welsh"},
    "xh": {"Name": "Xhosa"},
    "zu": {"Name": "Zulu"},
}


def request(query, params):
    start = (params['pageno'] * number_of_results) + 1

    if start > MAX_SEARCH_RESULT:
        return params

    query = {
        'cx': cx,
        'q': query,
        'safe': 'active' if params['safesearch'] > 0 else 'off',
        'num': number_of_results,
        'start': start,
    }

    if params['category'] == 'images':
        query['searchType'] = 'image'

    if params.get('time_range', None) in time_range_map:
        query['dateRestrict'] = time_range_map[params['time_range']]

    lang_info = get_lang_info(params, supported_languages, {}, True)
    query['gl'] = lang_info['country'].lower()
    query['hl'] = lang_info['params']['hl']
    if 'lr' in lang_info['params']:
        query['lr'] = lang_info['params']['lr']

    params['url'] = base_url.format(query=urlencode(query))
    params['headers']['X-Goog-Api-Key'] = api_key
    return params


def response(resp):
    result = resp.json()
    metadata = [
        {'number_of_results': min(MAX_SEARCH_RESULT, int(result['searchInformation']['totalResults'], 10))},
    ]
    search_type = result['queries']['request'][0].get('searchType', '')

    if 'spelling' in result:
        metadata.append({'correction': result['spelling']['correctedQuery']})

    return metadata + [_convert_result(search, search_type) for search in result.get('items', [])]


def _convert_result(result, search_type=''):
    """Convert `result JSON <https://developers.google.com/custom-search/v1/reference/rest/v1/Search#Result>`_
    to Searx result"""
    out = {
        "url": result['link'],
        "title": result['title'],
        "content": result.get('snippet', ''),
    }

    try:
        dt = result['pagemap']['metatags'][0]['date']
        parsed_dt = isoparse(dt)
        out['publishedDate'] = parsed_dt
    except (KeyError, IndexError):
        pass

    try:
        out['author'] = result['pagemap']['metatags'][0]['author']
    except (KeyError, IndexError):
        pass

    try:
        out['img_src'] = result['pagemap']['cse_thumbnail'][0]['src']
    except (KeyError, IndexError):
        pass

    if search_type == 'image' and 'image' in result:
        out['template'] = 'images.html'
        out['img_src'] = result['link']
        out['thumbnail_src'] = result['image']['thumbnailLink']
        out['img_format'] = f"{result['image']['width']} x {result['image']['height']} {result['fileFormat']}"
        out['url'] = result['image']['contextLink']

    return out
