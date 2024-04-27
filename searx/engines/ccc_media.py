# SPDX-License-Identifier: AGPL-3.0-or-later
"""media.ccc.de"""

import datetime
from urllib.parse import urlencode

from dateutil import parser

about = {
    'website': 'https://media.ccc.de',
    'official_api_documentation': 'https://github.com/voc/voctoweb',
    'use_official_api': True,
    'require_api_key': False,
    'results': 'JSON',
}
categories = ['videos']
paging = True

api_url = "https://api.media.ccc.de"


def request(query, params):
    args = {'q': query, 'page': params['pageno']}
    params['url'] = f"{api_url}/public/events/search?{urlencode(args)}"

    return params


def response(resp):
    results = []

    for item in resp.json()['events']:
        publishedDate = None
        if item.get('date'):
            publishedDate = parser.parse(item['date'])

        iframe_src = None
        for rec in item['recordings']:
            if rec['mime_type'].startswith('video'):
                if not iframe_src:
                    iframe_src = rec['recording_url']
                elif rec['mime_type'] == 'video/mp4':
                    # prefer mp4 (minimal data rates)
                    iframe_src = rec['recording_url']

        results.append(
            {
                'template': 'videos.html',
                'url': item['frontend_link'],
                'title': item['title'],
                'content': item['description'],
                'thumbnail': item['thumb_url'],
                'publishedDate': publishedDate,
                'length': datetime.timedelta(seconds=item['length']),
                'iframe_src': iframe_src,
            }
        )

    return results
