# SPDX-License-Identifier: AGPL-3.0-or-later
"""Yandex (Web, images)"""

from json import loads
from urllib.parse import urlencode
from html import unescape
from lxml import html
from searx.exceptions import SearxEngineCaptchaException
from searx.utils import humanize_bytes, eval_xpath, eval_xpath_list, extract_text, extr


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
search_type = ""

# Search URL
base_url_web = 'https://yandex.com/search/site/'
base_url_images = 'https://yandex.com/images/search'

results_xpath = '//li[contains(@class, "serp-item")]'
url_xpath = './/a[@class="b-serp-item__title-link"]/@href'
title_xpath = './/h3[@class="b-serp-item__title"]/a[@class="b-serp-item__title-link"]/span'
content_xpath = './/div[@class="b-serp-item__content"]//div[@class="b-serp-item__text"]'


def catch_bad_response(resp):
    if resp.url.path.startswith('/showcaptcha'):
        raise SearxEngineCaptchaException()


def request(query, params):
    query_params_web = {
        "tmpl_version": "releases",
        "text": query,
        "web": "1",
        "frame": "1",
        "searchid": "3131712",
    }

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

        content_between_tags = extr(
            html_sample, '{"location":"/images/search/', 'advRsyaSearchColumn":null}}', default="fail"
        )
        json_data = '{"location":"/images/search/' + content_between_tags + 'advRsyaSearchColumn":null}}'

        if content_between_tags == "fail":
            content_between_tags = extr(html_sample, '{"location":"/images/search/', 'false}}}')
            json_data = '{"location":"/images/search/' + content_between_tags + 'false}}}'

        json_resp = loads(json_data)

        results = []
        for _, item_data in json_resp['initialState']['serpList']['items']['entities'].items():
            title = item_data['snippet']['title']
            source = item_data['snippet']['url']
            thumb = item_data['image']
            fullsize_image = item_data['viewerData']['dups'][0]['url']
            height = item_data['viewerData']['dups'][0]['h']
            width = item_data['viewerData']['dups'][0]['w']
            filesize = item_data['viewerData']['dups'][0]['fileSizeInBytes']
            humanized_filesize = humanize_bytes(filesize)

            results.append(
                {
                    'title': title,
                    'url': source,
                    'img_src': fullsize_image,
                    'filesize': humanized_filesize,
                    'thumbnail_src': thumb,
                    'template': 'images.html',
                    'resolution': f'{width} x {height}',
                }
            )

        return results

    return []
