# SPDX-License-Identifier: AGPL-3.0-or-later
"""Nyaa.si (Anime Bittorrent tracker)

"""

from urllib.parse import urlencode

from lxml import html
from searx.utils import (
    eval_xpath_getindex,
    extract_text,
    get_torrent_size,
    int_or_zero,
)

# about
about = {
    "website": 'https://nyaa.si/',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['files']
paging = True

# search-url
base_url = 'https://nyaa.si/'

# xpath queries
xpath_results = '//table[contains(@class, "torrent-list")]//tr[not(th)]'
xpath_category = './/td[1]/a[1]'
xpath_title = './/td[2]/a[last()]'
xpath_torrent_links = './/td[3]/a'
xpath_filesize = './/td[4]/text()'
xpath_seeds = './/td[6]/text()'
xpath_leeches = './/td[7]/text()'
xpath_downloads = './/td[8]/text()'


# do search-request
def request(query, params):
    args = urlencode(
        {
            'q': query,
            'p': params['pageno'],
        }
    )
    params['url'] = base_url + '?' + args  #
    logger.debug("query_url --> %s", params['url'])
    return params


# get response from search-request
def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    for result in dom.xpath(xpath_results):
        # defaults
        filesize = 0
        magnet_link = ""
        torrent_link = ""

        # category in which our torrent belongs

        category = eval_xpath_getindex(result, xpath_category, 0, '')
        if category:
            category = category.attrib.get('title')

        # torrent title
        page_a = result.xpath(xpath_title)[0]
        title = extract_text(page_a)

        # link to the page
        href = base_url + page_a.attrib.get('href')

        for link in result.xpath(xpath_torrent_links):
            url = link.attrib.get('href')
            if 'magnet' in url:
                # link to the magnet
                magnet_link = url
            else:
                # link to the torrent file
                torrent_link = url

        # seed count
        seed = int_or_zero(result.xpath(xpath_seeds))

        # leech count
        leech = int_or_zero(result.xpath(xpath_leeches))

        # torrent downloads count
        downloads = int_or_zero(result.xpath(xpath_downloads))

        # let's try to calculate the torrent size

        filesize = None
        filesize_info = eval_xpath_getindex(result, xpath_filesize, 0, '')
        if filesize_info:
            filesize_info = result.xpath(xpath_filesize)[0]
            filesize = get_torrent_size(*filesize_info.split())

        # content string contains all information not included into template
        content = 'Category: "{category}". Downloaded {downloads} times.'
        content = content.format(category=category, downloads=downloads)

        results.append(
            {
                'url': href,
                'title': title,
                'content': content,
                'seed': seed,
                'leech': leech,
                'filesize': filesize,
                'torrentfile': torrent_link,
                'magnetlink': magnet_link,
                'template': 'torrent.html',
            }
        )

    return results
