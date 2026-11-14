# SPDX-License-Identifier: AGPL-3.0-or-later
"""Seznam"""

from urllib.parse import urlencode
from searx.exceptions import SearxEngineAccessDeniedException
from searx.utils import (
    extract_text,
    eval_xpath_list,
    eval_xpath_getindex,
)

# about
about = {
    "website": "https://www.seznam.cz/",
    "wikidata_id": "Q3490485",
    "official_api_documentation": "https://api.sklik.cz/",
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}
language = "cz"

categories = ['general', 'web']
base_url = 'https://search.seznam.cz/'


def request(query, params):
    params['url'] = base_url + '?' + urlencode({'q': query, 'oq': query})
    params['allow_redirects'] = True
    return params


def response(resp):
    if resp.url.path.startswith('/verify'):
        raise SearxEngineAccessDeniedException()

    results = []

    dom = resp.html()
    for result_element in eval_xpath_list(
        dom, '//div[@id="searchpage-root"]//div[@class="Layout--left"]/div[@class="f2c528"]'
    ):
        result_data = eval_xpath_getindex(
            result_element, './/div[@class="c8774a" or @class="e69e8d a11657"]', 0, default=None
        )
        if result_data is None:
            continue
        title_element = eval_xpath_getindex(result_element, './/h3/a', 0)
        results.append(
            {
                'url': title_element.get('href'),
                'title': extract_text(title_element),
                'content': extract_text(result_data),
            }
        )

    return results
