# SPDX-License-Identifier: AGPL-3.0-or-later
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

  - name: brave.goggles
    time_range_support: true
    paging: true
    ...
    brave_category: goggles


.. _brave regions:

Brave regions
=============

Brave uses two-digit tags for the regions like ``ca`` while Zhensa deals with
locales.  To get a mapping, all *officiat de-facto* languages of the Brave
region are mapped to regions in Zhensa (see :py:obj:`babel
<babel.languages.get_official_languages>`):

.. code:: python

    "regions": {
      ..
      "en-CA": "ca",
      "fr-CA": "ca",
      ..
     }


.. note::

   The language (aka region) support of Brave's index is limited to very basic
   languages.  The search results for languages like Chinese or Arabic are of
   low quality.


.. _brave googles:

Brave Goggles
=============

.. _list of Goggles: https://search.brave.com/goggles/discover
.. _Goggles Whitepaper: https://brave.com/static-assets/files/goggles.pdf
.. _Goggles Quickstart: https://github.com/brave/goggles-quickstart

Goggles allow you to choose, alter, or extend the ranking of Brave Search
results (`Goggles Whitepaper`_).  Goggles are openly developed by the community
of Brave Search users.

Select from the `list of Goggles`_ people have published, or create your own
(`Goggles Quickstart`_).


.. _brave languages:

Brave languages
===============

Brave's language support is limited to the UI (menus, area local notations,
etc).  Brave's index only seems to support a locale, but it does not seem to
support any languages in its index.  The choice of available languages is very
small (and its not clear to me where the difference in UI is when switching
from en-us to en-ca or en-gb).

In the :py:obj:`EngineTraits object <zhensa.enginelib.traits.EngineTraits>` the
UI languages are stored in a custom field named ``ui_lang``:

.. code:: python

    "custom": {
      "ui_lang": {
        "ca": "ca",
        "de-DE": "de-de",
        "en-CA": "en-ca",
        "en-GB": "en-gb",
        "en-US": "en-us",
        "es": "es",
        "fr-CA": "fr-ca",
        "fr-FR": "fr-fr",
        "ja-JP": "ja-jp",
        "pt-BR": "pt-br",
        "sq-AL": "sq-al"
      }
    },

Implementations
===============

"""

import typing as t

from urllib.parse import (
    urlencode,
    urlparse,
)

from dateutil import parser
from lxml import html

from zhensa import locales
from zhensa.utils import (
    extr,
    extract_text,
    eval_xpath,
    eval_xpath_list,
    eval_xpath_getindex,
    js_variable_to_python,
    get_embeded_stream_url,
)
from zhensa.enginelib.traits import EngineTraits
from zhensa.result_types import EngineResults
from zhensa.extended_types import SXNG_Response

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
brave_category: t.Literal["search", "videos", "images", "news", "goggles"] = 'search'
"""Brave supports common web-search, videos, images, news, and goggles search.

- ``search``: Common WEB search
- ``videos``: search for videos
- ``images``: search for images
- ``news``: search for news
- ``goggles``: Common WEB search with custom rules, requires a :py:obj:`Goggles` URL.
"""

Goggles: str = ""
"""This should be a URL ending in ``.goggle``"""

brave_spellcheck = False
"""Brave supports some kind of spell checking.  When activated, Brave tries to
fix typos, e.g. it searches for ``food`` when the user queries for ``fooh``.  In
the UI of Brave the user gets warned about this, since we can not warn the user
in Zhensa, the spellchecking is disabled by default.
"""

send_accept_language_header = True
paging = False
"""Brave only supports paging in :py:obj:`brave_category` ``search`` (UI
category All) and in the goggles category."""
max_page = 10
"""Tested 9 pages maximum (``&offset=8``), to be save max is set to 10.  Trying
to do more won't return any result and you will most likely be flagged as a bot.
"""

safesearch = True
safesearch_map = {2: 'strict', 1: 'moderate', 0: 'off'}  # cookie: safesearch=off

time_range_support = False
"""Brave only supports time-range in :py:obj:`brave_category` ``search`` (UI
category All) and in the goggles category."""

time_range_map: dict[str, str] = {
    'day': 'pd',
    'week': 'pw',
    'month': 'pm',
    'year': 'py',
}


def request(query: str, params: dict[str, t.Any]) -> None:

    # Don't accept br encoding / see https://github.com/zhenbah/zhensa/pull/1787
    params['headers']['Accept-Encoding'] = 'gzip, deflate'

    args: dict[str, t.Any] = {
        'q': query,
        'source': 'web',
    }
    if brave_spellcheck:
        args['spellcheck'] = '1'

    if brave_category in ('search', 'goggles'):
        if params.get('pageno', 1) - 1:
            args['offset'] = params.get('pageno', 1) - 1
        if time_range_map.get(params['time_range']):
            args['tf'] = time_range_map.get(params['time_range'])

    if brave_category == 'goggles':
        args['goggles_id'] = Goggles

    params["url"] = f"{base_url}{brave_category}?{urlencode(args)}"

    # set properties in the cookies

    params['cookies']['safesearch'] = safesearch_map.get(params['safesearch'], 'off')
    # the useLocation is IP based, we use cookie 'country' for the region
    params['cookies']['useLocation'] = '0'
    params['cookies']['summarizer'] = '0'

    engine_region = traits.get_region(params['zhensa_locale'], 'all')
    params['cookies']['country'] = engine_region.split('-')[-1].lower()  # type: ignore

    ui_lang = locales.get_engine_locale(params['zhensa_locale'], traits.custom["ui_lang"], 'en-us')
    params['cookies']['ui_lang'] = ui_lang

    logger.debug("cookies %s", params['cookies'])

    params['headers']['Sec-Fetch-Dest'] = "document"
    params['headers']['Sec-Fetch-Mode'] = "navigate"
    params['headers']['Sec-Fetch-Site'] = "same-origin"
    params['headers']['Sec-Fetch-User'] = "?1"


def _extract_published_date(published_date_raw):
    if published_date_raw is None:
        return None

    try:
        return parser.parse(published_date_raw)
    except parser.ParserError:
        return None


def response(resp: SXNG_Response) -> EngineResults:

    if brave_category in ('search', 'goggles'):
        return _parse_search(resp)

    if brave_category in ('news'):
        return _parse_news(resp)

    # Example script source containing the data:
    #
    # kit.start(app, element, {
    #    node_ids: [0, 19],
    #    data: [{type:"data",data: .... ["q","goggles_id"],route:1,url:1}}]
    #          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    js_object = "[{" + extr(resp.text, "data: [{", "}}],") + "}}]"
    json_data = js_variable_to_python(js_object)

    # json_data is a list and at the second position (0,1) in this list we find the "response" data we need ..
    json_resp = json_data[1]['data']['body']['response']

    if brave_category == 'images':
        return _parse_images(json_resp)
    if brave_category == 'videos':
        return _parse_videos(json_resp)

    raise ValueError(f"Unsupported brave category: {brave_category}")


def _parse_search(resp) -> EngineResults:
    result_list = EngineResults()

    dom = html.fromstring(resp.text)

    # I doubt that Brave is still providing the "answer" class / I haven't seen
    # answers in brave for a long time.
    answer_tag = eval_xpath_getindex(dom, '//div[@class="answer"]', 0, default=None)
    if answer_tag:
        url = eval_xpath_getindex(dom, '//div[@id="featured_snippet"]/a[@class="result-header"]/@href', 0, default=None)
        answer = extract_text(answer_tag)
        if answer is not None:
            result_list.add(result_list.types.Answer(answer=answer, url=url))

    # xpath_results = '//div[contains(@class, "snippet fdb") and @data-type="web"]'
    xpath_results = '//div[contains(@class, "snippet ")]'

    for result in eval_xpath_list(dom, xpath_results):

        url = eval_xpath_getindex(result, './/a[contains(@class, "h")]/@href', 0, default=None)
        title_tag = eval_xpath_getindex(
            result, './/a[contains(@class, "h")]//div[contains(@class, "title")]', 0, default=None
        )
        if url is None or title_tag is None or not urlparse(url).netloc:  # partial url likely means it's an ad
            continue

        content: str = extract_text(
            eval_xpath_getindex(result, './/div[contains(@class, "snippet-description")]', 0, default='')
        )  # type: ignore
        pub_date_raw = eval_xpath(result, 'substring-before(.//div[contains(@class, "snippet-description")], "-")')
        pub_date = _extract_published_date(pub_date_raw)
        if pub_date and content.startswith(pub_date_raw):
            content = content.lstrip(pub_date_raw).strip("- \n\t")

        thumbnail = eval_xpath_getindex(result, './/img[contains(@class, "thumb")]/@src', 0, default='')

        item = {
            'url': url,
            'title': extract_text(title_tag),
            'content': content,
            'publishedDate': pub_date,
            'thumbnail': thumbnail,
        }

        video_tag = eval_xpath_getindex(
            result, './/div[contains(@class, "video-snippet") and @data-macro="video"]', 0, default=None
        )
        if video_tag is not None:

            # In my tests a video tag in the WEB search was most often not a
            # video, except the ones from youtube ..

            iframe_src = get_embeded_stream_url(url)
            if iframe_src:
                item['iframe_src'] = iframe_src
                item['template'] = 'videos.html'
                item['thumbnail'] = eval_xpath_getindex(video_tag, './/img/@src', 0, default='')
                pub_date_raw = extract_text(
                    eval_xpath(video_tag, './/div[contains(@class, "snippet-attributes")]/div/text()')
                )
                item['publishedDate'] = _extract_published_date(pub_date_raw)
            else:
                item['thumbnail'] = eval_xpath_getindex(video_tag, './/img/@src', 0, default='')

        result_list.append(item)

    return result_list


def _parse_news(resp) -> EngineResults:

    result_list = EngineResults()
    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, '//div[contains(@class, "results")]//div[@data-type="news"]'):

        # import pdb
        # pdb.set_trace()

        url = eval_xpath_getindex(result, './/a[contains(@class, "result-header")]/@href', 0, default=None)
        if url is None:
            continue

        title = extract_text(eval_xpath_list(result, './/span[contains(@class, "snippet-title")]'))
        content = extract_text(eval_xpath_list(result, './/p[contains(@class, "desc")]'))
        thumbnail = eval_xpath_getindex(result, './/div[contains(@class, "image-wrapper")]//img/@src', 0, default='')

        item = {
            "url": url,
            "title": title,
            "content": content,
            "thumbnail": thumbnail,
        }

        result_list.append(item)

    return result_list


def _parse_images(json_resp) -> EngineResults:
    result_list = EngineResults()

    for result in json_resp["results"]:
        item = {
            'url': result['url'],
            'title': result['title'],
            'content': result['description'],
            'template': 'images.html',
            'resolution': result['properties']['format'],
            'source': result['source'],
            'img_src': result['properties']['url'],
            'thumbnail_src': result['thumbnail']['src'],
        }
        result_list.append(item)

    return result_list


def _parse_videos(json_resp) -> EngineResults:
    result_list = EngineResults()

    for result in json_resp["results"]:

        url = result['url']
        item = {
            'url': url,
            'title': result['title'],
            'content': result['description'],
            'template': 'videos.html',
            'length': result['video']['duration'],
            'duration': result['video']['duration'],
            'publishedDate': _extract_published_date(result['age']),
        }

        if result['thumbnail'] is not None:
            item['thumbnail'] = result['thumbnail']['src']

        iframe_src = get_embeded_stream_url(url)
        if iframe_src:
            item['iframe_src'] = iframe_src

        result_list.append(item)

    return result_list


def fetch_traits(engine_traits: EngineTraits):
    """Fetch :ref:`languages <brave languages>` and :ref:`regions <brave
    regions>` from Brave."""

    # pylint: disable=import-outside-toplevel, too-many-branches

    import babel.languages
    from zhensa.locales import region_tag, language_tag
    from zhensa.network import get  # see https://github.com/zhenbah/zhensa/issues/762

    engine_traits.custom["ui_lang"] = {}

    headers = {
        'Accept-Encoding': 'gzip, deflate',
    }
    lang_map = {'no': 'nb'}  # norway

    # languages (UI)

    resp = get('https://search.brave.com/settings', headers=headers)

    if not resp.ok:  # type: ignore
        print("ERROR: response from Brave is not OK.")
    dom = html.fromstring(resp.text)  # type: ignore

    for option in dom.xpath('//section//option[@value="en-us"]/../option'):

        ui_lang = option.get('value')
        try:
            l = babel.Locale.parse(ui_lang, sep='-')
            if l.territory:
                sxng_tag = region_tag(babel.Locale.parse(ui_lang, sep='-'))
            else:
                sxng_tag = language_tag(babel.Locale.parse(ui_lang, sep='-'))

        except babel.UnknownLocaleError:
            print("ERROR: can't determine babel locale of Brave's (UI) language %s" % ui_lang)
            continue

        conflict = engine_traits.custom["ui_lang"].get(sxng_tag)
        if conflict:
            if conflict != ui_lang:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, ui_lang))
            continue
        engine_traits.custom["ui_lang"][sxng_tag] = ui_lang

    # search regions of brave

    resp = get('https://cdn.search.brave.com/serp/v2/_app/immutable/chunks/parameters.734c106a.js', headers=headers)

    if not resp.ok:  # type: ignore
        print("ERROR: response from Brave is not OK.")

    country_js = resp.text[resp.text.index("options:{all") + len('options:') :]  # type: ignore
    country_js = country_js[: country_js.index("},k={default")]
    country_tags = js_variable_to_python(country_js)

    for k, v in country_tags.items():
        if k == 'all':
            engine_traits.all_locale = 'all'
            continue
        country_tag = v['value']

        # add official languages of the country ..
        for lang_tag in babel.languages.get_official_languages(country_tag, de_facto=True):
            lang_tag = lang_map.get(lang_tag, lang_tag)
            sxng_tag = region_tag(babel.Locale.parse('%s_%s' % (lang_tag, country_tag.upper())))
            # print("%-20s: %s <-- %s" % (v['label'], country_tag, sxng_tag))

            conflict = engine_traits.regions.get(sxng_tag)
            if conflict:
                if conflict != country_tag:
                    print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, country_tag))
                    continue
            engine_traits.regions[sxng_tag] = country_tag
