# SPDX-License-Identifier: AGPL-3.0-or-later
"""Within this module we implement a *demo online engine*.  Do not look to
close to the implementation, its just a simple example which queries `The Art
Institute of Chicago <https://www.artic.edu>`_

Configuration
=============

To get in use of this *demo* engine add the following entry to your engines
list in ``settings.yml``:

.. code:: yaml

  - name: my online engine
    engine: demo_online
    shortcut: demo
    disabled: false

Implementations
===============

"""

import typing as t

from urllib.parse import urlencode
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


engine_type = "online"
send_accept_language_header = True
categories = ["general"]
disabled = True
timeout = 2.0
categories = ["images"]
paging = True
page_size = 20

search_api = "https://api.artic.edu/api/v1/artworks/search"
image_api = "https://www.artic.edu/iiif/2/"

about = {
    "website": "https://www.artic.edu",
    "wikidata_id": "Q239303",
    "official_api_documentation": "http://api.artic.edu/docs/",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}


# if there is a need for globals, use a leading underline
_my_online_engine = None


def setup(engine_settings: "OnlineParams") -> bool:
    """Dynamic setup of the engine settings.

    For more details see :py:obj:`searx.enginelib.Engine.setup`."""
    global _my_online_engine  # pylint: disable=global-statement
    _my_online_engine = engine_settings.get("name")
    return True


def init(engine_settings: dict[str, t.Any]) -> bool:  # pylint: disable=unused-argument
    """Initialization of the engine.

    For more details see :py:obj:`searx.enginelib.Engine.init`."""
    return True


def request(query: str, params: "OnlineParams") -> None:
    """Build up the ``params`` for the online request.  In this example we build a
    URL to fetch images from `artic.edu <https://artic.edu>`__."""
    args = urlencode(
        {
            "q": query,
            "page": params["pageno"],
            "fields": "id,title,artist_display,medium_display,image_id,date_display,dimensions,artist_titles",
            "limit": page_size,
        }
    )
    params["url"] = f"{search_api}?{args}"


def response(resp: "SXNG_Response") -> EngineResults:
    """Parse out the result items from the response.  In this example we parse the
    response from `api.artic.edu <https://artic.edu>`__ and filter out all
    images.

    """
    res = EngineResults()
    json_data = resp.json()

    res.add(
        res.types.Answer(
            answer="this is a dummy answer ..",
            url="https://example.org",
        )
    )

    for result in json_data["data"]:

        if not result["image_id"]:
            continue

        kwargs: dict[str, t.Any] = {
            "url": "https://artic.edu/artworks/%(id)s" % result,
            "title": result["title"] + " (%(date_display)s) // %(artist_display)s" % result,
            "content": "%(medium_display)s // %(dimensions)s" % result,
            "author": ", ".join(result["artist_titles"]),
            "img_src": image_api + "/%(image_id)s/full/843,/0/default.jpg" % result,
            "template": "images.html",
        }

        res.add(res.types.LegacyResult(**kwargs))

    return res
