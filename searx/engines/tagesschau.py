# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""ARD: `Tagesschau API`_

The Tagesschau is a news program of the ARD.  Via the `Tagesschau API`_, current
news and media reports are available in JSON format.  The `Bundesstelle für Open
Data`_ offers a `OpenAPI`_ portal at bundDEV_ where APIs are documented an can
be tested.

This SearXNG engine uses the `/api2u/search`_ API.

.. _/api2u/search: http://tagesschau.api.bund.dev/
.. _bundDEV: https://bund.dev/apis
.. _Bundesstelle für Open Data: https://github.com/bundesAPI
.. _Tagesschau API: https://github.com/AndreasFischer1985/tagesschau-api/blob/main/README_en.md
.. _OpenAPI: https://swagger.io/specification/

"""
from typing import TYPE_CHECKING

from datetime import datetime
from urllib.parse import urlencode
import re

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

about = {
    'website': "https://tagesschau.de",
    'wikidata_id': "Q703907",
    'official_api_documentation': None,
    'use_official_api': True,
    'require_api_key': False,
    'results': 'JSON',
    'language': 'de',
}
categories = ['general', 'news']
paging = True

results_per_page = 10
base_url = "https://www.tagesschau.de"

use_source_url = True
"""When set to false, display URLs from Tagesschau, and not the actual source
(e.g. NDR, WDR, SWR, HR, ...)

.. note::

   The actual source may contain additional content, such as commentary, that is
   not displayed in the Tagesschau.

"""


def request(query, params):
    args = {
        'searchText': query,
        'pageSize': results_per_page,
        'resultPage': params['pageno'] - 1,
    }

    params['url'] = f"{base_url}/api2u/search?{urlencode(args)}"

    return params


def response(resp):
    results = []

    json = resp.json()

    for item in json['searchResults']:
        item_type = item.get('type')
        if item_type in ('story', 'webview'):
            results.append(_story(item))
        elif item_type == 'video':
            results.append(_video(item))
        else:
            logger.error("unknow result type: %s", item_type)

    return results


def _story(item):
    return {
        'title': item['title'],
        'thumbnail': item.get('teaserImage', {}).get('imageVariants', {}).get('16x9-256'),
        'publishedDate': datetime.strptime(item['date'][:19], '%Y-%m-%dT%H:%M:%S'),
        'content': item['firstSentence'],
        'url': item['shareURL'] if use_source_url else item['detailsweb'],
    }


def _video(item):
    streams = item['streams']
    video_url = streams.get('h264s') or streams.get('h264m') or streams.get('h264l') or streams.get('h264xl')
    title = item['title']

    if "_vapp.mxf" in title:
        title = title.replace("_vapp.mxf", "")
        title = re.sub(r"APP\d+ (FC-)?", "", title, count=1)

    return {
        'template': 'videos.html',
        'title': title,
        'thumbnail': item.get('teaserImage', {}).get('imageVariants', {}).get('16x9-256'),
        'publishedDate': datetime.strptime(item['date'][:19], '%Y-%m-%dT%H:%M:%S'),
        'content': item.get('firstSentence', ''),
        'iframe_src': video_url,
        'url': video_url,
    }
