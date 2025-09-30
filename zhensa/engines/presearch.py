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
video streams Zhensa can't use the video template for this and if Zhensa can't
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

The time format returned by Presearch varies depending on the language set.
Multiple different formats can be supported by using ``dateutil`` parser, but
it doesn't support formats such as "N time ago", "vor N time" (German),
"Hace N time" (Spanish). Because of this, the dates are simply joined together
with the rest of other metadata.


Implementations
===============

"""

from urllib.parse import urlencode, urlparse
from zhensa import locales
from zhensa.network import get
from zhensa.utils import gen_useragent, html_to_text, parse_duration_string

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
    if params['zhensa_locale'] != 'all':
        l = locales.get_locale(params['zhensa_locale'])

        # Presearch narrows down the search by region.  In Zhensa when the user
        # does not set a region (e.g. 'en-CA' / canada) we cannot hand over a region.

        # We could possibly use zhensa.locales.get_official_locales to determine
        # in which regions this language is an official one, but then we still
        # wouldn't know which region should be given more weight / Presearch
        # performs an IP-based geolocation of the user, we don't want that in
        # Zhensa ;-)

        if l.territory:
            headers['Accept-Language'] = f"{l.language}-{l.territory},{l.language};" "q=0.9,*;" "q=0.5"

    resp = get(url, headers=headers)

    for line in resp.text.split("\n"):
        if "window.searchId = " in line:
            return line.split("= ")[1][:-1].replace('"', ""), resp.cookies

    raise RuntimeError("Couldn't find any request id for presearch")


def request(query, params):
    request_id, cookies = _get_request_id(query, params)
    params["headers"]["Accept"] = "application/json"
    params["url"] = f"{base_url}/results?id={request_id}"
    params["cookies"] = cookies

    return params


def _strip_leading_strings(text):
    for x in ['wikipedia', 'google']:
        if text.lower().endswith(x):
            text = text[: -len(x)]
    return text.strip()


def _fix_title(title, url):
    """
    Titles from Presearch shows domain + title without spacing, and HTML
    This function removes these 2 issues.
    Transforming "translate.google.co.in<em>Google</em> Translate" into "Google Translate"
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    title = html_to_text(title)
    # Fixes issue where domain would show up in the title
    # translate.google.co.inGoogle Translate -> Google Translate
    if (
        title.startswith(domain)
        and len(title) > len(domain)
        and not title.startswith(domain + "/")
        and not title.startswith(domain + " ")
    ):
        title = title.removeprefix(domain)
    return title


def parse_search_query(json_results):
    results = []
    if not json_results:
        return results

    for item in json_results.get('specialSections', {}).get('topStoriesCompact', {}).get('data', []):
        result = {
            'url': item['link'],
            'title': _fix_title(item['title'], item['link']),
            'thumbnail': item['image'],
            'content': '',
            'metadata': item.get('source'),
        }
        results.append(result)

    for item in json_results.get('standardResults', []):
        result = {
            'url': item['link'],
            'title': _fix_title(item['title'], item['link']),
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
        results = parse_search_query(json_resp.get('results', {}))

    elif search_type == 'images':
        for item in json_resp.get('images', []):
            results.append(
                {
                    'template': 'images.html',
                    'title': html_to_text(item['title']),
                    'url': item.get('link'),
                    'img_src': item.get('image'),
                    'thumbnail_src': item.get('thumbnail'),
                }
            )

    elif search_type == 'videos':
        # The results in the video category are most often links to pages that contain
        # a video and not to a video stream --> Zhensa can't use the video template.

        for item in json_resp.get('videos', []):
            duration = item.get('duration')
            if duration:
                duration = parse_duration_string(duration)

            results.append(
                {
                    'title': html_to_text(item['title']),
                    'url': item.get('link'),
                    'content': item.get('description', ''),
                    'thumbnail': item.get('image'),
                    'length': duration,
                }
            )

    elif search_type == 'news':
        for item in json_resp.get('news', []):
            source = item.get('source')
            # Bug on their end, time sometimes returns "</a>"
            time = html_to_text(item.get('time')).strip()
            metadata = [source]
            if time != "":
                metadata.append(time)

            results.append(
                {
                    'title': html_to_text(item['title']),
                    'url': item.get('link'),
                    'content': html_to_text(item.get('description', '')),
                    'metadata': ' / '.join(metadata),
                    'thumbnail': item.get('image'),
                }
            )

    return results
