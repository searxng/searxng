# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This is the implementation of the google news engine.  The google news API
ignores some parameters from the common :ref:`google API`:

- num_ : the number of search results is ignored
- save_ : is ignored / Google-News results are always *SafeSearch*

.. _num: https://developers.google.com/custom-search/docs/xml_results#numsp
.. _save: https://developers.google.com/custom-search/docs/xml_results#safesp

"""

# pylint: disable=invalid-name

import binascii
from datetime import datetime
import re
from urllib.parse import urlencode
from base64 import b64decode
from lxml import html

from searx.utils import (
    eval_xpath,
    eval_xpath_list,
    eval_xpath_getindex,
    extract_text,
)

# pylint: disable=unused-import
from searx.engines.google import (
    supported_languages_url,
    _fetch_supported_languages,
)

# pylint: enable=unused-import

from searx.engines.google import (
    get_lang_info,
    detect_google_sorry,
)

# about
about = {
    "website": 'https://news.google.com',
    "wikidata_id": 'Q12020',
    "official_api_documentation": 'https://developers.google.com/custom-search',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# compared to other google engines google-news has a different time range
# support.  The time range is included in the search term.
time_range_dict = {
    'day': 'when:1d',
    'week': 'when:7d',
    'month': 'when:1m',
    'year': 'when:1y',
}

# engine dependent config

categories = ['news']
paging = False
use_locale_domain = True
time_range_support = True

# Google-News results are always *SafeSearch*. Option 'safesearch' is set to
# False here, otherwise checker will report safesearch-errors::
#
#  safesearch : results are identitical for safesearch=0 and safesearch=2
safesearch = False


def request(query, params):
    """Google-News search request"""

    lang_info = get_lang_info(params, supported_languages, language_aliases, False)
    logger.debug("HTTP header Accept-Language --> %s", lang_info['headers']['Accept-Language'])

    # google news has only one domain
    lang_info['subdomain'] = 'news.google.com'

    ceid = "%s:%s" % (lang_info['country'], lang_info['language'])

    # google news redirects en to en-US
    if lang_info['params']['hl'] == 'en':
        lang_info['params']['hl'] = 'en-US'

    # Very special to google-news compared to other google engines, the time
    # range is included in the search term.
    if params['time_range']:
        query += ' ' + time_range_dict[params['time_range']]

    query_url = (
        'https://'
        + lang_info['subdomain']
        + '/search'
        + "?"
        + urlencode(
            {
                'q': query,
                **lang_info['params'],
                'ie': "utf8",
                'oe': "utf8",
                'gl': lang_info['country'],
            }
        )
        + ('&ceid=%s' % ceid)
    )  # ceid includes a ':' character which must not be urlencoded
    params['url'] = query_url

    params['headers'].update(lang_info['headers'])
    params['headers']['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    params['headers']['Cookie'] = "CONSENT=YES+cb.%s-14-p0.en+F+941;" % datetime.now().strftime("%Y%m%d")

    return params


def response(resp):
    """Get response from google's search request"""
    results = []

    detect_google_sorry(resp)

    # convert the text to dom
    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, '//div[@class="xrnccd"]'):

        # The first <a> tag in the <article> contains the link to the
        # article The href attribute of the <a> is a google internal link,
        # we can't use.  The real link is hidden in the jslog attribute:
        #
        #   <a ...
        #      jslog="95014; 4:https://www.cnn.com/.../index.html; track:click"
        #      href="./articles/CAIiENu3nGS...?hl=en-US&amp;gl=US&amp;ceid=US%3Aen"
        #      ... />

        jslog = eval_xpath_getindex(result, './article/a/@jslog', 0)
        url = re.findall('http[^;]*', jslog)
        if url:
            url = url[0]
        else:
            # The real URL is base64 encoded in the json attribute:
            # jslog="95014; 5:W251bGwsbnVsbCxudW...giXQ==; track:click"
            jslog = jslog.split(";")[1].split(':')[1].strip()
            try:
                padding = (4 - (len(jslog) % 4)) * "="
                jslog = b64decode(jslog + padding)
            except binascii.Error:
                # URL cant be read, skip this result
                continue

            # now we have : b'[null, ... null,"https://www.cnn.com/.../index.html"]'
            url = re.findall('http[^;"]*', str(jslog))[0]

        # the first <h3> tag in the <article> contains the title of the link
        title = extract_text(eval_xpath(result, './article/h3[1]'))

        # the first <div> tag in the <article> contains the content of the link
        content = extract_text(eval_xpath(result, './article/div[1]'))

        # the second <div> tag contains origin publisher and the publishing date

        pub_date = extract_text(eval_xpath(result, './article/div[2]//time'))
        pub_origin = extract_text(eval_xpath(result, './article/div[2]//a'))

        pub_info = []
        if pub_origin:
            pub_info.append(pub_origin)
        if pub_date:
            # The pub_date is mostly a string like 'yesertday', not a real
            # timezone date or time.  Therefore we can't use publishedDate.
            pub_info.append(pub_date)
        pub_info = ', '.join(pub_info)
        if pub_info:
            content = pub_info + ': ' + content

        # The image URL is located in a preceding sibling <img> tag, e.g.:
        # "https://lh3.googleusercontent.com/DjhQh7DMszk.....z=-p-h100-w100"
        # These URL are long but not personalized (double checked via tor).

        img_src = extract_text(result.xpath('preceding-sibling::a/figure/img/@src'))

        results.append(
            {
                'url': url,
                'title': title,
                'content': content,
                'img_src': img_src,
            }
        )

    # return results
    return results
