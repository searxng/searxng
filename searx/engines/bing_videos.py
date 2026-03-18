# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bing-Videos: description see :py:obj:`searx.engines.bing`."""

import json
from urllib.parse import urlencode

from lxml import html

from searx.engines.bing import (  # pylint: disable=unused-import
    fetch_traits,
    get_locale_params,
    override_accept_language,
)
from searx.engines.bing_images import time_map
from searx.utils import eval_xpath, eval_xpath_getindex

about = {
    "website": "https://www.bing.com/videos",
    "wikidata_id": "Q4914152",
    "official_api_documentation": "https://github.com/MicrosoftDocs/bing-docs",
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

# engine dependent config
categories = ["videos", "web"]
paging = True
safesearch = True
time_range_support = True

base_url = "https://www.bing.com/videos/asyncv2"
"""Bing-Video search URL"""


def request(query, params):
    """Assemble a Bing-Video request."""

    engine_region = traits.get_region(params["searxng_locale"], traits.all_locale)

    override_accept_language(params, engine_region)

    # build URL query
    # - example: https://www.bing.com/videos/asyncv2?q=foo&async=content&first=1&count=35
    query_params = {
        "q": query,
        "async": "content",
        # to simplify the page count lets use the default of 35 videos per page
        "first": (int(params.get("pageno", 1)) - 1) * 35 + 1,
        "count": 35,
    }

    locale_params = get_locale_params(engine_region)
    if locale_params:
        query_params.update(locale_params)

    # time range
    # - example: one week (10080 minutes) '&qft= filterui:videoage-lt10080'  '&form=VRFLTR'
    if params["time_range"]:
        query_params["form"] = "VRFLTR"
        query_params["qft"] = " filterui:videoage-lt%s" % time_map[params["time_range"]]

    params["url"] = base_url + "?" + urlencode(query_params)

    return params


def response(resp):
    """Get response from Bing-Video"""

    results = []

    dom = html.fromstring(resp.text)

    for result in dom.xpath('//div[contains(@id, "mc_vtvc_video")]'):
        metadata = json.loads(eval_xpath_getindex(result, './/div[@class="vrhdata"]/@vrhm', index=0))
        info = " - ".join(eval_xpath(result, './/div[@class="mc_vtvc_meta_block"]//span/text()')).strip()
        thumbnail = eval_xpath_getindex(
            result,
            './/img[starts-with(@class, "rms")]/@data-src-hq',
            index=0,
            default=None,
        )

        results.append(
            {
                "url": metadata["murl"],
                "thumbnail": thumbnail,
                "title": metadata.get("vt", ""),
                "content": info,
                "length": metadata["du"],
                "template": "videos.html",
            }
        )

    return results
