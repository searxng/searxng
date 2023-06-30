# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Torznab_ is an API specification that provides a standardized way to query
torrent site for content. It is used by a number of torrent applications,
including Prowlarr_ and Jackett_.

Using this engine together with Prowlarr_ or Jackett_ allows you to search
a huge number of torrent sites which are not directly supported.

Configuration
=============

The engine has the following settings:

``base_url``:
  Torznab endpoint URL.

``api_key``:
  The API key to use for authentication.

``torznab_categories``:
  The categories to use for searching. This is a list of category IDs.  See
  Prowlarr-categories_ or Jackett-categories_ for more information.

``show_torrent_files``:
  Whether to show the torrent file in the search results.  Be carful as using
  this with Prowlarr_ or Jackett_ leaks the API key.  This should be used only
  if you are querying a Torznab endpoint without authentication or if the
  instance is private.  Be aware that private trackers may ban you if you share
  the torrent file.  Defaults to ``false``.

``show_magnet_links``:
  Whether to show the magnet link in the search results.  Be aware that private
  trackers may ban you if you share the magnet link.  Defaults to ``true``.

.. _Torznab:
   https://torznab.github.io/spec-1.3-draft/index.html
.. _Prowlarr:
   https://github.com/Prowlarr/Prowlarr
.. _Jackett:
   https://github.com/Jackett/Jackett
.. _Prowlarr-categories:
   https://wiki.servarr.com/en/prowlarr/cardigann-yml-definition#categories
.. _Jackett-categories:
   https://github.com/Jackett/Jackett/wiki/Jackett-Categories

Implementations
===============

"""
from __future__ import annotations
from typing import TYPE_CHECKING

from typing import List, Dict, Any
from datetime import datetime
from urllib.parse import quote
from lxml import etree  # type: ignore

from searx.exceptions import SearxEngineAPIException

if TYPE_CHECKING:
    import httpx
    import logging

    logger: logging.Logger

# engine settings
about: Dict[str, Any] = {
    "website": None,
    "wikidata_id": None,
    "official_api_documentation": "https://torznab.github.io/spec-1.3-draft",
    "use_official_api": True,
    "require_api_key": False,
    "results": 'XML',
}
categories: List[str] = ['files']
paging: bool = False
time_range_support: bool = False

# defined in settings.yml
# example (Jackett): "http://localhost:9117/api/v2.0/indexers/all/results/torznab"
base_url: str = ''
api_key: str = ''
# https://newznab.readthedocs.io/en/latest/misc/api/#predefined-categories
torznab_categories: List[str] = []
show_torrent_files: bool = False
show_magnet_links: bool = True


def init(engine_settings=None):  # pylint: disable=unused-argument
    """Initialize the engine."""
    if len(base_url) < 1:
        raise ValueError('missing torznab base_url')


def request(query: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Build the request params."""
    search_url: str = base_url + '?t=search&q={search_query}'

    if len(api_key) > 0:
        search_url += '&apikey={api_key}'
    if len(torznab_categories) > 0:
        search_url += '&cat={torznab_categories}'

    params['url'] = search_url.format(
        search_query=quote(query), api_key=api_key, torznab_categories=",".join([str(x) for x in torznab_categories])
    )

    return params


def response(resp: httpx.Response) -> List[Dict[str, Any]]:
    """Parse the XML response and return a list of results."""
    results = []
    search_results = etree.XML(resp.content)

    # handle errors:  https://newznab.readthedocs.io/en/latest/misc/api/#newznab-error-codes
    if search_results.tag == "error":
        raise SearxEngineAPIException(search_results.get("description"))

    channel: etree.Element = search_results[0]

    item: etree.Element
    for item in channel.iterfind('item'):
        result: Dict[str, Any] = build_result(item)
        results.append(result)

    return results


def build_result(item: etree.Element) -> Dict[str, Any]:
    """Build a result from a XML item."""

    # extract attributes from XML
    # see https://torznab.github.io/spec-1.3-draft/torznab/Specification-v1.3.html#predefined-attributes
    enclosure: etree.Element | None = item.find('enclosure')
    enclosure_url: str | None = None
    if enclosure is not None:
        enclosure_url = enclosure.get('url')

    size = get_attribute(item, 'size')
    if not size and enclosure:
        size = enclosure.get('length')
    if size:
        size = int(size)

    guid = get_attribute(item, 'guid')
    comments = get_attribute(item, 'comments')
    pubDate = get_attribute(item, 'pubDate')
    seeders = get_torznab_attribute(item, 'seeders')
    leechers = get_torznab_attribute(item, 'leechers')
    peers = get_torznab_attribute(item, 'peers')

    # map attributes to searx result
    result: Dict[str, Any] = {
        'template': 'torrent.html',
        'title': get_attribute(item, 'title'),
        'filesize': size,
        'files': get_attribute(item, 'files'),
        'seed': seeders,
        'leech': _map_leechers(leechers, seeders, peers),
        'url': _map_result_url(guid, comments),
        'publishedDate': _map_published_date(pubDate),
        'torrentfile': None,
        'magnetlink': None,
    }

    link = get_attribute(item, 'link')
    if show_torrent_files:
        result['torrentfile'] = _map_torrent_file(link, enclosure_url)
    if show_magnet_links:
        magneturl = get_torznab_attribute(item, 'magneturl')
        result['magnetlink'] = _map_magnet_link(magneturl, guid, enclosure_url, link)
    return result


def _map_result_url(guid: str | None, comments: str | None) -> str | None:
    if guid and guid.startswith('http'):
        return guid
    if comments and comments.startswith('http'):
        return comments
    return None


def _map_leechers(leechers: str | None, seeders: str | None, peers: str | None) -> str | None:
    if leechers:
        return leechers
    if seeders and peers:
        return str(int(peers) - int(seeders))
    return None


def _map_published_date(pubDate: str | None) -> datetime | None:
    if pubDate is not None:
        try:
            return datetime.strptime(pubDate, '%a, %d %b %Y %H:%M:%S %z')
        except (ValueError, TypeError) as e:
            logger.debug("ignore exception (publishedDate): %s", e)
    return None


def _map_torrent_file(link: str | None, enclosure_url: str | None) -> str | None:
    if link and link.startswith('http'):
        return link
    if enclosure_url and enclosure_url.startswith('http'):
        return enclosure_url
    return None


def _map_magnet_link(
    magneturl: str | None,
    guid: str | None,
    enclosure_url: str | None,
    link: str | None,
) -> str | None:
    if magneturl and magneturl.startswith('magnet'):
        return magneturl
    if guid and guid.startswith('magnet'):
        return guid
    if enclosure_url and enclosure_url.startswith('magnet'):
        return enclosure_url
    if link and link.startswith('magnet'):
        return link
    return None


def get_attribute(item: etree.Element, property_name: str) -> str | None:
    """Get attribute from item."""
    property_element: etree.Element | None = item.find(property_name)
    if property_element is not None:
        return property_element.text
    return None


def get_torznab_attribute(item: etree.Element, attribute_name: str) -> str | None:
    """Get torznab special attribute from item."""
    element: etree.Element | None = item.find(
        './/torznab:attr[@name="{attribute_name}"]'.format(attribute_name=attribute_name),
        {'torznab': 'http://torznab.com/schemas/2015/feed'},
    )
    if element is not None:
        return element.get("value")
    return None
