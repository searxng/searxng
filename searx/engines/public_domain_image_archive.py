# SPDX-License-Identifier: AGPL-3.0-or-later
"""Public domain image archive"""

from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl
from json import dumps

from searx.network import get
from searx.utils import extr
from searx.exceptions import SearxEngineAccessDeniedException, SearxEngineException

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

base_url = 'https://oqi2j6v4iz-dsn.algolia.net'
pdia_base_url = 'https://pdimagearchive.org'
pdia_search_url = pdia_base_url + '/search/?q='
pdia_config_start = "/_astro/InfiniteSearch."
pdia_config_end = ".js"
categories = ['images']
page_size = 20
paging = True


__CACHED_API_KEY = None


def _clean_url(url):
    parsed = urlparse(url)
    query = [(k, v) for (k, v) in parse_qsl(parsed.query) if k not in ['ixid', 's']]

    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(query), parsed.fragment))


def _get_algolia_api_key():
    global __CACHED_API_KEY  # pylint:disable=global-statement

    if __CACHED_API_KEY:
        return __CACHED_API_KEY

    resp = get(pdia_search_url)
    if resp.status_code != 200:
        raise LookupError("Failed to fetch config location (and as such the API key) for PDImageArchive")
    pdia_config_filepart = extr(resp.text, pdia_config_start, pdia_config_end)
    pdia_config_url = pdia_base_url + pdia_config_start + pdia_config_filepart + pdia_config_end

    resp = get(pdia_config_url)
    if resp.status_code != 200:
        raise LookupError("Failed to obtain Algolia API key for PDImageArchive")

    api_key = extr(resp.text, 'const r="', '"', default=None)

    if api_key is None:
        raise LookupError("Couldn't obtain Algolia API key for PDImageArchive")

    __CACHED_API_KEY = api_key
    return api_key


def _clear_cached_api_key():
    global __CACHED_API_KEY  # pylint:disable=global-statement

    __CACHED_API_KEY = None


def request(query, params):
    api_key = _get_algolia_api_key()

    args = {
        'x-algolia-api-key': api_key,
        'x-algolia-application-id': 'OQI2J6V4IZ',
    }
    params['url'] = f"{base_url}/1/indexes/*/queries?{urlencode(args)}"
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

    # http errors are handled manually to be able to reset the api key
    params['raise_for_httperror'] = False
    return params


def response(resp):
    results = []
    json_data = resp.json()

    if resp.status_code == 403:
        _clear_cached_api_key()
        raise SearxEngineAccessDeniedException()

    if resp.status_code != 200:
        raise SearxEngineException()

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
                'url': _clean_url(f"{about['website']}/images/{result['objectID']}"),
                'img_src': _clean_url(base_image_url),
                'thumbnail_src': _clean_url(base_image_url + THUMBNAIL_SUFFIX),
                'title': f"{result['title'].strip()} by {result['artist']} {result.get('displayYear', '')}",
                'content': content,
            }
        )

    return results
