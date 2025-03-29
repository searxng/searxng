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

from urllib.parse import urlencode
from searx.result_types import EngineResults

engine_type = "online"
language_support = False
categories = ["news"]
paging = True
page_size = 10

time_range_support = True
time_range_args = {"month": "pub_date:ultimi_30_giorni", "year": "pub_date:ultimo_anno"}

search_api = "https://api.ilpost.org/search/api/site_search/?"

about = {
    "website": "https://www.ilpost.it",
    "wikidata_id": "Q3792882",
    "official_api_documentation": None,
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
    "language": "it",
}


def request(query, params):
    query_params = {
        "qs": query,
        "pg": params["pageno"],
        "sort": "date_d",
        "filters": "ctype:articoli",
    }

    if params["time_range"]:
        if params["time_range"] not in time_range_args:
            return None
        query_params["filters"] += f";{time_range_args.get(params['time_range'], 'pub_date:da_sempre')}"
    params["url"] = search_api + urlencode(query_params)
    return params


def response(resp) -> EngineResults:
    res = EngineResults()
    json_data = resp.json()

    for result in json_data["docs"]:
        res.add(
            res.types.MainResult(
                url=result["link"],
                title=result["title"],
                content=result.get("summary", ""),
                thumbnail=result.get("image"),
            )
        )

    return res
