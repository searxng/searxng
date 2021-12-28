# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint

"""IMDB - Internet Movie Database

Retrieves results from a basic search.  Advanced search options are not
supported.  IMDB's API is undocumented, here are some posts about:

- https://stackoverflow.com/questions/1966503/does-imdb-provide-an-api
- https://rapidapi.com/blog/how-to-use-imdb-api/

An alternative that needs IMDPro_ is `IMDb and Box Office Mojo
<https://developer.imdb.com/documentation>`_

.. __IMDPro: https://pro.imdb.com/login

"""

import json

about = {
    "website": 'https://imdb.com/',
    "wikidata_id": 'Q37312',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = []
paging = False

# suggestion_url = "https://sg.media-imdb.com/suggestion/{letter}/{query}.json"
suggestion_url = "https://v2.sg.media-imdb.com/suggestion/{letter}/{query}.json"

href_base = 'https://imdb.com/{category}/{entry_id}'

search_categories = {"nm": "name", "tt": "title", "kw": "keyword", "co": "company", "ep": "episode"}


def request(query, params):

    query = query.replace(" ", "_").lower()
    params['url'] = suggestion_url.format(letter=query[0], query=query)

    return params


def response(resp):

    suggestions = json.loads(resp.text)
    results = []

    for entry in suggestions.get('d', []):

        # https://developer.imdb.com/documentation/key-concepts#imdb-ids
        entry_id = entry['id']
        categ = search_categories.get(entry_id[:2])
        if categ is None:
            logger.error('skip unknown category tag %s in %s', entry_id[:2], entry_id)
            continue

        title = entry['l']
        if 'q' in entry:
            title += " (%s)" % entry['q']

        content = ''
        if 'rank' in entry:
            content += "(%s) " % entry['rank']
        if 'y' in entry:
            content += str(entry['y']) + " - "
        if 's' in entry:
            content += entry['s']

        # imageUrl is the image itself, it is not a thumb!
        image_url = entry.get('i', {}).get('imageUrl')
        if image_url:
            # get thumbnail
            image_url_name, image_url_prefix = image_url.rsplit('.', 1)
            # recipe to get the magic value:
            #  * search on imdb.com, look at the URL of the thumbnail on the right side of the screen
            #  * search using the imdb engine, compare the imageUrl and thumbnail URL
            # QL75 : JPEG quality (?)
            # UX280 : resize to width 320
            # 280,414 : size of the image (add white border)
            magic = 'QL75_UX280_CR0,0,280,414_'
            if not image_url_name.endswith('_V1_'):
                magic = '_V1_' + magic
            image_url = image_url_name + magic + '.' + image_url_prefix
        results.append(
            {
                "title": title,
                "url": href_base.format(category=categ, entry_id=entry_id),
                "content": content,
                "img_src": image_url,
            }
        )

    return results
