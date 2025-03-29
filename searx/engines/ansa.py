# SPDX-License-Identifier: AGPL-3.0-or-later
"""Engine for Ansa, Italy's oldest news agency.

To use this engine add the following entry to your engines
list in ``settings.yml``:

.. code:: yaml

  - name: ansa
    engine: ansa
    shortcut: ans
    disabled: false

"""

from urllib.parse import urlencode
from lxml import html
from searx.result_types import EngineResults, MainResult
from searx.utils import eval_xpath, eval_xpath_list, extract_text

engine_type = 'online'
language_support = False
categories = ['news']
paging = True
page_size = 12
base_url = 'https://www.ansa.it'

time_range_support = True
time_range_args = {
    'day': 1,
    'week': 7,
    'month': 31,
    'year': 365,
}
# https://www.ansa.it/ricerca/ansait/search.shtml?start=0&any=houthi&periodo=&sort=data%3Adesc
search_api = 'https://www.ansa.it/ricerca/ansait/search.shtml?'

about = {
    'website': 'https://www.ansa.it',
    'wikidata_id': 'Q392934',
    'official_api_documentation': None,
    'use_official_api': False,
    'require_api_key': False,
    'results': 'HTML',
    'language': 'it',
}


def request(query, params):
    query_params = {
        'any': query,
        'start': (params['pageno'] - 1) * page_size,
        'sort': "data:desc",
    }

    if params['time_range']:
        query_params['periodo'] = time_range_args.get(params['time_range'])

    params['url'] = search_api + urlencode(query_params)
    return params


def response(resp) -> EngineResults:
    res = EngineResults()
    doc = html.fromstring(resp.text)

    for result in eval_xpath_list(doc, "//div[@class='article']"):

        res_obj = MainResult(
            title=extract_text(eval_xpath(result, "./div[@class='content']/h2[@class='title']/a")),
            content=extract_text(eval_xpath(result, "./div[@class='content']/div[@class='text']")),
            url=base_url + extract_text(eval_xpath(result, "./div[@class='content']/h2[@class='title']/a/@href")),
        )

        thumbnail = extract_text(eval_xpath(result, "./div[@class='image']/a/img/@src"))
        if thumbnail:
            res_obj.thumbnail = base_url + thumbnail

        res.append(res_obj)

    return res
