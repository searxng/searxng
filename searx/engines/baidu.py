# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bing (Web)

- https://github.com/searx/searx/issues/2019#issuecomment-648227442
"""

import re
from urllib.parse import urlencode
from lxml import html
from searx.utils import eval_xpath, extract_text, eval_xpath_list, eval_xpath_getindex
from searx.network import raise_for_httperror, multi_requests, get, Request
from searx.exceptions import SearxEngineCaptchaException

about = {
    "website": 'https://www.baidu.com',
    "wikidata_id": 'Q14772',
    "official_api_documentation": 'https://apis.baidu.com/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
    "language": 'zn',
}

# engine dependent config
categories = ['general', 'web']
paging = False
time_range_support = False
safesearch = False

base_url = 'https://www.baidu.com/'
search_string = 's?{query}'

skip_tpls = ('img_normal', 'short_video', 'yl_music_song', 'dict3', 'recommend_list')

desc_xpath_per_tpl = {
    'se_com_default': './/span[contains(@class, "content-right_8Zs40")]',
    'kaifa_pc_open_source_software': './/p[contains(@class, "c-color-text")]',
    'bk_polysemy': './/div/@aria-label',
    'se_st_single_video_zhanzhang': './/span[contains(@class, "c-span-last")]//p[2]',
}


def get_initial_parameters(params):
    resp_index = get(base_url, headers=params['headers'], raise_for_httperror=True)
    dom = html.fromstring(resp_index.text)
    query_params = {}
    for ielement in eval_xpath_list(dom, '//form[@id="form"]//input[@name]'):
        name = ielement.attrib.get('name')
        value = ielement.attrib.get('value')
        query_params[name] = value
    return query_params, resp_index.cookies


def request(query, params):
    params['headers'].update(
        {
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Sec-GPC': '1',
            'Upgrade-Insecure-Requests': '1',
            'TE': 'trailers',
        }
    )

    query_params, cookies = get_initial_parameters(params)
    query_params['wd'] = query

    params['url'] = base_url + search_string.format(query=urlencode(query_params))
    params['cookies'] = cookies
    params['raise_for_httperror'] = False
    return params


def response(resp):
    results = []

    if resp.url.host == 'wappass.baidu.com' or resp.url.path.startswith('/static/captcha'):
        raise SearxEngineCaptchaException()
    raise_for_httperror(resp)

    dom = html.fromstring(resp.text)

    # follow redirect but don't use the result page to reduce the CAPTCHA issue
    redirect_element = eval_xpath_getindex(dom, '//noscript/meta[@http-equiv="refresh"]/@content', 0, default=None)
    if redirect_element and redirect_element.startswith('0; url='):
        get(
            base_url + redirect_element[8:],
            headers=resp.search_params['headers'],
            cookies=resp.search_params['cookies'],
        )

    for result in eval_xpath_list(dom, '//div[contains(@id,"content_left")]/div[contains(@class, "c-container")]'):
        tpl = result.attrib.get('tpl')
        if tpl in skip_tpls:
            continue

        if tpl == 'kaifa_pc_blog_weak':
            # skip the result to kaifa.baidu.com (search engine for IT)
            # but includes results from kaifa
            for r2 in eval_xpath_list(result, './/div[contains(@class, "c-gap-bottom-small")]'):
                title = extract_text(eval_xpath(r2, './/div[@class="c-row"]//a'))
                url = extract_text(eval_xpath(r2, './/div[@class="c-row"]//a/@href'))
                content = extract_text(eval_xpath(r2, '//span[@class="c-line-clamp2"]'))
                results.append(
                    {
                        'url': url,
                        'title': title,
                        'content': content,
                    }
                )
            continue

        # normal results
        title = extract_text(eval_xpath(result, './/h3/a'))
        url = extract_text(eval_xpath(result, './/h3/a/@href'))

        if not title or not url:
            continue

        content = None
        if tpl in desc_xpath_per_tpl:
            # try the XPath for the Baidu template
            content = extract_text(eval_xpath(result, desc_xpath_per_tpl[tpl]))
        if not content:
            # no content was found: try all the XPath from the Baidu templates
            for xp in desc_xpath_per_tpl.values():
                content = extract_text(eval_xpath(result, xp))
                if content:
                    break
        results.append(
            {
                'url': url,
                'title': title,
                'content': content,
            }
        )

    # resolve the Baidu redirections
    # note: Baidu does not support HTTP/2
    request_list = [
        Request.get(
            u['url'].replace('http://www.baidu.com/link?url=', 'https://www.baidu.com/link?url='),
            allow_redirects=False,
            headers=resp.search_params['headers'],
        )
        for u in results
    ]
    response_list = multi_requests(request_list)
    for i, redirect_response in enumerate(response_list):
        if not isinstance(redirect_response, Exception):
            results[i]['url'] = redirect_response.headers['location']

    return results


def debug_write_content_to_file(text):
    RE_STYLE_ELEMENT = re.compile(r'<style[^>]*>[^<]+</style>')
    RE_SCRIPT_ELEMENT = re.compile(r'<script[^>]*>[^<]+</script>')
    RE_COMMENT_ELEMENT = re.compile(r'\<\!\-\-[^-]+\-\-\>')
    with open('baidu.html', 'wt', encoding='utf-8') as f:
        text = RE_STYLE_ELEMENT.sub("", text)
        text = RE_SCRIPT_ELEMENT.sub("", text)
        text = RE_COMMENT_ELEMENT.sub("", text)
        text = "\n".join([ll.rstrip() for ll in text.splitlines() if ll.strip()])
        f.write(text)
