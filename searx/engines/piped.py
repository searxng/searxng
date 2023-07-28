# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""An alternative privacy-friendly YouTube frontend which is efficient by
design.  `Piped’s architecture`_ consists of 3 components:

- :py:obj:`backend <backend_url>`
- :py:obj:`frontend <frontend_url>`
- proxy

.. _Piped’s architecture: https://docs.piped.video/docs/architecture/

Configuration
=============

The :py:obj:`backend_url` and :py:obj:`frontend_url` has to be set in the engine
named `piped` and are used by all piped engines

.. code:: yaml

  - name: piped
    engine: piped
    piped_filter: videos
    ...
    frontend_url: https://..
    backend_url:
      - https://..
      - https://..

  - name: piped.music
    engine: piped
    network: piped
    shortcut: ppdm
    piped_filter: music_songs
    ...
"""

from __future__ import annotations

import time
import random
from urllib.parse import urlencode
import datetime
from dateutil import parser

# about
about = {
    "website": 'https://github.com/TeamPiped/Piped/',
    "wikidata_id": 'Q107565255',
    "official_api_documentation": 'https://docs.piped.video/docs/api-documentation/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = []
paging = False

# search-url
backend_url: list | str = "https://pipedapi.kavin.rocks"
"""Piped-Backend_: The core component behind Piped.  The value is an URL or a
list of URLs.  In the latter case instance will be selected randomly.  For a
complete list of offical instances see Piped-Instances (`JSON
<https://piped-instances.kavin.rocks/>`__)

.. _Piped-Instances: https://github.com/TeamPiped/Piped/wiki/Instances
.. _Piped-Backend: https://github.com/TeamPiped/Piped-Backend

"""

frontend_url: str = "https://piped.video"
"""Piped-Frontend_: URL to use as link and for embeds.

.. _Piped-Frontend: https://github.com/TeamPiped/Piped
"""

piped_filter = 'all'
"""Content filter ``music_songs`` or ``videos``"""


def _backend_url() -> str:
    from searx.engines import engines  # pylint: disable=import-outside-toplevel

    url = engines['piped'].backend_url  # type: ignore
    if isinstance(url, list):
        url = random.choice(url)
    return url


def _frontend_url() -> str:
    from searx.engines import engines  # pylint: disable=import-outside-toplevel

    return engines['piped'].frontend_url  # type: ignore


def request(query, params):

    query = urlencode({'q': query})
    params["url"] = _backend_url() + f"/search?{query}&filter={piped_filter}"

    return params


def response(resp):
    results = []

    search_results = resp.json()["items"]

    for result in search_results:
        publishedDate = parser.parse(time.ctime(result.get("uploaded", 0) / 1000))

        item = {
            # the api url differs from the frontend, hence use piped.video as default
            "url": _frontend_url() + result.get("url", ""),
            "title": result.get("title", ""),
            "publishedDate": publishedDate,
            "iframe_src": _frontend_url() + '/embed' + result.get("url", ""),
        }

        if piped_filter == 'videos':
            item["template"] = "videos.html"
            item["content"] = result.get("shortDescription", "")
            item["thumbnail"] = result.get("thumbnail", "")

        elif piped_filter == 'music_songs':
            item["template"] = "default.html"
            item["img_src"] = result.get("thumbnail", "")
            item["content"] = result.get("uploaderName", "")
            length = result.get("duration")
            if length:
                item["length"] = datetime.timedelta(seconds=length)

        results.append(item)

    return results
