# SPDX-License-Identifier: AGPL-3.0-or-later
"""FindThatMeme (Images)"""

from json import dumps
from datetime import datetime
from searx.utils import humanize_bytes

about = {
    "website": 'https://findthatmeme.com',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

base_url = "https://findthatmeme.com/api/v1/search"
categories = ['images']
paging = True


def request(query, params):

    start_index = (params["pageno"] - 1) * 50
    data = {"search": query, "offset": start_index}
    params["url"] = base_url
    params["method"] = 'POST'
    params['headers']['content-type'] = "application/json"
    params['data'] = dumps(data)

    return params


def response(resp):
    search_res = resp.json()
    results = []

    for item in search_res:
        img = 'https://s3.thehackerblog.com/findthatmeme/' + item['image_path']
        thumb = 'https://s3.thehackerblog.com/findthatmeme/thumb/' + item.get('thumbnail', '')
        date = datetime.strptime(item["updated_at"].split("T")[0], "%Y-%m-%d")
        formatted_date = datetime.fromtimestamp(date.timestamp())

        results.append(
            {
                'url': item['source_page_url'],
                'title': item['source_site'],
                'img_src': img if item['type'] == 'IMAGE' else thumb,
                'filesize': humanize_bytes(item['meme_file_size']),
                'publishedDate': formatted_date,
                'template': 'images.html',
            }
        )

    return results
