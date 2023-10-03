# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Moviepilot is a German movie database, similar to IMDB or TMDB.  It doesn't
have any official API, but it uses JSON requests internally to fetch search
results and suggestions, that's being used in this implementation.

Moviepilot additionally allows to discover movies by certain categories
or filters, hence we provide the following syntax:

- Any normal search query -> Fetch search results by the query

- A query containing one of the category identifiers ``fsk``, ``genre``,
  ``jahr``, ``jahrzent``, ``land``, ``online``, ``stimmung`` will be used to
  search trending items by the provided filters, which are appended to the
  filter category after a ``-``.

Search examples:

- Normal: ``!mp Tom Cruise``
- By filter: ``!mp person-Ryan-Gosling``
- By filter: ``!mp fsk-0 land-deutschland genre-actionfilm``
- By filter: ``!mp jahrzehnt-2020er online-netflix``

For a list of all public filters, observe the url path when browsing

- https://www.moviepilot.de/filme/beste.

"""

from urllib.parse import urlencode
from searx.utils import html_to_text

about = {
    'website': "https://www.moviepilot.de",
    'official_api_documentation': None,
    'use_official_api': False,
    'require_api_key': False,
    'results': 'JSON',
    'language': 'de',
}
paging = True
categories = ["movies"]

base_url = "https://www.moviepilot.de"
image_url = "https://assets.cdn.moviepilot.de/files/{image_id}/fill/155/223/{filename}"

filter_types = ["fsk", "genre", "jahr", "jahrzehnt", "land", "online", "stimmung", "person"]


def request(query, params):
    query_parts = query.split(" ")

    discovery_filters = []
    for query_part in query_parts:
        filter_category_and_value = query_part.split("-", 1)

        if len(filter_category_and_value) < 2:
            continue

        filter_category = filter_category_and_value[0]

        if filter_category in filter_types:
            discovery_filters.append(query_part)

    params['discovery'] = len(discovery_filters) != 0

    if params['discovery']:
        args = {
            'page': params['pageno'],
            'order': 'beste',
        }
        params["url"] = f"{base_url}/api/discovery?{urlencode(args)}"
        for discovery_filter in discovery_filters:
            params["url"] += f"&filters[]={discovery_filter}"
    else:
        args = {
            'q': query,
            'page': params['pageno'],
            'type': 'suggest',
        }
        params["url"] = f"{base_url}/api/search?{urlencode(args)}"

    return params


def response(resp):
    results = []

    json = resp.json()

    json_results = []

    if resp.search_params['discovery']:
        json_results = json['results']
    else:
        json_results = json

    for result in json_results:
        item = {'title': result['title']}

        if resp.search_params['discovery']:
            content_list = [result.get(x) for x in ['abstract', 'summary']]
            item['url'] = base_url + result['path']
            item['content'] = html_to_text(' | '.join([x for x in content_list if x]))
            item['metadata'] = html_to_text(result.get('meta_short', ''))

            if result.get('image'):
                item['img_src'] = image_url.format(image_id=result['image'], filename=result['image_filename'])
        else:
            item['url'] = result['url']
            item['content'] = ', '.join([result['class'], result['info'], result['more']])
            item['img_src'] = result['image']

        results.append(item)

    return results
