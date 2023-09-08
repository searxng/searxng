# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Deviantart (Images)

"""

import urllib.parse
from lxml import html

from searx.utils import extract_text, eval_xpath, eval_xpath_list

# about
about = {
    "website": 'https://www.deviantart.com/',
    "wikidata_id": 'Q46523',
    "official_api_documentation": 'https://www.deviantart.com/developers/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['images']
paging = True

# search-url
base_url = 'https://www.deviantart.com'

results_xpath = '//div[@class="_2pZkk"]/div/div/a'
url_xpath = './@href'
thumbnail_src_xpath = './div/img/@src'
img_src_xpath = './div/img/@srcset'
title_xpath = './@aria-label'
premium_xpath = '../div/div/div/text()'
premium_keytext = 'Watch the artist to view this deviation'
cursor_xpath = '(//a[@class="_1OGeq"]/@href)[last()]'


def request(query, params):

    # https://www.deviantart.com/search?q=foo

    nextpage_url = params['engine_data'].get('nextpage')
    # don't use nextpage when user selected to jump back to page 1
    if params['pageno'] > 1 and nextpage_url is not None:
        params['url'] = nextpage_url
    else:
        params['url'] = f"{base_url}/search?{urllib.parse.urlencode({'q': query})}"

    return params


def response(resp):

    results = []
    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, results_xpath):
        # skip images that are blurred
        _text = extract_text(eval_xpath(result, premium_xpath))
        if _text and premium_keytext in _text:
            continue
        img_src = extract_text(eval_xpath(result, img_src_xpath))
        if img_src:
            img_src = img_src.split(' ')[0]
            parsed_url = urllib.parse.urlparse(img_src)
            img_src = parsed_url._replace(path=parsed_url.path.split('/v1')[0]).geturl()

        results.append(
            {
                'template': 'images.html',
                'url': extract_text(eval_xpath(result, url_xpath)),
                'img_src': img_src,
                'thumbnail_src': extract_text(eval_xpath(result, thumbnail_src_xpath)),
                'title': extract_text(eval_xpath(result, title_xpath)),
            }
        )

    nextpage_url = extract_text(eval_xpath(dom, cursor_xpath))
    if nextpage_url:
        results.append(
            {
                'engine_data': nextpage_url.replace("http://", "https://"),
                'key': 'nextpage',
            }
        )

    return results
