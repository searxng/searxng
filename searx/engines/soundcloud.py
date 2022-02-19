# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Soundcloud (Music)
"""

import re
from json import loads
from lxml import html
from dateutil import parser
from urllib.parse import quote_plus, urlencode
from searx.network import get as http_get

# about
about = {
    "website": 'https://soundcloud.com',
    "wikidata_id": 'Q568769',
    "official_api_documentation": 'https://developers.soundcloud.com/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['music']
paging = True

# search-url
# missing attribute: user_id, app_version, app_locale
url = 'https://api-v2.soundcloud.com/'
search_url = (
    url + 'search?{query}'
    '&variant_ids='
    '&facet=model'
    '&limit=20'
    '&offset={offset}'
    '&linked_partitioning=1'
    '&client_id={client_id}'
)  # noqa

cid_re = re.compile(r'client_id:"([^"]*)"', re.I | re.U)
guest_client_id = ''


def get_client_id():
    response = http_get("https://soundcloud.com")

    if response.ok:
        tree = html.fromstring(response.content)
        # script_tags has been moved from /assets/app/ to /assets/ path.  I
        # found client_id in https://a-v2.sndcdn.com/assets/49-a0c01933-3.js
        script_tags = tree.xpath("//script[contains(@src, '/assets/')]")
        app_js_urls = [script_tag.get('src') for script_tag in script_tags if script_tag is not None]

        # extracts valid app_js urls from soundcloud.com content
        for app_js_url in app_js_urls[::-1]:
            # gets app_js and searches for the clientid
            response = http_get(app_js_url)
            if response.ok:
                cids = cid_re.search(response.content.decode())
                if cids is not None and len(cids.groups()):
                    return cids.groups()[0]
    logger.warning("Unable to fetch guest client_id from SoundCloud, check parser!")
    return ""


def init(engine_settings=None):
    global guest_client_id
    # api-key
    guest_client_id = get_client_id()


# do search-request
def request(query, params):
    offset = (params['pageno'] - 1) * 20

    params['url'] = search_url.format(query=urlencode({'q': query}), offset=offset, client_id=guest_client_id)

    return params


# get response from search-request
def response(resp):
    results = []
    search_res = loads(resp.text)

    # parse results
    for result in search_res.get('collection', []):

        if result['kind'] in ('track', 'playlist'):
            uri = quote_plus(result['uri'])
            res = {
                'url': result['permalink_url'],
                'title': result['title'],
                'content': result['description'] or '',
                'publishedDate': parser.parse(result['last_modified']),
                'iframe_src': "https://w.soundcloud.com/player/?url=" + uri,
            }
            img_src = result['artwork_url'] or result['user']['avatar_url']
            if img_src:
                res['img_src'] = img_src
            results.append(res)

    return results
