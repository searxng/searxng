# SPDX-License-Identifier: AGPL-3.0-or-later
"""Public domain image archive, based on the unsplash engine

Meow meow

"""

from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl
from json import dumps

algolia_api_key = "153d2a10ce67a0be5484de130a132050"
"""Algolia API key. See engine documentation """

THUMBNAIL_SUFFIX = "?fit=max&h=360&w=360"
"""
Example thumbnail urls (from requests & html):
- https://the-public-domain-review.imgix.net
  /shop/nov-2023-prints-00043.jpg
  ?fit=max&h=360&w=360
- https://the-public-domain-review.imgix.net
  /collections/the-history-of-four-footed-beasts-and-serpents-1658/
  8616383182_5740fa7851_o.jpg
  ?fit=max&h=360&w=360

Example full image urls (from html)
- https://the-public-domain-review.imgix.net/shop/
  nov-2023-prints-00043.jpg
  ?fit=clip&w=970&h=800&auto=format,compress
- https://the-public-domain-review.imgix.net/collections/
  the-history-of-four-footed-beasts-and-serpents-1658/8616383182_5740fa7851_o.jpg
  ?fit=clip&w=310&h=800&auto=format,compress

The thumbnail url from the request will be cleaned for the full image link
The cleaned thumbnail url will have THUMBNAIL_SUFFIX added to them, based on the original thumbnail parameters
"""

# about
about = {
    "website": 'https://pdimagearchive.org',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

base_url = 'https://oqi2j6v4iz-dsn.algolia.net/'
search_url = base_url + f'1/indexes/*/queries?x-algolia-api-key={algolia_api_key}&x-algolia-application-id=OQI2J6V4IZ'
categories = ['images']
page_size = 20
paging = True


def clean_url(url):
    parsed = urlparse(url)
    query = [(k, v) for (k, v) in parse_qsl(parsed.query) if k not in ['ixid', 's']]

    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(query), parsed.fragment))


def request(query, params):
    params['url'] = search_url
    params["method"] = "POST"
    request_params = {
        "page": params["pageno"] - 1,
        "query": query,
        "highlightPostTag": "__ais-highlight__",
        "highlightPreTag": "__ais-highlight__",
    }
    data = {
        "requests": [
            {"indexName": "prod_all-images", "params": urlencode(request_params)},
        ]
    }
    params["data"] = dumps(data)
    logger.debug("query_url --> %s", params['url'])
    return params


def response(resp):
    results = []
    json_data = resp.json()

    if 'results' not in json_data:
        return []

    for result in json_data['results'][0]['hits']:
        content = []

        if "themes" in result:
            content.append("Themes: " + result['themes'])

        if "encompassingWork" in result:
            content.append("Encompassing work: " + result['encompassingWork'])
        content = "\n".join(content)

        base_image_url = result['thumbnail'].split("?")[0]

        results.append(
            {
                'template': 'images.html',
                'url': clean_url(f"{about['website']}/images/{result['objectID']}"),
                'img_src': clean_url(base_image_url),
                'thumbnail_src': clean_url(base_image_url + THUMBNAIL_SUFFIX),
                'title': f"{result['title'].strip()} by {result['artist']} {result.get('displayYear', '')}",
                'content': content,
            }
        )

    return results
