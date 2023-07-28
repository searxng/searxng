# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""An alternative privacy-friendly YouTube frontend which is efficient by
design.  `Piped’s architecture`_ consists of 3 components:

- :py:obj:`backend <backend_url>`
- :py:obj:`frontend <frontend_url>`
- proxy

.. _Piped’s architecture: https://docs.piped.video/docs/architecture/

"""

from __future__ import annotations

import time
import random
from urllib.parse import urlencode
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
categories = ["videos", "music"]
paging = False

# search-url
backend_url: list|str = "https://pipedapi.kavin.rocks"
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

content_filter = 'videos'
"""Content filter ``music_albums`` or ``videos``"""

def request(query, params):
    if isinstance(backend_url, list):
        base_url = random.choice(backend_url)
    else:
        base_url = backend_url

    query = urlencode({'q': query})
    params["url"] = base_url + f"/search?{query}&filter={content_filter}"

    return params


def response(resp):
    results = []

    search_results = resp.json()["items"]

    for result in search_results:
        publishedDate = parser.parse(time.ctime(result.get("uploaded", 0) / 1000))

        results.append(
            {
                # the api url differs from the frontend, hence use piped.video as default
                "url": frontend_url + result.get("url", ""),
                "title": result.get("title", ""),
                "content": result.get("shortDescription", ""),
                "template": "videos.html",
                "publishedDate": publishedDate,
                "iframe_src": frontend_url + '/embed' + result.get("url", ""),
                "thumbnail": result.get("thumbnail", ""),
            }
        )

    return results
