# SPDX-License-Identifier: AGPL-3.0-or-later
"""RottenTomatoes (movies)
"""

from urllib.parse import quote_plus
from lxml import html
from searx.utils import eval_xpath, eval_xpath_list, extract_text

# about
about = {
    "website": 'https://www.rottentomatoes.com/',
    "wikidata_id": 'Q105584',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}
categories = ['movies']

base_url = "https://www.rottentomatoes.com"

results_xpath = "//search-page-media-row"
url_xpath = "./a[1]/@href"
title_xpath = "./a/img/@alt"
img_src_xpath = "./a/img/@src"
release_year_xpath = "concat('From ', string(./@releaseyear))"
score_xpath = "concat('Score: ', string(./@tomatometerscore))"
cast_xpath = "concat('Starring ', string(./@cast))"


def request(query, params):
    params["url"] = f"{base_url}/search?search={quote_plus(query)}"
    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, results_xpath):
        content = []
        for xpath in (release_year_xpath, score_xpath, cast_xpath):
            info = extract_text(eval_xpath(result, xpath))

            # a gap in the end means that no data was found
            if info and info[-1] != " ":
                content.append(info)

        results.append(
            {
                'url': extract_text(eval_xpath(result, url_xpath)),
                'title': extract_text(eval_xpath(result, title_xpath)),
                'content': ', '.join(content),
                'img_src': extract_text(eval_xpath(result, img_src_xpath)),
            }
        )

    return results
