# SPDX-License-Identifier: AGPL-3.0-or-later
"""BPB refers to ``Bundeszentrale für poltische Bildung``, which is a German
governmental institution aiming to reduce misinformation by providing resources
about politics and history.
"""

from datetime import datetime
from urllib.parse import urlencode

about = {
    'website': "https://www.bpb.de",
    'official_api_documentation': None,
    'use_official_api': False,
    'require_api_key': False,
    'results': 'JSON',
    'language': 'de',
}

paging = True
categories = ['general']


base_url = "https://www.bpb.de"


def request(query, params):
    args = {
        'query[term]': query,
        'page': params['pageno'] - 1,
        'sort[direction]': 'descending',
        'payload[nid]': 65350,
    }
    params['url'] = f"{base_url}/bpbapi/filter/search?{urlencode(args)}"
    return params


def response(resp):
    results = []

    json_resp = resp.json()

    for result in json_resp['teaser']:
        img_src = None
        if result['teaser']['image']:
            img_src = base_url + result['teaser']['image']['sources'][-1]['url']

        metadata = result['extension']['overline']
        authors = ', '.join(author['name'] for author in result['extension'].get('authors', []))
        if authors:
            metadata += f" | {authors}"

        publishedDate = None
        if result['extension'].get('publishingDate'):
            publishedDate = datetime.utcfromtimestamp(result['extension']['publishingDate'])

        results.append(
            {
                'url': base_url + result['teaser']['link']['url'],
                'title': result['teaser']['title'],
                'content': result['teaser']['text'],
                'img_src': img_src,
                'publishedDate': publishedDate,
                'metadata': metadata,
            }
        )

    return results
