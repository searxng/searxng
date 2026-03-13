# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bing-Images: description see :py:obj:`searx.engines.bing`."""

import json
from urllib.parse import urlencode

from lxml import html

from searx.engines.bing import (  # pylint: disable=unused-import
    fetch_traits,
    get_locale_params,
    override_accept_language,
)

# about
about = {
    "website": "https://www.bing.com/images",
    "wikidata_id": "Q182496",
    "official_api_documentation": "https://github.com/MicrosoftDocs/bing-docs",
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

# engine dependent config
categories = ["images", "web"]
paging = True
safesearch = True
time_range_support = True
time_map = {
    "day": 60 * 24,
    "week": 60 * 24 * 7,
    "month": 60 * 24 * 31,
    "year": 60 * 24 * 365,
}

base_url = "https://www.bing.com/images/async"
"""Bing-Image search URL"""


def request(query, params):
    """Assemble a Bing-Image request."""

    engine_region = traits.get_region(params["searxng_locale"], traits.all_locale)

    override_accept_language(params, engine_region)

    # build URL query
    # - example: https://www.bing.com/images/async?q=foo&async=1&first=1&count=35
    query_params = {
        "q": query,
        "async": "1",
        # to simplify the page count lets use the default of 35 images per page
        "first": (int(params.get("pageno", 1)) - 1) * 35 + 1,
        "count": 35,
    }

    locale_params = get_locale_params(engine_region)
    if locale_params:
        query_params.update(locale_params)

    # time range
    # - example: one year (525600 minutes) 'qft=filterui:age-lt525600'
    if params["time_range"]:
        query_params["qft"] = "filterui:age-lt%s" % time_map[params["time_range"]]

    params["url"] = base_url + "?" + urlencode(query_params)

    return params


def response(resp):
    """Get response from Bing-Image"""

    results = []

    dom = html.fromstring(resp.text)

    for result in dom.xpath('//ul[contains(@class, "dgControl_list")]/li'):
        metadata = result.xpath('.//a[@class="iusc"]/@m')
        if not metadata:
            continue

        metadata = json.loads(result.xpath('.//a[@class="iusc"]/@m')[0])
        title = " ".join(result.xpath('.//div[@class="infnmpt"]//a/text()')).strip()
        img_format = " ".join(result.xpath('.//div[@class="imgpt"]/div/span/text()')).strip().split(" · ")
        source = " ".join(result.xpath('.//div[@class="imgpt"]//div[@class="lnkw"]//a/text()')).strip()
        results.append(
            {
                "template": "images.html",
                "url": metadata["purl"],
                "thumbnail_src": metadata["turl"],
                "img_src": metadata["murl"],
                "content": metadata.get("desc"),
                "title": title,
                "source": source,
                "resolution": img_format[0],
                "img_format": img_format[1] if len(img_format) >= 2 else None,
            }
        )
    return results
