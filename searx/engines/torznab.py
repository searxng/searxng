# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Torznab WebAPI

A engine that implements the `torznab WebAPI`_.

.. _torznab WebAPI: https://torznab.github.io/spec-1.3-draft/torznab

"""

from datetime import datetime
from urllib.parse import quote
from lxml import etree

from searx.exceptions import SearxEngineAPIException

# about
about = {
    "website": None,
    "wikidata_id": None,
    "official_api_documentation": "https://torznab.github.io/spec-1.3-draft",
    "use_official_api": True,
    "require_api_key": False,
    "results": 'XML',
}

categories = ['files']
paging = False
time_range_support = False

# defined in settings.yml
# example (Jackett): "http://localhost:9117/api/v2.0/indexers/all/results/torznab"
base_url = ''
api_key = ''
# https://newznab.readthedocs.io/en/latest/misc/api/#predefined-categories
torznab_categories = []


def init(engine_settings=None):  # pylint: disable=unused-argument
    if len(base_url) < 1:
        raise ValueError('missing torznab base_url')


def request(query, params):

    search_url = base_url + '?t=search&q={search_query}'
    if len(api_key) > 0:
        search_url += '&apikey={api_key}'
    if len(torznab_categories) > 0:
        search_url += '&cat={torznab_categories}'

    params['url'] = search_url.format(
        search_query=quote(query), api_key=api_key, torznab_categories=",".join([str(x) for x in torznab_categories])
    )

    return params


def response(resp):
    results = []

    search_results = etree.XML(resp.content)

    # handle errors
    # https://newznab.readthedocs.io/en/latest/misc/api/#newznab-error-codes
    if search_results.tag == "error":
        raise SearxEngineAPIException(search_results.get("description"))

    for item in search_results[0].iterfind('item'):
        result = {'template': 'torrent.html'}

        enclosure = item.find('enclosure')

        result["filesize"] = int(enclosure.get('length'))

        link = get_property(item, 'link')
        guid = get_property(item, 'guid')
        comments = get_property(item, 'comments')

        # define url
        result["url"] = enclosure.get('url')
        if comments is not None and comments.startswith('http'):
            result["url"] = comments
        elif guid is not None and guid.startswith('http'):
            result["url"] = guid

        # define torrent file url
        result["torrentfile"] = None
        if enclosure.get('url').startswith("http"):
            result["torrentfile"] = enclosure.get('url')
        elif link is not None and link.startswith('http'):
            result["torrentfile"] = link

        # define magnet link
        result["magnetlink"] = get_torznab_attr(item, 'magneturl')
        if result["magnetlink"] is None:
            if enclosure.get('url').startswith("magnet"):
                result["magnetlink"] = enclosure.get('url')
            elif link is not None and link.startswith('magnet'):
                result["magnetlink"] = link

        result["title"] = get_property(item, 'title')
        result["files"] = get_property(item, 'files')

        result["publishedDate"] = None
        try:
            result["publishedDate"] = datetime.strptime(get_property(item, 'pubDate'), '%a, %d %b %Y %H:%M:%S %z')
        except (ValueError, TypeError) as e:
            logger.debug("ignore exception (publishedDate): %s", e)

        result["seed"] = get_torznab_attr(item, 'seeders')

        # define leech
        result["leech"] = get_torznab_attr(item, 'leechers')
        if result["leech"] is None and result["seed"] is not None:
            peers = get_torznab_attr(item, 'peers')
            if peers is not None:
                result["leech"] = int(peers) - int(result["seed"])

        results.append(result)

    return results


def get_property(item, property_name):
    property_element = item.find(property_name)

    if property_element is not None:
        return property_element.text

    return None


def get_torznab_attr(item, attr_name):
    element = item.find(
        './/torznab:attr[@name="{attr_name}"]'.format(attr_name=attr_name),
        {'torznab': 'http://torznab.com/schemas/2015/feed'},
    )

    if element is not None:
        return element.get("value")

    return None
