# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=too-many-branches, invalid-name

"""4get (web, images, videos, music, news)

.. hint::
   Make sure the name of the scraper you want to use is set correctly!
   duckduckgo is ddg, findthatmeme is ftm, souncloud is sc, and youtube
   is yt.
"""

import time
from urllib.parse import urlencode, urlparse, parse_qs
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Engine metadata
about = {
    "website": 'https://4get.ca/',
    "official_api_documentation": 'https://4get.ca/api.txt',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# Engine configuration
paging = True
base_url: list = []
scraper: list = []
search_type: list = []
safesearch = True
time_range_support = True
safesearch_map = {0: 'yes', 1: 'maybe', 2: 'no'}


def request(query, params):
    key = params['engine_data'].get('npt')

    query_params = {
        "s": query,
        "scraper": scraper,
        "country": "any",
        "nsfw": safesearch_map[params['safesearch']],
        "lang": "any",
    }

    if params['time_range']:
        date = (datetime.now() - relativedelta(**{f"{params['time_range']}s": 1})).strftime("%Y-%m-%d")
        query_params["newer"] = date

    params['url'] = f"{base_url}/api/v1/{search_type}?{urlencode(query_params)}"

    if params['pageno'] > 1:
        params['url'] += f"&npt={key}"

    return params


# Format the video duration
def format_duration(duration):
    seconds = int(duration)
    length = time.gmtime(seconds)
    if length.tm_hour:
        return time.strftime("%H:%M:%S", length)
    return time.strftime("%M:%S", length)


# get embedded youtube links
def _get_iframe_src(url):
    parsed_url = urlparse(url)
    if parsed_url.path == '/watch' and parsed_url.query:
        video_id = parse_qs(parsed_url.query).get('v', [])  # type: ignore
        if video_id:
            return 'https://www.youtube-nocookie.com/embed/' + video_id[0]  # type: ignore
    return None


def response(resp):
    results = []
    data = resp.json()

    try:
        results.append(
            {
                'engine_data': data["npt"],
                'key': "npt",
            }
        )
    except KeyError:
        # there are no more results
        return results

    if search_type == 'web':
        for item in data["web"]:

            results.append(
                {
                    "title": item["title"],
                    "url": item["url"],
                    "content": item["description"],
                    "publishedDate": datetime.utcfromtimestamp(item.get("date")) if item.get("date") else None,
                    "img_src": item["thumb"]["url"] or None,
                }
            )

    elif search_type == 'images':
        for item in data["image"]:

            width = item["source"][0]["width"]
            height = item["source"][0]["height"]
            resolution = f'{width} x {height}' if width is not None else ''

            results.append(
                {
                    "title": item["title"],
                    "url": item["source"][0]["url"],
                    "img_src": item["source"][0]["url"],
                    "thumbnail_src": item["source"][-1]["url"],
                    "source": item["url"],
                    "template": "images.html",
                    "resolution": resolution,
                }
            )

    elif search_type == 'videos':
        for item in data["video"]:

            results.append(
                {
                    "url": item["url"],
                    "title": item["title"],
                    "content": item["description"] or "",
                    "author": item["author"]["name"],
                    "publishedDate": datetime.utcfromtimestamp(item["date"]),
                    "length": format_duration(item.get("duration")) if item.get("duration") else None,
                    "thumbnail": item["thumb"]["url"],
                    "iframe_src": _get_iframe_src(item["url"]),
                    "template": "videos.html",
                }
            )

    elif search_type == 'news':
        for item in data["news"]:

            results.append(
                {
                    "title": item["title"],
                    "url": item["url"],
                    "content": item["description"],
                    "author": item["author"],
                    "publishedDate": datetime.utcfromtimestamp(item["date"]),
                    "img_src": item["thumb"]["url"],
                }
            )

    elif search_type == 'music':
        for section in ["song", "playlist"]:
            for item in data[section]:

                results.append(
                    {
                        "title": item["title"],
                        "url": item["url"],
                        "content": item["description"] or "",
                        "author": item["author"]["name"],
                        "publishedDate": datetime.utcfromtimestamp(item["date"]),
                        "length": format_duration(item["duration"]),
                        "img_src": item["thumb"]["url"],
                    }
                )

        for item in data["author"]:

            results.append(
                {
                    "title": item["title"],
                    "url": item["url"],
                    "content": item["description"],
                    "img_src": item["thumb"]["url"],
                    "metadata": f'followers: {item["followers"]}',
                }
            )

    return results
