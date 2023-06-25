# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Peertube and :py:obj:`SepiaSearch <searx.engines.sepiasearch>` do share
(more or less) the same REST API and the schema of the JSON result is identical.

"""

import re
from urllib.parse import urlencode
from datetime import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

import babel

from searx.network import get  # see https://github.com/searxng/searxng/issues/762
from searx.locales import language_tag
from searx.utils import html_to_text
from searx.enginelib.traits import EngineTraits

traits: EngineTraits

about = {
    # pylint: disable=line-too-long
    "website": 'https://joinpeertube.org',
    "wikidata_id": 'Q50938515',
    "official_api_documentation": 'https://docs.joinpeertube.org/api-rest-reference.html#tag/Search/operation/searchVideos',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ["videos"]
paging = True
base_url = "https://peer.tube"
"""Base URL of the Peertube instance.  A list of instances is available at:

- https://instances.joinpeertube.org/instances
"""

time_range_support = True
time_range_table = {
    'day': relativedelta(),
    'week': relativedelta(weeks=-1),
    'month': relativedelta(months=-1),
    'year': relativedelta(years=-1),
}

safesearch = True
safesearch_table = {0: 'both', 1: 'false', 2: 'false'}


def minute_to_hm(minute):
    if isinstance(minute, int):
        return "%d:%02d" % (divmod(minute, 60))
    return None


def request(query, params):
    """Assemble request for the Peertube API"""

    if not query:
        return False

    # eng_region = traits.get_region(params['searxng_locale'], 'en_US')
    eng_lang = traits.get_language(params['searxng_locale'], None)

    params['url'] = (
        base_url.rstrip("/")
        + "/api/v1/search/videos?"
        + urlencode(
            {
                'search': query,
                'searchTarget': 'search-index',  # Vidiversum
                'resultType': 'videos',
                'start': (params['pageno'] - 1) * 10,
                'count': 10,
                # -createdAt: sort by date ascending / createdAt: date descending
                'sort': '-match',  # sort by *match descending*
                'nsfw': safesearch_table[params['safesearch']],
            }
        )
    )

    if eng_lang is not None:
        params['url'] += '&languageOneOf[]=' + eng_lang
        params['url'] += '&boostLanguages[]=' + eng_lang

    if params['time_range'] in time_range_table:
        time = datetime.now().date() + time_range_table[params['time_range']]
        params['url'] += '&startDate=' + time.isoformat()

    return params


def response(resp):
    return video_response(resp)


def video_response(resp):
    """Parse video response from SepiaSearch and Peertube instances."""
    results = []

    json_data = resp.json()

    if 'data' not in json_data:
        return []

    for result in json_data['data']:
        metadata = [
            x
            for x in [
                result.get('channel', {}).get('displayName'),
                result.get('channel', {}).get('name') + '@' + result.get('channel', {}).get('host'),
                ', '.join(result.get('tags', [])),
            ]
            if x
        ]

        results.append(
            {
                'url': result['url'],
                'title': result['name'],
                'content': html_to_text(result.get('description') or ''),
                'author': result.get('account', {}).get('displayName'),
                'length': minute_to_hm(result.get('duration')),
                'template': 'videos.html',
                'publishedDate': parse(result['publishedAt']),
                'iframe_src': result.get('embedUrl'),
                'thumbnail': result.get('thumbnailUrl') or result.get('previewUrl'),
                'metadata': ' | '.join(metadata),
            }
        )

    return results


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages from peertube's search-index source code.

    See videoLanguages_ in commit `8ed5c729 - Refactor and redesign client`_

    .. _8ed5c729 - Refactor and redesign client:
       https://framagit.org/framasoft/peertube/search-index/-/commit/8ed5c729
    .. _videoLanguages:
       https://framagit.org/framasoft/peertube/search-index/-/commit/8ed5c729#3d8747f9a60695c367c70bb64efba8f403721fad_0_291
    """

    resp = get(
        'https://framagit.org/framasoft/peertube/search-index/-/raw/master/client/src/components/Filters.vue',
        # the response from search-index repository is very slow
        timeout=60,
    )

    if not resp.ok:  # type: ignore
        print("ERROR: response from peertube is not OK.")
        return

    js_lang = re.search(r"videoLanguages \(\)[^\n]+(.*?)\]", resp.text, re.DOTALL)  # type: ignore
    if not js_lang:
        print("ERROR: can't determine languages from peertube")
        return

    for lang in re.finditer(r"\{ id: '([a-z]+)', label:", js_lang.group(1)):
        eng_tag = lang.group(1)
        if eng_tag == 'oc':
            # Occitanis not known by babel, its closest relative is Catalan
            # but 'ca' is already in the list of engine_traits.languages -->
            # 'oc' will be ignored.
            continue
        try:
            sxng_tag = language_tag(babel.Locale.parse(eng_tag))
        except babel.UnknownLocaleError:
            print("ERROR: %s is unknown by babel" % eng_tag)
            continue

        conflict = engine_traits.languages.get(sxng_tag)
        if conflict:
            if conflict != eng_tag:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, eng_tag))
            continue
        engine_traits.languages[sxng_tag] = eng_tag

    engine_traits.languages['zh_Hans'] = 'zh'
    engine_traits.languages['zh_Hant'] = 'zh'
