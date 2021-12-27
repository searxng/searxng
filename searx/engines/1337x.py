# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 1337x
"""

from urllib.parse import quote, urljoin
from lxml import html
from searx.utils import extract_text, get_torrent_size, eval_xpath, eval_xpath_list, eval_xpath_getindex

# about
about = {
    "website": 'https://1337x.to/',
    "wikidata_id": 'Q28134166',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

url = 'https://1337x.to/'
search_url = url + 'search/{search_term}/{pageno}/'
categories = ['files']
paging = True


def request(query, params):
    params['url'] = search_url.format(search_term=quote(query), pageno=params['pageno'])

    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, '//table[contains(@class, "table-list")]/tbody//tr'):
        href = urljoin(url, eval_xpath_getindex(result, './td[contains(@class, "name")]/a[2]/@href', 0))
        title = extract_text(eval_xpath(result, './td[contains(@class, "name")]/a[2]'))
        seed = extract_text(eval_xpath(result, './/td[contains(@class, "seeds")]'))
        leech = extract_text(eval_xpath(result, './/td[contains(@class, "leeches")]'))
        filesize_info = extract_text(eval_xpath(result, './/td[contains(@class, "size")]/text()'))
        filesize, filesize_multiplier = filesize_info.split()
        filesize = get_torrent_size(filesize, filesize_multiplier)

        results.append(
            {
                'url': href,
                'title': title,
                'seed': seed,
                'leech': leech,
                'filesize': filesize,
                'template': 'torrent.html',
            }
        )

    return results
