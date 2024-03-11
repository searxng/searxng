# SPDX-License-Identifier: AGPL-3.0-or-later
"""Presearch supports the search types listed in :py:obj:`search_type` (general,
images, videos, news).

Configured ``presarch`` engines:

.. code:: yaml

  - name: presearch
    engine: presearch
    search_type: search
    categories: [general, web]

  - name: presearch images
    ...
    search_type: images
    categories: [images, web]

  - name: presearch videos
    ...
    search_type: videos
    categories: [general, web]

  - name: presearch news
    ...
    search_type: news
    categories: [news, web]

.. hint::

   By default Presearch's video category is intentionally placed into::

       categories: [general, web]


Search type ``video``
=====================

The results in the video category are most often links to pages that contain a
video, for instance many links from Preasearch's video category link content
from facebook (aka Meta) or Twitter (aka X).  Since these are not real links to
video streams SearXNG can't use the video template for this and if SearXNG can't
use this template, then the user doesn't want to see these hits in the videos
category.


Languages & Regions
===================

In Presearch there are languages for the UI and regions for narrowing down the
search.  If we set "auto" for the region in the WEB-UI of Presearch and cookie
``use_local_search_results=false``, then the defaults are set for both (the
language and the region) from the ``Accept-Language`` header.

Since the region is already "auto" by default, we only need to set the
``use_local_search_results`` cookie and send the ``Accept-Language`` header.  We
have to set these values in both requests we send to Presearch; in the first
request to get the request-ID from Presearch and in the final request to get the
result list (see ``send_accept_language_header``).


Implementations
===============

"""

from urllib.parse import urlencode
from searx import locales
from searx.network import get
from searx.utils import gen_useragent, html_to_text

about = {
    "website": "https://presearch.io",
    "wikidiata_id": "Q7240905",
    "official_api_documentation": "https://docs.presearch.io/nodes/api",
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}
paging = True
safesearch = True
time_range_support = True
send_accept_language_header = True
categories = ["general", "web"]  # general, images, videos, news

search_type = "search"
"""must be any of ``search``, ``images``, ``videos``, ``news``"""

base_url = "https://presearch.com"
safesearch_map = {0: 'false', 1: 'true', 2: 'true'}


def init(_):
    if search_type not in ['search', 'images', 'videos', 'news']:
        raise ValueError(f'presearch search_type: {search_type}')


def _get_request_id(query, params):

    args = {
        "q": query,
        "page": params["pageno"],
    }

    if params["time_range"]:
        args["time"] = params["time_range"]

    url = f"{base_url}/{search_type}?{urlencode(args)}"

    headers = {
        'User-Agent': gen_useragent(),
        'Cookie': (
            f"b=1;"
            f" presearch_session=;"
            f" use_local_search_results=false;"
            f" use_safe_search={safesearch_map[params['safesearch']]}"
        ),
    }
    if params['searxng_locale'] != 'all':
        l = locales.get_locale(params['searxng_locale'])

        # Presearch narrows down the search by region.  In SearXNG when the user
        # does not set a region (e.g. 'en-CA' / canada) we cannot hand over a region.

        # We could possibly use searx.locales.get_official_locales to determine
        # in which regions this language is an official one, but then we still
        # wouldn't know which region should be given more weight / Presearch
        # performs an IP-based geolocation of the user, we don't want that in
        # SearXNG ;-)

        if l.territory:
            headers['Accept-Language'] = f"{l.language}-{l.territory},{l.language};" "q=0.9,*;" "q=0.5"

    resp_text = get(url, headers=headers).text  # type: ignore

    for line in resp_text.split("\n"):
        if "window.searchId = " in line:
            return line.split("= ")[1][:-1].replace('"', "")

    return None


def request(query, params):
    request_id = _get_request_id(query, params)
    params["headers"]["Accept"] = "application/json"
    params["url"] = f"{base_url}/results?id={request_id}"

    return params


def _strip_leading_strings(text):
    for x in ['wikipedia', 'google']:
        if text.lower().endswith(x):
            text = text[: -len(x)]
    return text.strip()


def parse_search_query(json_results):
    results = []

    for item in json_results.get('specialSections', {}).get('topStoriesCompact', {}).get('data', []):
        result = {
            'url': item['link'],
            'title': item['title'],
            'img_src': item['image'],
            'content': '',
            'metadata': item.get('source'),
        }
        results.append(result)

    for item in json_results.get('standardResults', []):
        result = {
            'url': item['link'],
            'title': item['title'],
            'content': html_to_text(item['description']),
        }
        results.append(result)

    info = json_results.get('infoSection', {}).get('data')
    if info:
        attributes = []
        for item in info.get('about', []):

            text = html_to_text(item)
            if ':' in text:
                # split text into key / value
                label, value = text.split(':', 1)
            else:
                # In other languages (tested with zh-TW) a colon is represented
                # by a different symbol --> then we split at the first space.
                label, value = text.split(' ', 1)
                label = label[:-1]

            value = _strip_leading_strings(value)
            attributes.append({'label': label, 'value': value})
        content = []
        for item in [info.get('subtitle'), info.get('description')]:
            if not item:
                continue
            item = _strip_leading_strings(html_to_text(item))
            if item:
                content.append(item)

        results.append(
            {
                'infobox': info['title'],
                'id': info['title'],
                'img_src': info.get('image'),
                'content': ' | '.join(content),
                'attributes': attributes,
            }
        )
    return results


def response(resp):
    results = []
    json_resp = resp.json()

    if search_type == 'search':
        results = parse_search_query(json_resp.get('results'))

    elif search_type == 'images':
        for item in json_resp.get('images', []):
            results.append(
                {
                    'template': 'images.html',
                    'title': item['title'],
                    'url': item.get('link'),
                    'img_src': item.get('image'),
                    'thumbnail_src': item.get('thumbnail'),
                }
            )

    elif search_type == 'videos':
        # The results in the video category are most often links to pages that contain
        # a video and not to a video stream --> SearXNG can't use the video template.

        for item in json_resp.get('videos', []):
            metadata = [x for x in [item.get('description'), item.get('duration')] if x]
            results.append(
                {
                    'title': item['title'],
                    'url': item.get('link'),
                    'content': '',
                    'metadata': ' / '.join(metadata),
                    'img_src': item.get('image'),
                }
            )

    elif search_type == 'news':
        for item in json_resp.get('news', []):
            metadata = [x for x in [item.get('source'), item.get('time')] if x]
            results.append(
                {
                    'title': item['title'],
                    'url': item.get('link'),
                    'content': item.get('description', ''),
                    'metadata': ' / '.join(metadata),
                    'img_src': item.get('image'),
                }
            )

    return results
