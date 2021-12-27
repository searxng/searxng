# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Nyaa.si (Anime Bittorrent tracker)
"""

from lxml import html
from urllib.parse import urlencode
from searx.utils import extract_text, get_torrent_size, int_or_zero

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
search_url = base_url + '?page=search&{query}&offset={offset}'

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
    query = urlencode({'term': query})
    params['url'] = search_url.format(query=query, offset=params['pageno'])
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
        try:
            category = result.xpath(xpath_category)[0].attrib.get('title')
        except:
            pass

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
        try:
            filesize_info = result.xpath(xpath_filesize)[0]
            filesize, filesize_multiplier = filesize_info.split()
            filesize = get_torrent_size(filesize, filesize_multiplier)
        except:
            pass

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
