# SPDX-License-Identifier: AGPL-3.0-or-later
"""LiveSpace (Videos)

.. hint::

   This engine only search for **live streams**!

"""

from urllib.parse import urlencode
from datetime import datetime
from babel import dates

about = {
    "website": 'https://live.space',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['videos']

base_url = 'https://backend.live.space'

# engine dependent config
paging = True
results_per_page = 10


def request(query, params):

    args = {'page': params['pageno'] - 1, 'searchKey': query, 'size': results_per_page}
    params['url'] = f"{base_url}/search/public/stream?{urlencode(args)}"
    params['headers'] = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    return params


def response(resp):

    results = []
    json = resp.json()
    now = datetime.now()

    # for live videos

    for result in json.get('result', []):

        title = result.get("title")
        thumbnailUrl = result.get("thumbnailUrl")
        category = result.get("category/name")
        username = result.get("user", {}).get("userName", "")
        url = f'https://live.space/watch/{username}'

        # stream tags
        # currently the api seems to always return null before the first tag,
        # so strip that unless it's not already there
        tags = ''
        if result.get("tags"):
            tags = [x for x in result.get("tags").split(';') if x and x != 'null']
            tags = ', '.join(tags)

        content = []
        if category:
            content.append(f'category - {category}')

        if tags and len(tags) > 0:
            content.append(f'tags - {tags}')

        # time & duration
        start_time = None
        if result.get("startTimeStamp"):
            start_time = datetime.fromtimestamp(result.get("startTimeStamp") / 1000)

        # for VODs (videos on demand)
        end_time = None
        if result.get("endTimeStamp"):
            end_time = datetime.fromtimestamp(result.get("endTimeStamp") / 1000)

        timestring = ""
        if start_time:
            delta = (now if end_time is None else end_time) - start_time
            timestring = dates.format_timedelta(delta, granularity='second')

        results.append(
            {
                'url': url,
                'title': title,
                'content': "No category or tags." if len(content) == 0 else ' '.join(content),
                'author': username,
                'length': (">= " if end_time is None else "") + timestring,
                'publishedDate': start_time,
                'thumbnail': thumbnailUrl,
                'template': 'videos.html',
            }
        )

    return results
