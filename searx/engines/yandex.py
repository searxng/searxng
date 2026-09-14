# SPDX-License-Identifier: AGPL-3.0-or-later
"""Yandex (Web, images)"""

from json import loads
from urllib.parse import urlencode
from html import unescape
from lxml import html
from searx.exceptions import SearxEngineCaptchaException
from searx.utils import humanize_bytes, eval_xpath, eval_xpath_list, extract_text

# Engine metadata
about = {
    "website": 'https://yandex.com/',
    "wikidata_id": 'Q5281',
    "official_api_documentation": "?",
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# Engine configuration
categories = []
paging = True
enable_http3 = True
search_type = ""

# Search URL
base_url_web = 'https://yandex.com/search/site/'
base_url_images = 'https://yandex.com/images/search'

# Supported languages
yandex_supported_langs = [
    "ru",  # Russian
    "en",  # English
    "be",  # Belarusian
    "fr",  # French
    "de",  # German
    "id",  # Indonesian
    "kk",  # Kazakh
    "tt",  # Tatar
    "tr",  # Turkish
    "uk",  # Ukrainian
]

results_xpath = '//li[contains(@class, "serp-item")]'
url_xpath = './/a[@class="b-serp-item__title-link"]/@href'
title_xpath = './/h3[@class="b-serp-item__title"]/a[@class="b-serp-item__title-link"]/span'
content_xpath = './/div[@class="b-serp-item__content"]//div[@class="b-serp-item__text"]'


def catch_bad_response(resp):
    if resp.headers.get('x-yandex-captcha') == 'captcha':
        raise SearxEngineCaptchaException()


def extract_json_object(text, marker):
    """Return the first complete JSON object that starts with ``marker``.

    Yandex embeds a large JSON object in the HTML returned by image search.
    Looking for a hard-coded suffix is fragile because the same text can occur
    inside nested objects or JSON strings. This parser tracks braces while
    respecting quoted strings and escaped characters.
    """

    start = text.find(marker)
    if start == -1:
        raise ValueError(f'JSON marker not found: {marker}')

    depth = 0
    in_string = False
    escaped = False

    for index in range(start, len(text)):
        char = text[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    raise ValueError('Incomplete JSON object in Yandex response')


def request(query, params):
    query_params_web = {
        "tmpl_version": "releases",
        "text": query,
        "web": "1",
        "frame": "1",
        "searchid": "3131712",
    }

    lang = params["language"].split("-")[0]
    if lang in yandex_supported_langs:
        query_params_web["lang"] = lang

    query_params_images = {
        "text": query,
        "uinfo": "sw-1920-sh-1080-ww-1125-wh-999",
    }

    if params['pageno'] > 1:
        query_params_web.update({"p": params["pageno"] - 1})
        query_params_images.update({"p": params["pageno"] - 1})

    params["cookies"] = {'cookie': "yp=1716337604.sp.family%3A0#1685406411.szm.1:1920x1080:1920x999"}

    if search_type == 'web':
        params['url'] = f"{base_url_web}?{urlencode(query_params_web)}"
    elif search_type == 'images':
        params['url'] = f"{base_url_images}?{urlencode(query_params_images)}"

    return params


def response(resp):
    if search_type == 'web':
        catch_bad_response(resp)

        dom = html.fromstring(resp.text)

        results = []

        for result in eval_xpath_list(dom, results_xpath):
            results.append(
                {
                    'url': extract_text(eval_xpath(result, url_xpath)),
                    'title': extract_text(eval_xpath(result, title_xpath)),
                    'content': extract_text(eval_xpath(result, content_xpath)),
                }
            )

        return results

    if search_type == 'images':
        catch_bad_response(resp)

        html_data = html.fromstring(resp.text)
        html_sample = unescape(html.tostring(html_data, encoding='unicode'))

        json_data = extract_json_object(html_sample, '{"location":"/images/search/')
        json_resp = loads(json_data)

        results = []
        for _, item_data in json_resp['initialState']['serpList']['items']['entities'].items():
            title = item_data['snippet']['title']
            source = item_data['snippet']['url']

            image_source = item_data["viewerData"]["thumb"]
            for i in item_data['viewerData']['dups'] + item_data['viewerData']['preview']:
                if i["h"] > image_source["h"]:
                    image_source = i

            humanized_filesize = None
            if image_source.get("fileSizeInBytes"):
                humanized_filesize = humanize_bytes(image_source["fileSizeInBytes"])

            results.append(
                {
                    'title': title,
                    'url': source,
                    'img_src': image_source["url"],
                    'filesize': humanized_filesize,
                    'thumbnail_src': item_data["image"],
                    'template': 'images.html',
                    'resolution': f'{image_source["w"]} x {image_source["h"]}',
                }
            )

        return results

    return []
