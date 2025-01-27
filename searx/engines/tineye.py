# SPDX-License-Identifier: AGPL-3.0-or-later
"""This engine implements *Tineye - reverse image search*

Using TinEye, you can search by image or perform what we call a reverse image
search.  You can do that by uploading an image or searching by URL. You can also
simply drag and drop your images to start your search.  TinEye constantly crawls
the web and adds images to its index.  Today, the TinEye index is over 50.2
billion images `[tineye.com] <https://tineye.com/how>`_.

.. hint::

   This SearXNG engine only supports *'searching by URL'* and it does not use
   the official API `[api.tineye.com] <https://api.tineye.com/python/docs/>`_.

"""

from typing import TYPE_CHECKING
from urllib.parse import urlencode
from datetime import datetime
from flask_babel import gettext

from searx.result_types import EngineResults

if TYPE_CHECKING:
    import logging

    logger = logging.getLogger()

about = {
    "website": 'https://tineye.com',
    "wikidata_id": 'Q2382535',
    "official_api_documentation": 'https://api.tineye.com/python/docs/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

engine_type = 'online_url_search'
""":py:obj:`searx.search.processors.online_url_search`"""

categories = ['general']
paging = True
safesearch = False
base_url = 'https://tineye.com'
search_string = '/api/v1/result_json/?page={page}&{query}'

FORMAT_NOT_SUPPORTED = gettext(
    "Could not read that image url. This may be due to an unsupported file"
    " format. TinEye only supports images that are JPEG, PNG, GIF, BMP, TIFF or WebP."
)
"""TinEye error message"""

NO_SIGNATURE_ERROR = gettext(
    "The image is too simple to find matches. TinEye requires a basic level of"
    " visual detail to successfully identify matches."
)
"""TinEye error message"""

DOWNLOAD_ERROR = gettext("The image could not be downloaded.")
"""TinEye error message"""


def request(query, params):
    """Build TinEye HTTP request using ``search_urls`` of a :py:obj:`engine_type`."""

    params['raise_for_httperror'] = False

    if params['search_urls']['data:image']:
        query = params['search_urls']['data:image']
    elif params['search_urls']['http']:
        query = params['search_urls']['http']

    logger.debug("query URL: %s", query)
    query = urlencode({'url': query})

    # see https://github.com/TinEye/pytineye/blob/main/pytineye/api.py
    params['url'] = base_url + search_string.format(query=query, page=params['pageno'])

    params['headers'].update(
        {
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, defalte, br',
            'Host': 'tineye.com',
            'DNT': '1',
            'TE': 'trailers',
        }
    )
    return params


def parse_tineye_match(match_json):
    """Takes parsed JSON from the API server and turns it into a :py:obj:`dict`
    object.

    Attributes `(class Match) <https://github.com/TinEye/pytineye/blob/main/pytineye/api.py>`__

    - `image_url`, link to the result image.
    - `domain`, domain this result was found on.
    - `score`, a number (0 to 100) that indicates how closely the images match.
    - `width`, image width in pixels.
    - `height`, image height in pixels.
    - `size`, image area in pixels.
    - `format`, image format.
    - `filesize`, image size in bytes.
    - `overlay`, overlay URL.
    - `tags`, whether this match belongs to a collection or stock domain.

    - `backlinks`, a list of Backlink objects pointing to the original websites
      and image URLs. List items are instances of :py:obj:`dict`, (`Backlink
      <https://github.com/TinEye/pytineye/blob/main/pytineye/api.py>`__):

      - `url`, the image URL to the image.
      - `backlink`, the original website URL.
      - `crawl_date`, the date the image was crawled.

    """

    # HINT: there exists an alternative backlink dict in the domains list / e.g.::
    #
    #     match_json['domains'][0]['backlinks']

    backlinks = []
    if "backlinks" in match_json:

        for backlink_json in match_json["backlinks"]:
            if not isinstance(backlink_json, dict):
                continue

            crawl_date = backlink_json.get("crawl_date")
            if crawl_date:
                crawl_date = datetime.strptime(crawl_date, '%Y-%m-%d')
            else:
                crawl_date = datetime.min

            backlinks.append(
                {
                    'url': backlink_json.get("url"),
                    'backlink': backlink_json.get("backlink"),
                    'crawl_date': crawl_date,
                    'image_name': backlink_json.get("image_name"),
                }
            )

    return {
        'image_url': match_json.get("image_url"),
        'domain': match_json.get("domain"),
        'score': match_json.get("score"),
        'width': match_json.get("width"),
        'height': match_json.get("height"),
        'size': match_json.get("size"),
        'image_format': match_json.get("format"),
        'filesize': match_json.get("filesize"),
        'overlay': match_json.get("overlay"),
        'tags': match_json.get("tags"),
        'backlinks': backlinks,
    }


def response(resp) -> EngineResults:
    """Parse HTTP response from TinEye."""
    results = EngineResults()

    # handle the 422 client side errors, and the possible 400 status code error
    if resp.status_code in (400, 422):
        json_data = resp.json()
        suggestions = json_data.get('suggestions', {})
        message = f'HTTP Status Code: {resp.status_code}'

        if resp.status_code == 422:
            s_key = suggestions.get('key', '')
            if s_key == "Invalid image URL":
                # test https://docs.searxng.org/_static/searxng-wordmark.svg
                message = FORMAT_NOT_SUPPORTED
            elif s_key == 'NO_SIGNATURE_ERROR':
                # test https://pngimg.com/uploads/dot/dot_PNG4.png
                message = NO_SIGNATURE_ERROR
            elif s_key == 'Download Error':
                # test https://notexists
                message = DOWNLOAD_ERROR
            else:
                logger.warning("Unknown suggestion key encountered: %s", s_key)
        else:  # 400
            description = suggestions.get('description')
            if isinstance(description, list):
                message = ','.join(description)

        # see https://github.com/searxng/searxng/pull/1456#issuecomment-1193105023
        # results.add(results.types.Answer(answer=message))
        logger.info(message)
        return results

    # Raise for all other responses
    resp.raise_for_status()

    json_data = resp.json()

    for match_json in json_data['matches']:

        tineye_match = parse_tineye_match(match_json)
        if not tineye_match['backlinks']:
            continue

        backlink = tineye_match['backlinks'][0]
        results.append(
            {
                'template': 'images.html',
                'url': backlink['backlink'],
                'thumbnail_src': tineye_match['image_url'],
                'source': backlink['url'],
                'title': backlink['image_name'],
                'img_src': backlink['url'],
                'format': tineye_match['image_format'],
                'width': tineye_match['width'],
                'height': tineye_match['height'],
                'publishedDate': backlink['crawl_date'],
            }
        )

    # append number of results

    number_of_results = json_data.get('num_matches')
    if number_of_results:
        results.append({'number_of_results': number_of_results})

    return results
