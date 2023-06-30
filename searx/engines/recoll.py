# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
""".. sidebar:: info

   - `Recoll <https://www.lesbonscomptes.com/recoll/>`_
   - `recoll-webui <https://framagit.org/medoc92/recollwebui.git>`_
   - :origin:`searx/engines/recoll.py`

Recoll_ is a desktop full-text search tool based on Xapian.  By itself Recoll_
does not offer WEB or API access, this can be achieved using recoll-webui_

Configuration
=============

You must configure the following settings:

``base_url``:
  Location where recoll-webui can be reached.

``mount_prefix``:
  Location where the file hierarchy is mounted on your *local* filesystem.

``dl_prefix``:
  Location where the file hierarchy as indexed by recoll can be reached.

``search_dir``:
  Part of the indexed file hierarchy to be search, if empty the full domain is
  searched.

Example
=======

Scenario:

#. Recoll indexes a local filesystem mounted in ``/export/documents/reference``,
#. the Recoll search interface can be reached at https://recoll.example.org/ and
#. the contents of this filesystem can be reached though https://download.example.org/reference

.. code:: yaml

   base_url: https://recoll.example.org/
   mount_prefix: /export/documents
   dl_prefix: https://download.example.org
   search_dir: ''

Implementations
===============

"""

from datetime import date, timedelta
from json import loads
from urllib.parse import urlencode, quote

# about
about = {
    "website": None,
    "wikidata_id": 'Q15735774',
    "official_api_documentation": 'https://www.lesbonscomptes.com/recoll/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
paging = True
time_range_support = True

# parameters from settings.yml
base_url = None
search_dir = ''
mount_prefix = None
dl_prefix = None

# embedded
embedded_url = '<{ttype} controls height="166px" ' + 'src="{url}" type="{mtype}"></{ttype}>'


# helper functions
def get_time_range(time_range):
    sw = {'day': 1, 'week': 7, 'month': 30, 'year': 365}  # pylint: disable=invalid-name

    offset = sw.get(time_range, 0)
    if not offset:
        return ''

    return (date.today() - timedelta(days=offset)).isoformat()


# do search-request
def request(query, params):
    search_after = get_time_range(params['time_range'])
    search_url = base_url + 'json?{query}&highlight=0'
    params['url'] = search_url.format(
        query=urlencode({'query': query, 'page': params['pageno'], 'after': search_after, 'dir': search_dir})
    )

    return params


# get response from search-request
def response(resp):
    results = []

    response_json = loads(resp.text)

    if not response_json:
        return []

    for result in response_json.get('results', []):
        title = result['label']
        url = result['url'].replace('file://' + mount_prefix, dl_prefix)
        content = '{}'.format(result['snippet'])

        # append result
        item = {'url': url, 'title': title, 'content': content, 'template': 'files.html'}

        if result['size']:
            item['size'] = int(result['size'])

        for parameter in ['filename', 'abstract', 'author', 'mtype', 'time']:
            if result[parameter]:
                item[parameter] = result[parameter]

        # facilitate preview support for known mime types
        if 'mtype' in result and '/' in result['mtype']:
            (mtype, subtype) = result['mtype'].split('/')
            item['mtype'] = mtype
            item['subtype'] = subtype

            if mtype in ['audio', 'video']:
                item['embedded'] = embedded_url.format(
                    ttype=mtype, url=quote(url.encode('utf8'), '/:'), mtype=result['mtype']
                )

            if mtype in ['image'] and subtype in ['bmp', 'gif', 'jpeg', 'png']:
                item['img_src'] = url

        results.append(item)

    if 'nres' in response_json:
        results.append({'number_of_results': response_json['nres']})

    return results
