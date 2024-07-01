# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Yandex (Web, images, videos)"""

import re
import sys
import json
import time
from urllib.parse import urlencode, urlparse, parse_qs
from lxml import html
from searx.utils import humanize_bytes
from html import unescape
from searx import logger
from searx import utils
from searx.exceptions import SearxEngineCaptchaException
from datetime import datetime

# about
about = {
    "website": 'https://yandex.com/',
    "wikidata_id": 'Q5281',
    "official_api_documentation": "?",
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['general', 'images', 'videos']
paging = True

# search-url
base_url_web = 'https://yandex.com/search/site/'
base_url_images = 'https://yandex.com/images/search'
base_url_videos = 'https://yandex.com/video/search'

url_extension = 'tmpl_version=releases%2Ffrontend%2Fvideo%2Fv1.1168.0%238d942de0f4ebc4eb6b8f3c24ffbd1f8dbc5bbe63'

url_xpath = "//a[@class='b-serp-item__title-link']/@href"
title_xpath = "//h3[@class='b-serp-item__title']/a[@class='b-serp-item__title-link']/span"
content_xpath = "//div[@class='b-serp-item__content']//div[@class='b-serp-item__text']"

images_request_block = '{"blocks":[{"block":"extra-content","params":{},"version":2},{"block":"i-global__params:ajax","params":{},"version":2},{"block":"search2:ajax","params":{},"version":2},{"block":"preview__isWallpaper","params":{},"version":2},{"block":"content_type_search","params":{},"version":2},{"block":"serp-controller","params":{},"version":2},{"block":"cookies_ajax","params":{},"version":2},{"block":"advanced-search-block","params":{},"version":2}],"metadata":{"bundles":{"lb":"AS?(E<X120"},"assets":{"las":"justifier-height=1;justifier-setheight=1;fitimages-height=1;justifier-fitincuts=1;react-with-dom=1;"},"extraContent":{"names":["i-react-ajax-adapter"]}}}'

videos_request_block = '{"blocks":[{"block":"extra-content","params":{},"version":2},{"block":"i-global__params:ajax","params":{},"version":2},{"block":"search2:ajax","params":{},"version":2},{"block":"vital-incut","params":{},"version":2},{"block":"content_type_search","params":{},"version":2},{"block":"serp-controller","params":{},"version":2},{"block":"cookies_ajax","params":{},"version":2}],"metadata":{"bundles":{"lb":"^G]!q<X120"},"assets":{"las":"react-with-dom=1;185.0=1;73.0=1;145.0=1;5a502a.0=1;32c342.0=1;b84ac8.0=1"},"extraContent":{"names":["i-react-ajax-adapter"]}}}'


def request(query, params):
    query_params_web = {
        "text": query,
        "web": "1",
        "frame": "1",
        "searchid": "3131712",
    }

    query_params_images = {
        "format": "json",
        "request": images_request_block,
        "text": query,
        "uinfo": "sw-1920-sh-1080-ww-1125-wh-999",
    }

    query_params_videos = {
        "format": "json",
        "request": videos_request_block,
        "text": query,
    }

    if params['pageno'] > 1:
        query_params_web.update({"p": params["pageno"] - 1, "lr": "21180"})
        query_params_images.update({"p": params["pageno"] - 1})
        query_params_videos.update({"p": params["pageno"] - 1})

    params['method'] = 'GET'
    params['headers']['accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
    params['headers']['accept-encoding'] = 'gzip'
    params['headers']['accept-language'] = 'en-US,en;q=0.5'
    params['headers']['dnt'] = '1'
    params['headers']['referer'] = 'https://yandex.com/images/search'
    params['headers']['connection'] = 'keep-alive'
    params['headers']['upgrade-insecure-requests'] = '1'
    params['headers']['sec-fetch-dest'] = 'document'
    params['headers']['sec-fetch-mode'] = 'navigate'
    params['headers']['sec-fetch-site'] = 'cross-site'
    params["cookies"] = {'cookie': "yp=1716337604.sp.family%3A1#1685406411.szm.1:1920x1080:1920x999"}

    if yandex_category == 'web':
        params['url'] = f"{base_url_web}?{urlencode(query_params_web)}"
    elif yandex_category == 'images':
        params['url'] = f"{base_url_images}?{url_extension}{urlencode(query_params_images)}"
    elif yandex_category == 'videos':
        params['url'] = f"{base_url_videos}?{url_extension}{urlencode(query_params_videos)}"

    return params


# get embedded youtube links
def _get_iframe_src(url):
    parsed_url = urlparse(url)
    if parsed_url.path == '/watch' and parsed_url.query:
        video_id = parse_qs(parsed_url.query).get('v', [])  # type: ignore
        if video_id:
            return 'https://www.youtube-nocookie.com/embed/' + video_id[0]  # type: ignore
    return None

def response(resp):
    if yandex_category == 'web':
        if (resp.url).path.startswith('/showcaptcha'):
            raise SearxEngineCaptchaException()

        dom = html.fromstring(resp.text)
        results_dom = dom.xpath('//li[contains(@class, "serp-item")]')

        results = []
        for result_dom in results_dom:
            urls = result_dom.xpath(url_xpath)
            titles = result_dom.xpath(title_xpath)
            contents = result_dom.xpath(content_xpath)

            title_texts = [title.xpath("normalize-space(.)") for title in titles]
            content_texts = [content.xpath("normalize-space(.)") for content in contents]

            for url, title_text, content_text in zip(urls, title_texts, content_texts):
                results.append({
                    "url": url,
                    "title": title_text,
                    "content": content_text,
                })

        return results

    elif yandex_category == 'images':
        if (resp.url).path.startswith('/showcaptcha'):
            raise SearxEngineCaptchaException()

        html_data = html.fromstring(resp.text)
        html_sample = unescape(html.tostring(html_data, encoding='unicode'))

        start_tag = '{"location":"/images/search/'
        end_tag = 'advRsyaSearchColumn":null}}'

        start_index = html_sample.find(start_tag)
        start_index = start_index if start_index != -1 else -1

        end_index = html_sample.find(end_tag, start_index)
        end_index = end_index + len(end_tag) if end_index != -1 else -1

        content_between_tags = html_sample[start_index:end_index] if start_index != -1 and end_index != -1 else None

#      # save to a file
#        with open('/path/to/output.txt', 'w') as f:
#         sys.stdout = f
#         print(selected_text)


        json_resp = utils.js_variable_to_python(content_between_tags)


        results = []
        for item_id, item_data in json_resp['initialState']['serpList']['items']['entities'].items():
            title = item_data['snippet']['title']
            source = item_data['snippet']['url']
            thumb = item_data['image']
#            fullsize_image = item_data['origUrl']
            fullsize_image = item_data['viewerData']['dups'][0]['url']
#            height = item_data['height']
#            width = item_data['width']
            height = item_data['viewerData']['dups'][0]['h']
            width = item_data['viewerData']['dups'][0]['w']
            filesize = item_data['viewerData']['dups'][0]['fileSizeInBytes']
            humanized_filesize = humanize_bytes(filesize)

            results.append({
                "title": title,
                "url": source,
                "img_src": fullsize_image,
                "filesize": humanized_filesize,
                "thumbnail_src": thumb,
                "template": "images.html",
                "resolution": f'{width} x {height}'
            })

        return results

    elif yandex_category == 'videos':
        if (resp.url).path.startswith('/showcaptcha'):
            raise SearxEngineCaptchaException()

        html_data = html.fromstring(resp.text)
        html_sample = unescape(html.tostring(html_data, encoding='unicode'))

        start_tag = '{"pages":{"search":{"query":'
        end_tag = '}}</noframes>'

        start_index = html_sample.find(start_tag)
        start_index = start_index if start_index != -1 else -1

        end_index = html_sample.find(end_tag, start_index)
        end_index = end_index + len(end_tag) if end_index != -1 else -1

        content_between_tags = html_sample[start_index:end_index] if start_index != -1 and end_index != -1 else None

        json_resp = r'''{}'''.format(content_between_tags.rsplit('</noframes>', 1)[0])

#      # save to a file
#        with open('/home/user/Desktop/json_resp.txt', 'w') as f:
#         sys.stdout = f
#         print(json_resp)

        #sometimes json_resp is valid json, sometimes not.
        #but we can (ussually) validate the json by removing the values in the clear_description and clear_title keys.
        #we don't need them and they may contain unescaped characters that make the decoding fail. so for now...

        # Step 1: Remove everything between "clear_description":" and ","
        pattern_desc = r'("clear_description":")(.*?)(",")'
        json_resp = re.sub(pattern_desc, r'\1\3', json_resp)
        # Step 2: Remove everything between "clear_title":" and ","
        pattern_title = r'("clear_title":")(.*?)(",")'
        json_resp = re.sub(pattern_title, r'\1\3', json_resp)

        #to do: when the search query is butterfly, yandex videos page 2 is broken


      # save to a file
#        with open('/home/user/Desktop/json_resp.txt', 'w') as f:
#         sys.stdout = f
#         print(json_resp)


        json_resp2 = json.loads(json_resp.encode("UTF-8"))
#        json_resp2 = json.loads(json_resp)


      # save to a file
#        with open('/home/user/Desktop/json_resp2.txt', 'w') as f:
#         sys.stdout = f
#         print(json_resp2)


        results = []

        for snippet_key in json_resp2['pages']['search']['viewerData']['organicSnippets']:
         for item in json_resp2['pages']['search']['viewerData']['organicSnippets'][snippet_key]:
          if 'title' in item:
             title = item['title']['text']
             url = item['url']
             description = item['description']
             thumbnail = item['thumb']['image']
             length = item['thumb']['duration']
             channel = item['channel']['name']
             release_time = item['time']
             release_date = datetime.strptime(release_time.split("T")[0], "%Y-%m-%d")
             formatted_date = datetime.utcfromtimestamp(release_date.timestamp())

             results.append({
                "title": title,
                "url": url,
                "author": channel,
                "publishedDate": formatted_date,
                "length": length,
                "content": description,
                "thumbnail": thumbnail,
                "iframe_src": _get_iframe_src(url),
                "template": "videos.html",
            })

    return results
