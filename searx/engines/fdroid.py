# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 F-Droid (a repository of FOSS applications for Android)
"""

from urllib.parse import urlencode
from lxml import html
from searx.utils import extract_text

# about
about = {
    "website": 'https://f-droid.org/',
    "wikidata_id": 'Q1386210',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['files', 'apps']
paging = True

# search-url
base_url = 'https://search.f-droid.org/'
search_url = base_url + '?{query}'


# do search-request
def request(query, params):
    query = urlencode({'q': query, 'page': params['pageno'], 'lang': ''})
    params['url'] = search_url.format(query=query)
    return params


# get response from search-request
def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    for app in dom.xpath('//a[@class="package-header"]'):
        app_url = app.xpath('./@href')[0]
        app_title = extract_text(app.xpath('./div/h4[@class="package-name"]/text()'))
        app_content = (
            extract_text(app.xpath('./div/div/span[@class="package-summary"]')).strip()
            + ' - '
            + extract_text(app.xpath('./div/div/span[@class="package-license"]')).strip()
        )
        app_img_src = app.xpath('./img[@class="package-icon"]/@src')[0]

        results.append({'url': app_url, 'title': app_title, 'content': app_content, 'img_src': app_img_src})

    return results
