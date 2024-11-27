# SPDX-License-Identifier: AGPL-3.0-or-later
"""Wikimedia Commons (images)

"""

import datetime

from urllib.parse import urlencode

from searx.utils import html_to_text, humanize_bytes

# about
about = {
    "website": 'https://commons.wikimedia.org/',
    "wikidata_id": 'Q565',
    "official_api_documentation": 'https://commons.wikimedia.org/w/api.php',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}
categories = ['images']
search_type = 'images'

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

search_types = {
    'images': 'bitmap|drawing',
    'videos': 'video',
    'audio': 'audio',
    'files': 'multimedia|office|archive|3d',
}


def request(query, params):
    language = 'en'
    if params['language'] != 'all':
        language = params['language'].split('-')[0]

    if search_type not in search_types:
        raise ValueError(f"Unsupported search type: {search_type}")

    filetype = search_types[search_type]

    args = {
        'uselang': language,
        'gsrlimit': number_of_results,
        'gsroffset': number_of_results * (params["pageno"] - 1),
        'gsrsearch': f"filetype:{filetype} {query}",
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
            'content': html_to_text(item["snippet"]),
        }

        if search_type == "images":
            result['template'] = 'images.html'
            result['img_src'] = imageinfo["url"]
            result['thumbnail_src'] = imageinfo["thumburl"]
            result['resolution'] = f'{imageinfo["width"]} x {imageinfo["height"]}'
        else:
            result['thumbnail'] = imageinfo["thumburl"]

        if search_type == "videos":
            result['template'] = 'videos.html'
            if imageinfo.get('duration'):
                result['length'] = datetime.timedelta(seconds=int(imageinfo['duration']))
            result['iframe_src'] = imageinfo['url']
        elif search_type == "files":
            result['template'] = 'files.html'
            result['metadata'] = imageinfo['mime']
            result['size'] = humanize_bytes(imageinfo['size'])
        elif search_type == "audio":
            result['iframe_src'] = imageinfo['url']

        results.append(result)

    return results
