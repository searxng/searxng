# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""SolidTorrents
"""

from datetime import datetime
from urllib.parse import urlencode
import random

from lxml import html

from searx.utils import (
    extract_text,
    eval_xpath,
    eval_xpath_getindex,
    eval_xpath_list,
    get_torrent_size,
)

about = {
    "website": 'https://www.solidtorrents.to/',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['files']
paging = True

# base_url can be overwritten by a list of URLs in the settings.yml
base_url = 'https://solidtorrents.to'


def request(query, params):
    if isinstance(base_url, list):
        params['base_url'] = random.choice(base_url)
    else:
        params['base_url'] = base_url
    search_url = params['base_url'] + '/search?{query}'
    query = urlencode({'q': query, 'page': params['pageno']})
    params['url'] = search_url.format(query=query)
    return params


def response(resp):
    results = []
    dom = html.fromstring(resp.text)

    for result in eval_xpath(dom, '//li[contains(@class, "search-result")]'):
        torrentfile = eval_xpath_getindex(result, './/a[contains(@class, "dl-torrent")]/@href', 0, None)
        magnet = eval_xpath_getindex(result, './/a[contains(@class, "dl-magnet")]/@href', 0, None)
        if torrentfile is None or magnet is None:
            continue  # ignore anime results that which aren't actually torrents
        title = eval_xpath_getindex(result, './/h5[contains(@class, "title")]', 0, None)
        url = eval_xpath_getindex(result, './/h5[contains(@class, "title")]/a/@href', 0, None)
        categ = eval_xpath(result, './/a[contains(@class, "category")]')
        stats = eval_xpath_list(result, './/div[contains(@class, "stats")]/div', min_len=5)

        params = {
            'seed': extract_text(stats[3]),
            'leech': extract_text(stats[2]),
            'title': extract_text(title),
            'url': resp.search_params['base_url'] + url,
            'filesize': get_torrent_size(*extract_text(stats[1]).split()),
            'magnetlink': magnet,
            'torrentfile': torrentfile,
            'metadata': extract_text(categ),
            'template': "torrent.html",
        }

        try:
            params['publishedDate'] = datetime.strptime(extract_text(stats[4]), '%b %d, %Y')
        except ValueError:
            pass

        results.append(params)

    return results
