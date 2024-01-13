# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Presearch (general, images, videos, news)

.. hint::

   The results in the video category are most often links to pages that contain
   a video, for instance many links from preasearch's video category link
   content from facebook (aka Meta) or Twitter (aka X).  Since these are not
   real links to video streams SearXNG can't use the video template for this and
   if SearXNG can't use this template, then the user doesn't want to see these
   hits in the videos category.

   TL;DR; by default presearch's video category is placed into categories::

       categories: [general, web]

"""

from urllib.parse import urlencode
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
categories = ["general", "web"]  # general, images, videos, news

search_type = "search"
"""must be any of ``search``, ``images``, ``videos``, ``news``"""

base_url = "https://presearch.com"
safesearch_map = {0: 'false', 1: 'true', 2: 'true'}


def init(_):
    if search_type not in ['search', 'images', 'videos', 'news']:
        raise ValueError(f'presearch search_type: {search_type}')


def _get_request_id(query, page, time_range, safesearch_param):
    args = {
        "q": query,
        "page": page,
    }
    if time_range:
        args["time"] = time_range

    url = f"{base_url}/{search_type}?{urlencode(args)}"
    headers = {
        'User-Agent': gen_useragent(),
        'Cookie': f"b=1;presearch_session=;use_safe_search={safesearch_map[safesearch_param]}",
    }
    resp_text = get(url, headers=headers).text  # type: ignore

    for line in resp_text.split("\n"):
        if "window.searchId = " in line:
            return line.split("= ")[1][:-1].replace('"', "")

    return None


def request(query, params):
    request_id = _get_request_id(query, params["pageno"], params["time_range"], params["safesearch"])

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
            label, value = html_to_text(item).split(':', 1)
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
