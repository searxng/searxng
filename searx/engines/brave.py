# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Brave (General, news, videos, images)
"""

from urllib.parse import urlencode
import chompjs
import json

about = {
    "website": 'https://search.brave.com/',
    "wikidata_id": 'Q22906900',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}
base_url = "https://search.brave.com/"
paging = False
categories = ['images', 'videos', 'news']  # images, videos, news


def request(query, params):
    args = {
        'q': query,
        'spellcheck': 1,
    }
    params["url"] = f"{base_url}{categories[0]}?{urlencode(args)}"


def get_video_results(json_data):
    results = []

    for result in json_data:
        results.append(
            {
                'template': 'videos.html',
                'url': result['url'],
                'thumbnail_src': result['thumbnail']['src'],
                'img_src': result['properties']['url'],
                'content': result['description'],
                'title': result['title'],
                'source': result['source'],
                'duration': result['video']['duration'],
            }
        )

    return results


def response(resp):
    results = []

    datastr = ""
    for line in resp.text.split("\n"):
        if "const data = " in line:
            datastr = line.replace("const data = ", "").strip()[:-1]
            break

    json_data = chompjs.parse_js_object(datastr)
    json_results = json_data[1]["data"]["body"]["response"]["results"]

    with open("outfile.json", "w") as f:
        json.dump(json_data, f)

    for result in json_results:
        item = {
            'url': result['url'],
            'title': result['title'],
            'content': result['description'],
        }
        if result['thumbnail'] != "null":
            item['thumbnail'] = result['thumbnail']['src']

        match categories[0]:
            case 'images':
                item['template'] = 'images.html'
                item['img_format'] = result['properties']['format']
                item['source'] = result['source']
                item['img_src'] = result['properties']['url']
            case 'videos':
                item['template'] = 'videos.html'
                item['length'] = result['video']['duration']
        
        results.append(item)

    return results
