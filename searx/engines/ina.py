# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 INA (Videos)
"""

from json import loads
from html import unescape
from urllib.parse import urlencode
from lxml import html
from dateutil import parser
from searx.utils import extract_text

# about
about = {
    "website": 'https://www.ina.fr/',
    "wikidata_id": 'Q1665109',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
    "language": 'fr',
}

# engine dependent config
categories = ['videos']
paging = True
page_size = 48

# search-url
base_url = 'https://www.ina.fr'
search_url = base_url + '/layout/set/ajax/recherche/result?autopromote=&hf={ps}&b={start}&type=Video&r=&{query}'

# specific xpath variables
results_xpath = '//div[contains(@class,"search-results--list")]//div[@class="media-body"]'
url_xpath = './/a/@href'
title_xpath = './/h3[@class="h3--title media-heading"]'
thumbnail_xpath = './/img/@src'
publishedDate_xpath = './/span[@class="broadcast"]'
content_xpath = './/p[@class="media-body__summary"]'


# do search-request
def request(query, params):
    params['url'] = search_url.format(ps=page_size, start=params['pageno'] * page_size, query=urlencode({'q': query}))

    return params


# get response from search-request
def response(resp):
    results = []

    # we get html in a JSON container...
    response = loads(resp.text)
    dom = html.fromstring(response)

    # parse results
    for result in dom.xpath(results_xpath):
        videoid = result.xpath(url_xpath)[0]
        url = base_url + videoid
        title = unescape(extract_text(result.xpath(title_xpath)))
        try:
            thumbnail = extract_text(result.xpath(thumbnail_xpath)[0])
        except:
            thumbnail = ''
        if thumbnail and thumbnail[0] == '/':
            thumbnail = base_url + thumbnail
        d = extract_text(result.xpath(publishedDate_xpath)[0])
        d = d.split('/')
        # force ISO date to avoid wrong parsing
        d = "%s-%s-%s" % (d[2], d[1], d[0])
        publishedDate = parser.parse(d)
        content = extract_text(result.xpath(content_xpath))

        # append result
        results.append(
            {
                'url': url,
                'title': title,
                'content': content,
                'template': 'videos.html',
                'publishedDate': publishedDate,
                'thumbnail': thumbnail,
            }
        )

    # return results
    return results
