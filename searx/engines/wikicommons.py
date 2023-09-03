# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Wikimedia Commons (images)

"""

from urllib.parse import urlencode

# about
about = {
    "website": 'https://commons.wikimedia.org/',
    "wikidata_id": 'Q565',
    "official_api_documentation": 'https://commons.wikimedia.org/w/api.php',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

base_url = "https://commons.wikimedia.org"
search_prefix = (
    '?action=query'
    '&format=json'
    '&generator=search'
    '&gsrnamespace=6'
    '&gsrprop=snippet'
    '&prop=info|imageinfo'
    '&iiprop=url|size|mime'
    '&iiurlheight=180'  # needed for the thumb url
)
paging = True
number_of_results = 10


def request(query, params):
    language = 'en'
    if params['language'] != 'all':
        language = params['language'].split('-')[0]

    args = {
        'uselang': language,
        'gsrlimit': number_of_results,
        'gsroffset': number_of_results * (params["pageno"] - 1),
        'gsrsearch': "filetype:bitmap|drawing " + query,
    }

    params["url"] = f"{base_url}/w/api.php{search_prefix}&{urlencode(args, safe=':|')}"
    return params


def response(resp):
    results = []
    json = resp.json()

    if not json.get("query", {}).get("pages"):
        return results

    for item in json["query"]["pages"].values():
        imageinfo = item["imageinfo"][0]
        title = item["title"].replace("File:", "").rsplit('.', 1)[0]
        result = {
            'url': imageinfo["descriptionurl"],
            'title': title,
            'content': item["snippet"],
            'img_src': imageinfo["url"],
            'img_format': f'{imageinfo["width"]} x {imageinfo["height"]}',
            'thumbnail_src': imageinfo["thumburl"],
            'template': 'images.html',
        }
        results.append(result)

    return results
