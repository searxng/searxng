# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Bandcamp (Music)

@website     https://bandcamp.com/
@provide-api no
@results     HTML
@parse       url, title, content, publishedDate, iframe_src, thumbnail

"""

from urllib.parse import urlencode, urlparse, parse_qs
from dateutil.parser import parse as dateparse
from lxml import html

from searx.utils import (
    eval_xpath_getindex,
    eval_xpath_list,
    extract_text,
)

# about
about = {
    "website": 'https://bandcamp.com/',
    "wikidata_id": 'Q545966',
    "official_api_documentation": 'https://bandcamp.com/developer',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['music']
paging = True

base_url = "https://bandcamp.com/"
search_string = 'search?{query}&page={page}'
iframe_src = "https://bandcamp.com/EmbeddedPlayer/{type}={result_id}/size=large/bgcol=000/linkcol=fff/artwork=small"


def request(query, params):
    '''pre-request callback

    params<dict>:
      method  : POST/GET
      headers : {}
      data    : {} # if method == POST
      url     : ''
      category: 'search category'
      pageno  : 1 # number of the requested page
    '''

    search_path = search_string.format(query=urlencode({'q': query}), page=params['pageno'])
    params['url'] = base_url + search_path
    return params


def response(resp):
    '''post-response callback

    resp: requests response object
    '''
    results = []
    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, '//li[contains(@class, "searchresult")]'):

        link = eval_xpath_getindex(result, './/div[@class="itemurl"]/a', 0, default=None)
        if link is None:
            continue

        title = result.xpath('.//div[@class="heading"]/a/text()')
        content = result.xpath('.//div[@class="subhead"]/text()')
        new_result = {
            "url": extract_text(link),
            "title": extract_text(title),
            "content": extract_text(content),
        }

        date = eval_xpath_getindex(result, '//div[@class="released"]/text()', 0, default=None)
        if date:
            new_result["publishedDate"] = dateparse(date.replace("released ", ""))

        thumbnail = result.xpath('.//div[@class="art"]/img/@src')
        if thumbnail:
            new_result['img_src'] = thumbnail[0]

        result_id = parse_qs(urlparse(link.get('href')).query)["search_item_id"][0]
        itemtype = extract_text(result.xpath('.//div[@class="itemtype"]')).lower()
        if "album" == itemtype:
            new_result["iframe_src"] = iframe_src.format(type='album', result_id=result_id)
        elif "track" == itemtype:
            new_result["iframe_src"] = iframe_src.format(type='track', result_id=result_id)

        results.append(new_result)
    return results
