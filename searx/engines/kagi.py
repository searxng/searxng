# SPDX-License-Identifier: AGPL-3.0-or-later
"""Kagi Search
Scrapes Kagi's HTML search results.
"""

from urllib.parse import urlencode
from lxml import html

from searx.utils import extract_text, eval_xpath, eval_xpath_list
from searx.exceptions import SearxEngineAPIException
from searx import logger

logger = logger.getChild('kagi')

about = {
    "website": 'https://kagi.com',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": True,
    "results": 'HTML',
}

categories = ['general', 'web']
paging = True
time_range_support = False
safesearch = False

base_url = 'https://kagi.com/html/search'

api_key = None  # Set in settings.yml

# Global cookie storage for Kagi authentication
kagi_cookies = {'kagi_session': None, '_kagi_search_': None}


def request(query, params):
    if not api_key:
        raise SearxEngineAPIException('missing Kagi API key')

    page = params['pageno']

    if 'cookies' not in params:
        params['cookies'] = {}
    params['cookies'].update(kagi_cookies)

    if kagi_cookies['kagi_session'] and kagi_cookies['_kagi_search_']:
        logger.debug(
            "Using Kagi cookies for authentication - session: %s, search: %s",
            kagi_cookies['kagi_session'],
            kagi_cookies['_kagi_search_'],
        )
        search_url = base_url + '?' + urlencode({'q': query, 'batch': page})
    else:
        missing = []
        if not kagi_cookies['kagi_session']:
            missing.append('kagi_session')
        if not kagi_cookies['_kagi_search_']:
            missing.append('_kagi_search_')
        logger.debug("Missing cookies %s, using API key for initial authentication", missing)
        search_url = base_url + '?' + urlencode({'q': query, 'token': api_key, 'batch': page})

    params['url'] = search_url
    params['headers'].update(
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
        }
    )
    params['allow_redirects'] = True
    params['verify'] = True
    params['max_redirects'] = 1

    return params


def response(resp):
    results = []

    if 'set-cookie' in resp.headers:
        cookies = resp.headers.get_list('set-cookie')
        for cookie in cookies:
            try:
                cookie_parts = cookie.split('=', 1)
                if len(cookie_parts) != 2:
                    continue

                name = cookie_parts[0].strip()
                value = cookie_parts[1].split(';')[0].strip()

                if name == 'kagi_session':
                    if value != kagi_cookies['kagi_session']:
                        kagi_cookies['kagi_session'] = value
                        resp.search_params['cookies']['kagi_session'] = value
                        logger.debug("Updated kagi_session cookie: %s", value)
                elif name == '_kagi_search_':  # Exact match for search cookie
                    if value != kagi_cookies['_kagi_search_']:
                        kagi_cookies['_kagi_search_'] = value
                        resp.search_params['cookies']['_kagi_search_'] = value
                        logger.debug("Updated _kagi_search_ cookie: %s", value)
            except ValueError as e:
                logger.warning("Failed to parse Kagi cookie: %s", str(e))

        logger.debug(
            "Global Kagi cookies - session: %s, search: %s", kagi_cookies['kagi_session'], kagi_cookies['_kagi_search_']
        )
        logger.debug(
            "Request Kagi cookies - session: %s, search: %s",
            resp.search_params['cookies'].get('kagi_session'),
            resp.search_params['cookies'].get('_kagi_search_'),
        )

    if resp.status_code == 401:
        kagi_cookies['kagi_session'] = None
        kagi_cookies['_kagi_search_'] = None
        resp.search_params['cookies'].clear()
        logger.debug("Cleared invalid Kagi cookies")

        raise SearxEngineAPIException('Invalid Kagi authentication')
    if resp.status_code == 429:
        raise SearxEngineAPIException('Kagi rate limit exceeded')
    if resp.status_code != 200:
        raise SearxEngineAPIException(f'Unexpected HTTP status code: {resp.status_code}')

    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, '//div[contains(@class, "_0_SRI")]'):
        try:
            title_tag = eval_xpath(result, './/a[contains(@class, "__sri_title_link")]')[0]
            title = extract_text(title_tag)
            url = title_tag.get('href')
            content_tag = eval_xpath(result, './/div[contains(@class, "__sri-desc")]')
            content = extract_text(content_tag[0]) if content_tag else ''
            domain = eval_xpath(result, './/span[contains(@class, "host")]/text()')
            if domain:
                domain = domain[0]

            search_result = {'url': url, 'title': title, 'content': content, 'domain': domain}
            results.append(search_result)

        except (IndexError, KeyError):
            continue

    return results
