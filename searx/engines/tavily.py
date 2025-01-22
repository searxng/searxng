# SPDX-License-Identifier: AGPL-3.0-or-later
"""

.. sidebar:: info

   Before reporting an issue with this engine,
   please consult `API error codes`_.

Tavily_ search API (AI engine).  This engine implements the REST API
(`POST /search`_) and does not make use of the `Tavily Python Wrapper`_.

From the API response this engine generates *result items* (shown in the main
result list) and an *answer result* (shown on top of the main result list).
If the *answer* from Tavily contains an image, the *answer result* is turned
into a *infobox result*.

.. attention::

   AI queries take considerably longer to process than queries to conventional
   search engines.  The ``timeout`` should therefore also be set considerably
   higher, but it is not recommended to activate AI queries by default
   (set ``disabled: true``), as otherwise all user searches will have to wait
   for the AI.

.. _Tavily: https://tavily.com/
.. _Tavily Python Wrapper: https://pypi.org/project/tavily-python/
.. _POST /search: https://docs.tavily.com/docs/rest-api/api-reference#endpoint-post-search
.. _Tavily API Credit Deduction:
   https://docs.tavily.com/docs/rest-api/api-reference#tavily-api-credit-deduction-overview
.. _Getting started: https://docs.tavily.com/docs/welcome#getting-started
.. _API error codes: https://docs.tavily.com/docs/rest-api/api-reference#error-codes

Configuration
=============

The engine has the following mandatory setting:

- :py:obj:`api_key`
- :py:obj:`topic`

Optional settings are:

- :py:obj:`days`
- :py:obj:`search_depth`
- :py:obj:`max_results`
- :py:obj:`include_images`
- :py:obj:`include_domains`
- :py:obj:`exclude_domains`

Example configuration for general search queries:

.. code:: yaml

  - name: tavily
    engine: tavily
    shortcut: tav
    categories: [general, ai]
    api_key: xxxxxxxx
    topic: general
    include_images: true
    timeout: 15
    disabled: true

Example configuration for news search:

.. code:: yaml

  - name: tavily news
    engine: tavily
    shortcut: tavnews
    categories: [news, ai]
    api_key: xxxxxxxx
    topic: news
    timeout: 15
    disabled: true


Implementation
==============

"""

from json import dumps
from datetime import datetime
from flask_babel import gettext

# about
about = {
    "website": "https://tavily.com/",
    "wikidata_id": None,
    "official_api_documentation": "https://docs.tavily.com/docs/rest-api/api-reference",
    "use_official_api": True,
    "require_api_key": True,
    "results": 'JSON',
}

search_url = "https://api.tavily.com/search"
paging = False
time_range_support = True

api_key: str = "unset"
"""Tavily API Key (`Getting started`_)."""

search_depth: str = "basic"
"""The depth of the search.  It can be ``basic`` or ``advanced``.  Default is
``basic`` unless specified otherwise in a given method.

- have an eye on your `Tavily API Credit Deduction`_!
"""

topic: str = ""
"""The category of the search.  This will determine which of tavily's agents
will be used for the search.  Currently: only ``general`` and ``news`` are
supported and ``general`` will implicitly activate ``include_answer`` in the
`POST /search`_ API."""

days: int = 3
"""The number of days back from the current date to include in the search results.
This specifies the time frame of data to be retrieved.  Please note that this
feature is only available when using the ``news`` search topic. Default is 3."""

max_results: int = 5
"""The maximum number of search results to return.  Default is 5."""

include_images: bool = False
"""Include a list of query-related images in the response.  Turns answer into
infobox with first image (as far there are any images in the response).  Will
implicitly activate ``include_image_descriptions`` in the `POST /search`_ API
(adds descriptive text for each image).
"""

include_domains: list[str] = []
"""A list of domains to specifically include in the search results. Default
is ``[]```, which includes all domains."""

exclude_domains: list[str] = []
"""A list of domains to specifically exclude from the search results. Default
is ``[]``, which doesn't exclude any domains.
"""


def request(query, params):

    data = {
        "query": query,
        "api_key": api_key,
        "search_depth": search_depth,
        "topic": topic,
        "time_range": params["time_range"],
        "max_results": max_results,
        "include_images": include_images,
        "include_domains": include_domains,
        "exclude_domains": exclude_domains,
    }

    if include_images:
        data["include_image_descriptions"] = True

    if topic == "general":
        data["include_answer"] = True

    elif topic == "news":
        data["topic"] = "news"
        data["days"] = days

    params["url"] = search_url
    params["method"] = "POST"
    params["headers"]["Content-type"] = "application/json"
    params["data"] = dumps(data)

    return params


def response(resp):
    results = []
    data = resp.json()

    for result in data.get("results", []):
        results.append(
            {
                "title": f"[{gettext('ai')}] {result['title']}",
                "url": result["url"],
                "content": result["content"],
                "publishedDate": _parse_date(result.get("published_date")),
            }
        )

    img_list = data.get("images")
    if img_list:
        content = data.get("answer")
        img_src = img_list[0]
        if isinstance(img_list[0], dict):
            img_src = img_list[0]["url"]
            img_caption = gettext("Image caption") + ": " + img_list[0]["description"]
            if not content:
                gettext("Image caption")
                content = img_caption
            else:
                content += "//" + img_caption

        results.append(
            {
                "infobox": f"Tavily [{gettext('ai')}]",
                "img_src": img_src,
                "content": content,
            }
        )

    elif data["answer"]:
        results.append({"answer": data["answer"]})

    return results


def _parse_date(pubDate):
    if pubDate is not None:
        try:
            return datetime.strptime(pubDate, "%a, %d %b %Y %H:%M:%S %Z")
        except (ValueError, TypeError) as e:
            logger.debug("ignore exception (publishedDate): %s", e)
    return None


def init(engine_settings: dict):
    msg = []

    val = engine_settings.get("api_key") or api_key
    if not val or val == "unset":
        msg.append("missing api_key")

    val = engine_settings.get("topic") or topic
    if val not in ["general", "news"]:
        msg.append(f"invalid topic: '{val}'")

    val = engine_settings.get("search_depth") or search_depth
    if val not in ["basic", "advanced"]:
        msg.append(f"invalid search_depth: '{val}'")

    if msg:
        raise ValueError(f"[{engine_settings['name']}] engine's settings: {' / '.join(msg)}")
