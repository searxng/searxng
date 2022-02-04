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
    get_torrent_size,
)

about = {
    "website": 'https://www.solidtorrents.net/',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['files']
paging = True

base_url = ''
base_url_rand = ''


def request(query, params):
    global base_url_rand  # pylint: disable=global-statement
    if isinstance(base_url, list):
        base_url_rand = random.choice(base_url)
    else:
        base_url_rand = base_url
    search_url = base_url_rand + '/search?{query}'
    page = (params['pageno'] - 1) * 20
    query = urlencode({'q': query, 'page': page})
    params['url'] = search_url.format(query=query)
    return params


def response(resp):
    results = []
    dom = html.fromstring(resp.text)

    for result in eval_xpath(dom, '//div[contains(@class, "search-result")]'):
        a = eval_xpath_getindex(result, './div/h5/a', 0, None)
        if a is None:
            continue
        title = extract_text(a)
        url = eval_xpath_getindex(a, '@href', 0, None)
        stats = eval_xpath(result, './div//div[contains(@class, "stats")]/div')
        n, u = extract_text(stats[1]).split()
        filesize = get_torrent_size(n, u)
        leech = extract_text(stats[2])
        seed = extract_text(stats[3])
        magnet = eval_xpath_getindex(result, './div//a[contains(@class, "dl-magnet")]/@href', 0, None)

        params = {
            'seed': seed,
            'leech': leech,
            'title': title,
            'url': base_url_rand + url,
            'filesize': filesize,
            'magnetlink': magnet,
            'template': "torrent.html",
        }

        date_str = extract_text(stats[4])

        try:
            params['publishedDate'] = datetime.strptime(date_str, '%b %d, %Y')
        except ValueError:
            pass

        results.append(params)

    return results
