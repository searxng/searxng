# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Wallhaven_ is a site created by and for people who like wallpapers.

.. _Wallhaven: https://wallhaven.cc/about#Copyright
"""

from datetime import datetime
from urllib.parse import urlencode

about = {
    'website': 'https://wallhaven.cc/',
    'official_api_documentation': 'https://wallhaven.cc/help/api',
    'use_official_api': True,
    'require_api_key': False,
    'results': 'JSON',
}
categories = ['images']
paging = True

base_url = "https://wallhaven.cc"

api_key = ''
"""If you own an API key you can add it here, further read `Rate Limiting and
Errors`_.

.. _Rate Limiting and Errors: https://wallhaven.cc/help/api#limits

"""

# Possible categories: sfw, sketchy, nsfw
safesearch_map = {0: '111', 1: '110', 2: '100'}
"""Turn purities on(1) or off(0) NSFW requires a valid API key.

.. code:: text

  100/110/111 <-- Bits stands for: SFW, Sketchy and NSFW

`What are SFW, Sketchy and NSFW all about?`_:

- SFW = "Safe for work" wallpapers.  *Grandma approves.*
- Sketchy = Not quite SFW not quite NSFW.  *Grandma might be uncomfortable.*
- NSFW = "Not safe for work". *Grandma isn't sure who you are anymore.*

.. _What are SFW, Sketchy and NSFW all about?:
   https://wallhaven.cc/faq#What-are-SFW-Sketchy-and-NSFW-all-about

"""


def request(query, params):
    args = {
        'q': query,
        'page': params['pageno'],
        'purity': safesearch_map[params['safesearch']],
    }

    if api_key:
        params['api_key'] = api_key

    params['url'] = f"{base_url}/api/v1/search?{urlencode(args)}"
    return params


def response(resp):
    results = []

    json = resp.json()

    for result in json['data']:
        results.append(
            {
                'template': 'images.html',
                'title': '',
                'content': f"{result['category']} / {result['purity']}",
                'url': result['url'],
                'img_src': result['path'],
                'thumbnail_src': result['thumbs']['small'],
                'img_format': result['resolution'],
                'publishedDate': datetime.strptime(result['created_at'], '%Y-%m-%d %H:%M:%S'),
            }
        )

    return results
