# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Digg (News, Social media)

"""

from urllib.parse import urlencode
from datetime import datetime

from lxml import html
from searx.utils import eval_xpath, extract_text

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
results_per_page = 10

# search-url
search_url = base_url + ('/search' '?{query}' '&size={size}' '&offset={offset}')


def request(query, params):
    offset = (params['pageno'] - 1) * results_per_page + 1
    params['url'] = search_url.format(
        query=urlencode({'q': query}),
        size=results_per_page,
        offset=offset,
    )
    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    results_list = eval_xpath(dom, '//section[contains(@class, "search-results")]')

    for result in results_list:

        titles = eval_xpath(result, '//article//header//h2')
        contents = eval_xpath(result, '//article//p')
        urls = eval_xpath(result, '//header/a/@href')
        published_dates = eval_xpath(result, '//article/div/div/time/@datetime')

        for (title, content, url, published_date) in zip(titles, contents, urls, published_dates):
            results.append(
                {
                    'url': url,
                    'publishedDate': datetime.strptime(published_date, '%Y-%m-%dT%H:%M:%SZ'),
                    'title': extract_text(title),
                    'content': extract_text(content),
                }
            )

    return results
