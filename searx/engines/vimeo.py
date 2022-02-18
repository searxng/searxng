# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Wikipedia (Web
"""

from urllib.parse import urlencode
from json import loads
from dateutil import parser

# about
about = {
    "website": 'https://vimeo.com/',
    "wikidata_id": 'Q156376',
    "official_api_documentation": 'http://developer.vimeo.com/api',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['videos']
paging = True

# search-url
base_url = 'https://vimeo.com/'
search_url = base_url + '/search/page:{pageno}?{query}'


# do search-request
def request(query, params):
    params['url'] = search_url.format(pageno=params['pageno'], query=urlencode({'q': query}))

    return params


# get response from search-request
def response(resp):
    results = []
    data_start_pos = resp.text.find('{"filtered"')
    data_end_pos = resp.text.find(';\n', data_start_pos + 1)
    data = loads(resp.text[data_start_pos:data_end_pos])

    # parse results
    for result in data['filtered']['data']:
        result = result[result['type']]
        videoid = result['uri'].split('/')[-1]
        url = base_url + videoid
        title = result['name']
        thumbnail = result['pictures']['sizes'][-1]['link']
        publishedDate = parser.parse(result['created_time'])

        # append result
        results.append(
            {
                'url': url,
                'title': title,
                'content': '',
                'template': 'videos.html',
                'publishedDate': publishedDate,
                'iframe_src': "https://player.vimeo.com/video/" + videoid,
                'thumbnail': thumbnail,
            }
        )

    # return results
    return results
