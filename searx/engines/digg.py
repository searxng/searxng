# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
 Digg (News, Social media)
"""

from json import loads
from urllib.parse import urlencode
from datetime import datetime

from lxml import html

# about
about = {
    "website": 'https://digg.com',
    "wikidata_id": 'Q270478',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['news', 'social media']
paging = True
base_url = 'https://digg.com'

# search-url
search_url = base_url + (
    '/api/search/'
    '?{query}'
    '&from={position}'
    '&size=20'
    '&format=html'
)

def request(query, params):
    offset = (params['pageno'] - 1) * 20
    params['url'] = search_url.format(
        query = urlencode({'q': query}),
        position = offset,
    )
    return params

def response(resp):
    results = []

    # parse results
    for result in loads(resp.text)['mapped']:

        # strip html tags and superfluous quotation marks from content
        content = html.document_fromstring(
            result['excerpt']
        ).text_content()

        # 'created': {'ISO': '2020-10-16T14:09:55Z', ...}
        published = datetime.strptime(
            result['created']['ISO'], '%Y-%m-%dT%H:%M:%SZ'
        )
        results.append({
            'url': result['url'],
            'title': result['title'],
            'content' : content,
            'template': 'videos.html',
            'publishedDate': published,
            'thumbnail': result['images']['thumbImage'],
        })

    return results
