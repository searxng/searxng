# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
 Deviantart (Images)
"""

from urllib.parse import urlencode
from lxml import html

# about
about = {
    "website": 'https://www.deviantart.com/',
    "wikidata_id": 'Q46523',
    "official_api_documentation": 'https://www.deviantart.com/developers/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['images']
paging = True
time_range_support = True

time_range_dict = {
    'day': 'popular-24-hours',
    'week': 'popular-1-week',
    'month': 'popular-1-month',
    'year': 'most-recent',
}

# search-url
base_url = 'https://www.deviantart.com'


def request(query, params):

    # https://www.deviantart.com/search/deviations?page=5&q=foo

    query = {
        'page': params['pageno'],
        'q': query,
    }
    if params['time_range'] in time_range_dict:
        query['order'] = time_range_dict[params['time_range']]

    params['url'] = base_url + '/search/deviations?' + urlencode(query)

    return params


def response(resp):

    results = []

    dom = html.fromstring(resp.text)

    for row in dom.xpath('//div[contains(@data-hook, "content_row")]'):
        for result in row.xpath('./div'):

            a_tag = result.xpath('.//a[@data-hook="deviation_link"]')[0]
            noscript_tag = a_tag.xpath('.//noscript')

            if noscript_tag:
                img_tag = noscript_tag[0].xpath('.//img')
            else:
                img_tag = a_tag.xpath('.//img')
            if not img_tag:
                continue
            img_tag = img_tag[0]

            results.append(
                {
                    'template': 'images.html',
                    'url': a_tag.attrib.get('href'),
                    'img_src': img_tag.attrib.get('src'),
                    'title': img_tag.attrib.get('alt'),
                }
            )

    return results
