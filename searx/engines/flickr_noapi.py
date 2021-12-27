# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Flickr (Images)
"""

from json import loads
from time import time
import re
from urllib.parse import urlencode
from searx.utils import ecma_unescape, html_to_text

# about
about = {
    "website": 'https://www.flickr.com',
    "wikidata_id": 'Q103204',
    "official_api_documentation": 'https://secure.flickr.com/services/api/flickr.photos.search.html',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['images']

url = 'https://www.flickr.com/'
search_url = url + 'search?{query}&page={page}'
time_range_url = '&min_upload_date={start}&max_upload_date={end}'
photo_url = 'https://www.flickr.com/photos/{userid}/{photoid}'
modelexport_re = re.compile(r"^\s*modelExport:\s*({.*}),$", re.M)
image_sizes = ('o', 'k', 'h', 'b', 'c', 'z', 'n', 'm', 't', 'q', 's')

paging = True
time_range_support = True
time_range_dict = {
    'day': 60 * 60 * 24,
    'week': 60 * 60 * 24 * 7,
    'month': 60 * 60 * 24 * 7 * 4,
    'year': 60 * 60 * 24 * 7 * 52,
}


def build_flickr_url(user_id, photo_id):
    return photo_url.format(userid=user_id, photoid=photo_id)


def _get_time_range_url(time_range):
    if time_range in time_range_dict:
        return time_range_url.format(start=time(), end=str(int(time()) - time_range_dict[time_range]))
    return ''


def request(query, params):
    params['url'] = search_url.format(query=urlencode({'text': query}), page=params['pageno']) + _get_time_range_url(
        params['time_range']
    )
    return params


def response(resp):
    results = []

    matches = modelexport_re.search(resp.text)

    if matches is None:
        return results

    match = matches.group(1)
    model_export = loads(match)

    if 'legend' not in model_export:
        return results

    legend = model_export['legend']

    # handle empty page
    if not legend or not legend[0]:
        return results

    for index in legend:
        photo = model_export['main'][index[0]][int(index[1])][index[2]][index[3]][int(index[4])]
        author = ecma_unescape(photo.get('realname', ''))
        source = ecma_unescape(photo.get('username', '')) + ' @ Flickr'
        title = ecma_unescape(photo.get('title', ''))
        content = html_to_text(ecma_unescape(photo.get('description', '')))
        img_src = None
        # From the biggest to the lowest format
        for image_size in image_sizes:
            if image_size in photo['sizes']:
                img_src = photo['sizes'][image_size]['url']
                img_format = (
                    'jpg ' + str(photo['sizes'][image_size]['width']) + 'x' + str(photo['sizes'][image_size]['height'])
                )
                break

        if not img_src:
            logger.debug('cannot find valid image size: {0}'.format(repr(photo)))
            continue

        # For a bigger thumbnail, keep only the url_z, not the url_n
        if 'n' in photo['sizes']:
            thumbnail_src = photo['sizes']['n']['url']
        elif 'z' in photo['sizes']:
            thumbnail_src = photo['sizes']['z']['url']
        else:
            thumbnail_src = img_src

        if 'ownerNsid' not in photo:
            # should not happen, disowned photo? Show it anyway
            url = img_src
        else:
            url = build_flickr_url(photo['ownerNsid'], photo['id'])

        result = {
            'url': url,
            'img_src': img_src,
            'thumbnail_src': thumbnail_src,
            'source': source,
            'img_format': img_format,
            'template': 'images.html',
        }
        result['author'] = author.encode(errors='ignore').decode()
        result['source'] = source.encode(errors='ignore').decode()
        result['title'] = title.encode(errors='ignore').decode()
        result['content'] = content.encode(errors='ignore').decode()
        results.append(result)

    return results
