# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pexels (images)"""

import re

from urllib.parse import urlencode
from lxml import html

import cloudscraper

from searx.result_types import EngineResults
from searx.utils import eval_xpath_list
from searx.enginelib import EngineCache
from searx.exceptions import SearxEngineAPIException
from searx.network import get


# about
about = {
    "website": 'https://www.pexels.com',
    "wikidata_id": 'Q101240504',
    "official_api_documentation": 'https://www.pexels.com/api/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

base_url = 'https://www.pexels.com'
categories = ['images']
results_per_page = 20

paging = True
time_range_support = True
time_range_map = {'day': 'last_24_hours', 'week': 'last_week', 'month': 'last_month', 'year': 'last_year'}

SECRET_KEY_RE = re.compile('"secret-key":\b*"(.*?)"')
SECRET_KEY_DB_KEY = "secret-key"


CACHE: EngineCache
"""Cache to store the secret API key for the engine."""


def init(engine_settings):
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache(engine_settings["name"])


def _get_secret_key():
    scraper = cloudscraper.create_scraper()
    resp = scraper.get(base_url)
    if resp.status_code != 200:
        raise SearxEngineAPIException("failed to obtain secret key")

    doc = html.fromstring(resp.text)
    for script_src in eval_xpath_list(doc, "//script/@src"):
        script = get(script_src)
        if script.status_code != 200:
            raise SearxEngineAPIException("failed to obtain secret key")

        match = SECRET_KEY_RE.search(script.text)
        if match:
            return match.groups()[0]

    # all scripts checked, but secret key was not found
    raise SearxEngineAPIException("failed to obtain secret key")


def request(query, params):
    args = {
        'query': query,
        'page': params['pageno'],
        'per_page': results_per_page,
    }
    if params['time_range']:
        args['date_from'] = time_range_map[params['time_range']]

    params["url"] = f"{base_url}/en-us/api/v3/search/photos?{urlencode(args)}"

    # cache api key for future requests
    secret_key = CACHE.get(SECRET_KEY_DB_KEY)
    if not secret_key:
        secret_key = _get_secret_key()
        CACHE.set(SECRET_KEY_DB_KEY, secret_key)

    params["headers"]["secret-key"] = CACHE.get(SECRET_KEY_DB_KEY)

    return params


def response(resp):
    res = EngineResults()
    json_data = resp.json()

    for result in json_data.get('data', []):
        attrs = result["attributes"]
        res.add(
            res.types.LegacyResult(
                {
                    'template': 'images.html',
                    'url': f"{base_url}/photo/{attrs['slug']}-{attrs['id']}/",
                    'title': attrs["title"],
                    'content': attrs["description"],
                    'thumbnail_src': attrs["image"]["small"],
                    'img_src': attrs["image"]["download_link"],
                    'resolution': f"{attrs['width']}x{attrs['height']}",
                    'author': f"{attrs['user']['username']}",
                }
            )
        )

    return res
