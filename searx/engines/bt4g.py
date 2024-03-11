# SPDX-License-Identifier: AGPL-3.0-or-later
"""BT4G_ (bt4g.com) is not a tracker and doesn't store any content and only
collects torrent metadata (such as file names and file sizes) and a magnet link
(torrent identifier).

This engine does not parse the HTML page because there is an API in XML (RSS).
The RSS feed provides fewer data like amount of seeders/leechers and the files
in the torrent file.  It's a tradeoff for a "stable" engine as the XML from RSS
content will change way less than the HTML page.

.. _BT4G: https://bt4g.com/

Configuration
=============

The engine has the following additional settings:

- :py:obj:`bt4g_order_by`
- :py:obj:`bt4g_category`

With this options a SearXNG maintainer is able to configure **additional**
engines for specific torrent searches.  For example a engine to search only for
Movies and sort the result list by the count of seeders.

.. code:: yaml

  - name: bt4g.movie
    engine: bt4g
    shortcut: bt4gv
    categories: video
    bt4g_order_by: seeders
    bt4g_category: 'movie'

Implementations
===============

"""

import re
from datetime import datetime
from urllib.parse import quote

from lxml import etree

from searx.utils import get_torrent_size

# about
about = {
    "website": 'https://bt4gprx.com',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'XML',
}

# engine dependent config
categories = ['files']
paging = True
time_range_support = True

# search-url
url = 'https://bt4gprx.com'
search_url = url + '/search?q={search_term}&orderby={order_by}&category={category}&p={pageno}&page=rss'
bt4g_order_by = 'relevance'
"""Result list can be ordered by ``relevance`` (default), ``size``, ``seeders``
or ``time``.

.. hint::

  When *time_range* is activate, the results always ordered by ``time``.
"""

bt4g_category = 'all'
"""BT$G offers categories: ``all`` (default), ``audio``, ``movie``, ``doc``,
``app`` and `` other``.
"""


def request(query, params):

    order_by = bt4g_order_by
    if params['time_range']:
        order_by = 'time'

    params['url'] = search_url.format(
        search_term=quote(query),
        order_by=order_by,
        category=bt4g_category,
        pageno=params['pageno'],
    )
    return params


def response(resp):
    results = []

    search_results = etree.XML(resp.content)

    # return empty array if nothing is found
    if len(search_results) == 0:
        return []

    for entry in search_results.xpath('./channel/item'):
        title = entry.find("title").text
        link = entry.find("guid").text
        fullDescription = entry.find("description").text.split('<br>')
        filesize = fullDescription[1]
        filesizeParsed = re.split(r"([A-Z]+)", filesize)
        magnetlink = entry.find("link").text
        pubDate = entry.find("pubDate").text
        results.append(
            {
                'url': link,
                'title': title,
                'magnetlink': magnetlink,
                'seed': 'N/A',
                'leech': 'N/A',
                'filesize': get_torrent_size(filesizeParsed[0], filesizeParsed[1]),
                'publishedDate': datetime.strptime(pubDate, '%a,%d %b %Y %H:%M:%S %z'),
                'template': 'torrent.html',
            }
        )

    return results
