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

pdia_base_url = 'https://pdimagearchive.org'
pdia_config_start = "/_astro/InfiniteSearch."
pdia_config_end = ".js"
categories = ['images']
page_size = 20
paging = True


__CACHED_API_URL = None


def _clean_url(url):
    parsed = urlparse(url)
    query = [(k, v) for (k, v) in parse_qsl(parsed.query) if k not in ['ixid', 's']]

    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(query), parsed.fragment))


def _get_algolia_api_url():
    global __CACHED_API_URL  # pylint:disable=global-statement

    if __CACHED_API_URL:
        return __CACHED_API_URL

    # fake request to extract api url
    resp = get(f"{pdia_base_url}/search/?q=")
    if resp.status_code != 200:
        raise LookupError("Failed to fetch config location (and as such the API url) for PDImageArchive")
    pdia_config_filepart = extr(resp.text, pdia_config_start, pdia_config_end)
    pdia_config_url = pdia_base_url + pdia_config_start + pdia_config_filepart + pdia_config_end

    resp = get(pdia_config_url)
    if resp.status_code != 200:
        raise LookupError("Failed to obtain AWS api url for PDImageArchive")

    api_url = extr(resp.text, 'const r="', '"', default=None)

    if api_url is None:
        raise LookupError("Couldn't obtain AWS api url for PDImageArchive")

    __CACHED_API_URL = api_url
    return api_url


def _clear_cached_api_url():
    global __CACHED_API_URL  # pylint:disable=global-statement

    __CACHED_API_URL = None


def request(query, params):
    params['url'] = _get_algolia_api_url()
    params['method'] = 'POST'

    request_data = {
        'page': params['pageno'] - 1,
        'query': query,
        'hitsPerPage': page_size,
        'indexName': 'prod_all-images',
    }
    params['headers'] = {'Content-Type': 'application/json'}
    params['data'] = dumps(request_data)

    # http errors are handled manually to be able to reset the api url
    params['raise_for_httperror'] = False
    return params


def response(resp):
    results = []
    json_data = resp.json()

    if resp.status_code == 403:
        _clear_cached_api_url()
        raise SearxEngineAccessDeniedException()

    if resp.status_code != 200:
        raise SearxEngineException()

    if 'results' not in json_data:
        return []

    for result in json_data['results'][0]['hits']:
        content = []

        if result.get("themes"):
            content.append("Themes: " + result['themes'])

        if result.get("encompassingWork"):
            content.append("Encompassing work: " + result['encompassingWork'])

        base_image_url = result['thumbnail'].split("?")[0]

        results.append(
            {
                'template': 'images.html',
                'url': _clean_url(f"{about['website']}/images/{result['objectID']}"),
                'img_src': _clean_url(base_image_url),
                'thumbnail_src': _clean_url(base_image_url + THUMBNAIL_SUFFIX),
                'title': f"{result['title'].strip()} by {result['artist']} {result.get('displayYear', '')}",
                'content': "\n".join(content),
            }
        )

    return results
