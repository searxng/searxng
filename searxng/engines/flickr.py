# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Flickr (Images)

 More info on api-key : https://www.flickr.com/services/apps/create/
"""

from json import loads
from urllib.parse import urlencode

# about
about = {
    "website": 'https://www.flickr.com',
    "wikidata_id": 'Q103204',
    "official_api_documentation": 'https://secure.flickr.com/services/api/flickr.photos.search.html',
    "use_official_api": True,
    "require_api_key": True,
    "results": 'JSON',
}

categories = ['images']

nb_per_page = 15
paging = True
api_key = None


url = 'https://api.flickr.com/services/rest/?method=flickr.photos.search' +\
      '&api_key={api_key}&{text}&sort=relevance' +\
      '&extras=description%2C+owner_name%2C+url_o%2C+url_n%2C+url_z' +\
      '&per_page={nb_per_page}&format=json&nojsoncallback=1&page={page}'
photo_url = 'https://www.flickr.com/photos/{userid}/{photoid}'

paging = True


def build_flickr_url(user_id, photo_id):
    return photo_url.format(userid=user_id, photoid=photo_id)


def request(query, params):
    params['url'] = url.format(text=urlencode({'text': query}),
                               api_key=api_key,
                               nb_per_page=nb_per_page,
                               page=params['pageno'])
    return params


def response(resp):
    results = []

    search_results = loads(resp.text)

    # return empty array if there are no results
    if 'photos' not in search_results:
        return []

    if 'photo' not in search_results['photos']:
        return []

    photos = search_results['photos']['photo']

    # parse results
    for photo in photos:
        if 'url_o' in photo:
            img_src = photo['url_o']
        elif 'url_z' in photo:
            img_src = photo['url_z']
        else:
            continue

# For a bigger thumbnail, keep only the url_z, not the url_n
        if 'url_n' in photo:
            thumbnail_src = photo['url_n']
        elif 'url_z' in photo:
            thumbnail_src = photo['url_z']
        else:
            thumbnail_src = img_src

        url = build_flickr_url(photo['owner'], photo['id'])

        # append result
        results.append({'url': url,
                        'title': photo['title'],
                        'img_src': img_src,
                        'thumbnail_src': thumbnail_src,
                        'content': photo['description']['_content'],
                        'author': photo['ownername'],
                        'template': 'images.html'})

    # return results
    return results
