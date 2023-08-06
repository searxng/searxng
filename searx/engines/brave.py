# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Brave supports the categories listed in :py:obj:`brave_category` (General,
news, videos, images).  The support of :py:obj:`paging` and :py:obj:`time range
<time_range_support>` is limited (see remarks).

Configured ``brave`` engines:

.. code:: yaml

  - name: brave
    engine: brave
    ...
    brave_category: search
    time_range_support: true
    paging: true

  - name: brave.images
    engine: brave
    ...
    brave_category: images

  - name: brave.videos
    engine: brave
    ...
    brave_category: videos

  - name: brave.news
    engine: brave
    ...
    brave_category: news


Implementations
===============

"""
# pylint: disable=fixme

from urllib.parse import (
    urlencode,
    urlparse,
    parse_qs,
)

import chompjs
from lxml import html

from searx.utils import (
    extract_text,
    eval_xpath_list,
    eval_xpath_getindex,
)

about = {
    "website": 'https://search.brave.com/',
    "wikidata_id": 'Q22906900',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

base_url = "https://search.brave.com/"
categories = []
brave_category = 'search'
"""Brave supports common web-search, video search, image and video search.

- ``search``: Common WEB search
- ``videos``: search for videos
- ``images``: search for images
- ``news``: search for news
"""

brave_spellcheck = False
"""Brave supports some kind of spell checking.  When activated, Brave tries to
fix typos, e.g. it searches for ``food`` when the user queries for ``fooh``.  In
the UI of Brave the user gets warned about this, since we can not warn the user
in SearXNG, the spellchecking is disabled by default.
"""

send_accept_language_header = True
paging = False
"""Brave only supports paging in :py:obj:`brave_category` ``search`` (UI
category All)."""

safesearch = True
safesearch_map = {2: 'strict', 1: 'moderate', 0: 'off'}  # cookie: safesearch=off

time_range_support = False
"""Brave only supports time-range in :py:obj:`brave_category` ``search`` (UI
category All)."""

time_range_map = {
    'day': 'pd',
    'week': 'pw',
    'month': 'pm',
    'year': 'py',
}


def request(query, params):

    # Don't accept br encoding / see https://github.com/searxng/searxng/pull/1787
    params['headers']['Accept-Encoding'] = 'gzip, deflate'

    args = {
        'q': query,
    }
    if brave_spellcheck:
        args['spellcheck'] = '1'

    if brave_category == 'search':
        if params.get('pageno', 1) - 1:
            args['offset'] = params.get('pageno', 1) - 1
        if time_range_map.get(params['time_range']):
            args['tf'] = time_range_map.get(params['time_range'])

    params["url"] = f"{base_url}{brave_category}?{urlencode(args)}"

    # set preferences in cookie
    params['cookies']['safesearch'] = safesearch_map.get(params['safesearch'], 'off')

    # ToDo: we need a fetch_traits(..) implementation / the ui_lang of Brave are
    #       limited and the country handling has it quirks

    eng_locale = params.get('searxng_locale')
    params['cookies']['useLocation'] = '0'  # the useLocation is IP based, we use 'country'
    params['cookies']['summarizer'] = '0'

    if not eng_locale or eng_locale == 'all':
        params['cookies']['country'] = 'all'  # country=all
    else:
        params['cookies']['country'] = eng_locale.split('-')[-1].lower()
        params['cookies']['ui_lang'] = eng_locale.split('-')[0].lower()

    # logger.debug("cookies %s", params['cookies'])


def response(resp):

    if brave_category == 'search':
        return _parse_search(resp)

    datastr = ""
    for line in resp.text.split("\n"):
        if "const data = " in line:
            datastr = line.replace("const data = ", "").strip()[:-1]
            break

    json_data = chompjs.parse_js_object(datastr)
    json_resp = json_data[1]['data']['body']['response']

    if brave_category == 'news':
        json_resp = json_resp['news']
        return _parse_news(json_resp)

    if brave_category == 'images':
        return _parse_images(json_resp)
    if brave_category == 'videos':
        return _parse_videos(json_resp)

    return []


def _parse_search(resp):

    result_list = []
    dom = html.fromstring(resp.text)

    answer_tag = eval_xpath_getindex(dom, '//div[@class="answer"]', 0, default=None)
    if answer_tag:
        result_list.append({'answer': extract_text(answer_tag)})

    # xpath_results = '//div[contains(@class, "snippet fdb") and @data-type="web"]'
    xpath_results = '//div[contains(@class, "snippet")]'

    for result in eval_xpath_list(dom, xpath_results):

        url = eval_xpath_getindex(result, './/a[@class="result-header"]/@href', 0, default=None)
        title_tag = eval_xpath_getindex(result, './/span[@class="snippet-title"]', 0, default=None)
        if not (url and title_tag):
            continue

        content_tag = eval_xpath_getindex(result, './/p[@class="snippet-description"]', 0, default='')
        img_src = eval_xpath_getindex(result, './/img[@class="thumb"]/@src', 0, default='')

        item = {
            'url': url,
            'title': extract_text(title_tag),
            'content': extract_text(content_tag),
            'img_src': img_src,
        }

        video_tag = eval_xpath_getindex(
            result, './/div[contains(@class, "video-snippet") and @data-macro="video"]', 0, default=None
        )
        if video_tag:

            # In my tests a video tag in the WEB search was mostoften not a
            # video, except the ones from youtube ..

            iframe_src = _get_iframe_src(url)
            if iframe_src:
                item['iframe_src'] = iframe_src
                item['template'] = 'videos.html'
                item['thumbnail'] = eval_xpath_getindex(video_tag, './/img/@src', 0, default='')
            else:
                item['img_src'] = eval_xpath_getindex(video_tag, './/img/@src', 0, default='')

        result_list.append(item)

    return result_list


def _get_iframe_src(url):
    parsed_url = urlparse(url)
    if parsed_url.path == '/watch' and parsed_url.query:
        video_id = parse_qs(parsed_url.query).get('v', [])  # type: ignore
        if video_id:
            return 'https://www.youtube-nocookie.com/embed/' + video_id[0]  # type: ignore
    return None


def _parse_news(json_resp):
    result_list = []

    for result in json_resp["results"]:
        item = {
            'url': result['url'],
            'title': result['title'],
            'content': result['description'],
        }
        if result['thumbnail'] != "null":
            item['img_src'] = result['thumbnail']['src']
        result_list.append(item)

    return result_list


def _parse_images(json_resp):
    result_list = []

    for result in json_resp["results"]:
        item = {
            'url': result['url'],
            'title': result['title'],
            'content': result['description'],
            'template': 'images.html',
            'img_format': result['properties']['format'],
            'source': result['source'],
            'img_src': result['properties']['url'],
        }
        result_list.append(item)

    return result_list


def _parse_videos(json_resp):
    result_list = []

    for result in json_resp["results"]:

        url = result['url']
        item = {
            'url': url,
            'title': result['title'],
            'content': result['description'],
            'template': 'videos.html',
            'length': result['video']['duration'],
            'duration': result['video']['duration'],
        }

        if result['thumbnail'] != "null":
            item['thumbnail'] = result['thumbnail']['src']

        iframe_src = _get_iframe_src(url)
        if iframe_src:
            item['iframe_src'] = iframe_src

        result_list.append(item)

    return result_list
