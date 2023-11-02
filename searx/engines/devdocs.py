# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Within this module we implement a devdocs.  Do not look to
close to the implementation, its just a simple example which queries `The Art
Institute of Chicago <https://www.artic.edu>`_

To get in use of this *demo* engine add the following entry to your engines
list in ``settings.yml``:

.. code:: yaml

  - name: DevDocs
    engine: devdocs
    shortcut: dev
    disabled: false

"""

from json import loads
from urllib.parse import urlencode

engine_type = 'online'
send_accept_language_header = True
categories = ['general']
disabled = True
timeout = 2.0
categories = ['images']
paging = True
page_size = 20

search_api = 'https://devdocs.io/#q='
image_api = ''

about = {
    "website": 'https://devdocs.io',
    # "wikidata_id": 'Q239303',
    "official_api_documentation": 'https://devdocs.io/help',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}


# if there is a need for globals, use a leading underline
_my_online_engine = None


def init(engine_settings):
    """Initialization of the (online) engine.  If no initialization is needed, drop
    this init function.

    """
    global _my_online_engine  # pylint: disable=global-statement
    _my_online_engine = engine_settings.get('name')


def request(query, params):
    """Build up the ``params`` for the online request.  In this example we build a
    URL to fetch images from `devdocs.io <https://devdocs.io>`__

    """
    # args = urlencode(
    #     {
    #         'q': query,
    #     }
    # )
    params['url'] = search_api + query
    return params


def response(resp):
    """Parse out the result items from the response.  In this we parse the
    response from `devdocs.io <https://devdocs.io>`__ 

    """
    results = []
    json_data = loads(resp.text)

    for result in json_data['data']:

        if not result['image_id']:
            continue

        results.append(
            {
                'url': 'https://artic.edu/artworks/%(id)s' % result,
                'title': result['title'] + " (%(date_display)s) //  %(artist_display)s" % result,
                'content': result['medium_display'],
                'author': ', '.join(result['artist_titles']),
                'img_src': image_api + '/%(image_id)s/full/843,/0/default.jpg' % result,
                'img_format': result['dimensions'],
                'template': 'images.html',
            }
        )

    return results
