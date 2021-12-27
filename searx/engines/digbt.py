# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 DigBT (Videos, Music, Files)
"""

from urllib.parse import urljoin
from lxml import html
from searx.utils import extract_text, get_torrent_size

# about
about = {
    "website": 'https://digbt.org',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['videos', 'music', 'files']
paging = True

URL = 'https://digbt.org'
SEARCH_URL = URL + '/search/{query}-time-{pageno}'
FILESIZE = 3
FILESIZE_MULTIPLIER = 4


def request(query, params):
    params['url'] = SEARCH_URL.format(query=query, pageno=params['pageno'])

    return params


def response(resp):
    dom = html.fromstring(resp.text)
    search_res = dom.xpath('.//td[@class="x-item"]')

    if not search_res:
        return list()

    results = list()
    for result in search_res:
        url = urljoin(URL, result.xpath('.//a[@title]/@href')[0])
        title = extract_text(result.xpath('.//a[@title]'))
        content = extract_text(result.xpath('.//div[@class="files"]'))
        files_data = extract_text(result.xpath('.//div[@class="tail"]')).split()
        filesize = get_torrent_size(files_data[FILESIZE], files_data[FILESIZE_MULTIPLIER])
        magnetlink = result.xpath('.//div[@class="tail"]//a[@class="title"]/@href')[0]

        results.append(
            {
                'url': url,
                'title': title,
                'content': content,
                'filesize': filesize,
                'magnetlink': magnetlink,
                'seed': 'N/A',
                'leech': 'N/A',
                'template': 'torrent.html',
            }
        )

    return results
