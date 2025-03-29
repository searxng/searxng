# SPDX-License-Identifier: AGPL-3.0-or-later
"""Engine for Il Post, a largely independent online Italian newspaper.

To use this engine add the following entry to your engines
list in ``settings.yml``:

.. code:: yaml

  - name: il post
    engine: il_post
    shortcut: pst
    disabled: false

"""

from json import loads
from urllib.parse import urlencode
from searx.result_types import EngineResults

engine_type = 'online'
language_support = False
categories = ['news']
paging = True
page_size = 10

time_range_support = True
time_range_args = {
    'month': 'pub_date:ultimi_30_giorni',
    'year': 'pub_date:ultimo_anno'
}

search_api = 'https://api.ilpost.org/search/api/site_search/?'

about = {
    "website": 'https://www.ilpost.it',
    "wikidata_id": 'Q3792882',
    "official_api_documentation": None,
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

def request(query, params):
    query_params = {
        'qs': query,
        'pg': params['pageno'],
        'sort': "date_d",
        'filters': 'ctype:articoli',
    }

    if params['time_range']:
        query_params['filters'] +=  f";{time_range_args.get(params['time_range'], 'pub_date:da_sempre')}"

    encoded_querystring = urlencode(query_params)


    params['url'] = search_api + encoded_querystring
    return params


def response(resp) -> EngineResults:
    res = EngineResults()
    json_data = loads(resp.text)

    for result in json_data['docs']:

        res.append(
            {
                'url': result['link'],
                'title': result['title'],
                'content': result['summary'] or None,
                'thumbnail': result['image'] or None,
            }
        )

    return res
