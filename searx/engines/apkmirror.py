# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""APKMirror
"""

# pylint: disable=invalid-name

from urllib.parse import urlencode
from lxml import html

from searx.utils import (
    eval_xpath_list,
    eval_xpath_getindex,
    extract_text,
)

about = {
    "website": 'https://www.apkmirror.com',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['files', 'apps']
paging = True
time_range_support = False

# search-url
base_url = 'https://www.apkmirror.com'
search_url = base_url + '/?post_type=app_release&searchtype=apk&page={pageno}&{query}'


def request(query, params):
    params['url'] = search_url.format(
        pageno=params['pageno'],
        query=urlencode({'s': query}),
    )
    logger.debug("query_url --> %s", params['url'])
    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    # parse results
    for result in eval_xpath_list(dom, "//div[@id='content']//div[@class='listWidget']/div/div[@class='appRow']"):

        link = eval_xpath_getindex(result, './/h5/a', 0)

        url = base_url + link.attrib.get('href') + '#downloads'
        title = extract_text(link)
        img_src = base_url + eval_xpath_getindex(result, './/img/@src', 0)
        res = {'url': url, 'title': title, 'img_src': img_src}

        results.append(res)

    return results
