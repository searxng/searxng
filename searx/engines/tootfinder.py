# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tootfinder (social media)
"""

from datetime import datetime
from json import loads
from searx.utils import html_to_text

about = {
    'website': "https://www.tootfinder.ch",
    'official_api_documentation': "https://wiki.tootfinder.ch/index.php?name=the-tootfinder-rest-api",
    'use_official_api': True,
    'require_api_key': False,
    'results': "JSON",
}
categories = ['social media']

base_url = "https://www.tootfinder.ch"


def request(query, params):
    params['url'] = f"{base_url}/rest/api/search/{query}"
    return params


def response(resp):
    results = []

    # the API of tootfinder has an issue that errors on server side are appended to the API response as HTML
    # thus we're only looking for the line that contains the actual json data and ignore everything else
    json_str = ""
    for line in resp.text.split("\n"):
        if line.startswith("[{"):
            json_str = line
            break

    for result in loads(json_str):
        thumbnail = None

        attachments = result.get('media_attachments', [])
        images = [attachment['preview_url'] for attachment in attachments if attachment['type'] == 'image']
        if len(images) > 0:
            thumbnail = images[0]

        title = result.get('card', {}).get('title')
        if not title:
            title = html_to_text(result['content'])[:75]

        results.append(
            {
                'url': result['url'],
                'title': title,
                'content': html_to_text(result['content']),
                'thumbnail': thumbnail,
                'publishedDate': datetime.strptime(result['created_at'], '%Y-%m-%d %H:%M:%S'),
            }
        )

    return results
