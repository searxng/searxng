# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Qwant (Web, News, Images, Videos)

This engine uses the Qwant API (https://api.qwant.com/v3). The API is
undocumented but can be reverse engineered by reading the network log of
https://www.qwant.com/ queries.

This implementation is used by different qwant engines in the settings.yml::

  - name: qwant
    categories: general
    ...
  - name: qwant news
    categories: news
    ...
  - name: qwant images
    categories: images
    ...
  - name: qwant videos
    categories: videos
    ...

"""

from datetime import (
    datetime,
    timedelta,
)
from json import loads
from urllib.parse import urlencode
from flask_babel import gettext

from searx.utils import match_language
from searx.exceptions import SearxEngineAPIException
from searx.network import raise_for_httperror


# about
about = {
    "website": 'https://www.qwant.com/',
    "wikidata_id": 'Q14657870',
    "official_api_documentation": None,
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = []
paging = True
supported_languages_url = about['website']

category_to_keyword = {
    'general': 'web',
    'news': 'news',
    'images': 'images',
    'videos': 'videos',
}

# search-url
url = 'https://api.qwant.com/v3/search/{keyword}?{query}&count={count}&offset={offset}'


def request(query, params):
    """Qwant search request"""
    keyword = category_to_keyword[categories[0]]
    count = 10  # web: count must be equal to 10

    if keyword == 'images':
        count = 50
        offset = (params['pageno'] - 1) * count
        # count + offset must be lower than 250
        offset = min(offset, 199)
    else:
        offset = (params['pageno'] - 1) * count
        # count + offset must be lower than 50
        offset = min(offset, 40)

    params['url'] = url.format(
        keyword=keyword,
        query=urlencode({'q': query}),
        offset=offset,
        count=count,
    )

    # add language tag
    if params['language'] == 'all':
        params['url'] += '&locale=en_US'
    else:
        language = match_language(
            params['language'],
            supported_languages,
            language_aliases,
        )
        params['url'] += '&locale=' + language.replace('-', '_')

    params['raise_for_httperror'] = False
    return params


def response(resp):
    """Get response from Qwant's search request"""
    # pylint: disable=too-many-locals, too-many-branches, too-many-statements

    keyword = category_to_keyword[categories[0]]
    results = []

    # load JSON result
    search_results = loads(resp.text)
    data = search_results.get('data', {})

    # check for an API error
    if search_results.get('status') != 'success':
        msg = ",".join(
            data.get(
                'message',
                [
                    'unknown',
                ],
            )
        )
        raise SearxEngineAPIException('API error::' + msg)

    # raise for other errors
    raise_for_httperror(resp)

    if keyword == 'web':
        # The WEB query contains a list named 'mainline'.  This list can contain
        # different result types (e.g. mainline[0]['type'] returns type of the
        # result items in mainline[0]['items']
        mainline = data.get('result', {}).get('items', {}).get('mainline', {})
    else:
        # Queries on News, Images and Videos do not have a list named 'mainline'
        # in the response.  The result items are directly in the list
        # result['items'].
        mainline = data.get('result', {}).get('items', [])
        mainline = [
            {'type': keyword, 'items': mainline},
        ]

    # return empty array if there are no results
    if not mainline:
        return []

    for row in mainline:

        mainline_type = row.get('type', 'web')
        if mainline_type != keyword:
            continue

        if mainline_type == 'ads':
            # ignore adds
            continue

        mainline_items = row.get('items', [])
        for item in mainline_items:

            title = item.get('title', None)
            res_url = item.get('url', None)

            if mainline_type == 'web':
                content = item['desc']
                results.append(
                    {
                        'title': title,
                        'url': res_url,
                        'content': content,
                    }
                )

            elif mainline_type == 'news':

                pub_date = item['date']
                if pub_date is not None:
                    pub_date = datetime.fromtimestamp(pub_date)
                news_media = item.get('media', [])
                img_src = None
                if news_media:
                    img_src = news_media[0].get('pict', {}).get('url', None)
                results.append(
                    {
                        'title': title,
                        'url': res_url,
                        'publishedDate': pub_date,
                        'img_src': img_src,
                    }
                )

            elif mainline_type == 'images':
                thumbnail = item['thumbnail']
                img_src = item['media']
                results.append(
                    {
                        'title': title,
                        'url': res_url,
                        'template': 'images.html',
                        'thumbnail_src': thumbnail,
                        'img_src': img_src,
                    }
                )

            elif mainline_type == 'videos':
                # some videos do not have a description: while qwant-video
                # returns an empty string, such video from a qwant-web query
                # miss the 'desc' key.
                d, s, c = item.get('desc'), item.get('source'), item.get('channel')
                content_parts = []
                if d:
                    content_parts.append(d)
                if s:
                    content_parts.append("%s: %s " % (gettext("Source"), s))
                if c:
                    content_parts.append("%s: %s " % (gettext("Channel"), c))
                content = ' // '.join(content_parts)
                length = item['duration']
                if length is not None:
                    length = timedelta(milliseconds=length)
                pub_date = item['date']
                if pub_date is not None:
                    pub_date = datetime.fromtimestamp(pub_date)
                thumbnail = item['thumbnail']
                # from some locations (DE and others?) the s2 link do
                # response a 'Please wait ..' but does not deliver the thumbnail
                thumbnail = thumbnail.replace('https://s2.qwant.com', 'https://s1.qwant.com', 1)
                results.append(
                    {
                        'title': title,
                        'url': res_url,
                        'content': content,
                        'publishedDate': pub_date,
                        'thumbnail': thumbnail,
                        'template': 'videos.html',
                        'length': length,
                    }
                )

    return results


# get supported languages from their site
def _fetch_supported_languages(resp):
    # list of regions is embedded in page as a js object
    response_text = resp.text
    response_text = response_text[response_text.find('INITIAL_PROPS') :]
    response_text = response_text[response_text.find('{') : response_text.find('</script>')]

    regions_json = loads(response_text)

    supported_languages = []
    for country, langs in regions_json['locales'].items():
        for lang in langs['langs']:
            lang_code = "{lang}-{country}".format(lang=lang, country=country)
            supported_languages.append(lang_code)

    return supported_languages
