# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Google (Scholar)

For detailed description of the *REST-full* API see: `Query Parameter
Definitions`_.

.. _Query Parameter Definitions:
   https://developers.google.com/custom-search/docs/xml_results#WebSearch_Query_Parameter_Definitions
"""

# pylint: disable=invalid-name

from urllib.parse import urlencode
from datetime import datetime
from typing import Optional
from lxml import html

from searx.utils import (
    eval_xpath,
    eval_xpath_getindex,
    eval_xpath_list,
    extract_text,
)

from searx.engines.google import (
    get_lang_info,
    time_range_dict,
    detect_google_sorry,
)

# pylint: disable=unused-import
from searx.engines.google import (
    supported_languages_url,
    _fetch_supported_languages,
)

# pylint: enable=unused-import

# about
about = {
    "website": 'https://scholar.google.com',
    "wikidata_id": 'Q494817',
    "official_api_documentation": 'https://developers.google.com/custom-search',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['science', 'scientific publications']
paging = True
language_support = True
use_locale_domain = True
time_range_support = True
safesearch = False
send_accept_language_header = True


def time_range_url(params):
    """Returns a URL query component for a google-Scholar time range based on
    ``params['time_range']``.  Google-Scholar does only support ranges in years.
    To have any effect, all the Searx ranges (*day*, *week*, *month*, *year*)
    are mapped to *year*.  If no range is set, an empty string is returned.
    Example::

        &as_ylo=2019
    """
    # as_ylo=2016&as_yhi=2019
    ret_val = ''
    if params['time_range'] in time_range_dict:
        ret_val = urlencode({'as_ylo': datetime.now().year - 1})
    return '&' + ret_val


def request(query, params):
    """Google-Scholar search request"""

    offset = (params['pageno'] - 1) * 10
    lang_info = get_lang_info(params, supported_languages, language_aliases, False)

    # subdomain is: scholar.google.xy
    lang_info['subdomain'] = lang_info['subdomain'].replace("www.", "scholar.")

    query_url = (
        'https://'
        + lang_info['subdomain']
        + '/scholar'
        + "?"
        + urlencode({'q': query, **lang_info['params'], 'ie': "utf8", 'oe': "utf8", 'start': offset})
    )

    query_url += time_range_url(params)
    params['url'] = query_url

    params['cookies']['CONSENT'] = "YES+"
    params['headers'].update(lang_info['headers'])
    params['headers']['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'

    # params['google_subdomain'] = subdomain
    return params


def parse_gs_a(text: Optional[str]):
    """Parse the text written in green.

    Possible formats:
    * "{authors} - {journal}, {year} - {publisher}"
    * "{authors} - {year} - {publisher}"
    * "{authors} - {publisher}"
    """
    if text is None or text == "":
        return None, None, None, None

    s_text = text.split(' - ')
    authors = s_text[0].split(', ')
    publisher = s_text[-1]
    if len(s_text) != 3:
        return authors, None, publisher, None

    # the format is "{authors} - {journal}, {year} - {publisher}" or "{authors} - {year} - {publisher}"
    # get journal and year
    journal_year = s_text[1].split(', ')
    # journal is optional and may contains some coma
    if len(journal_year) > 1:
        journal = ', '.join(journal_year[0:-1])
        if journal == '…':
            journal = None
    else:
        journal = None
    # year
    year = journal_year[-1]
    try:
        publishedDate = datetime.strptime(year.strip(), '%Y')
    except ValueError:
        publishedDate = None
    return authors, journal, publisher, publishedDate


def response(resp):  # pylint: disable=too-many-locals
    """Get response from google's search request"""
    results = []

    detect_google_sorry(resp)

    # which subdomain ?
    # subdomain = resp.search_params.get('google_subdomain')

    # convert the text to dom
    dom = html.fromstring(resp.text)

    # parse results
    for result in eval_xpath_list(dom, '//div[@data-cid]'):

        title = extract_text(eval_xpath(result, './/h3[1]//a'))

        if not title:
            # this is a [ZITATION] block
            continue

        pub_type = extract_text(eval_xpath(result, './/span[@class="gs_ct1"]'))
        if pub_type:
            pub_type = pub_type[1:-1].lower()

        url = eval_xpath_getindex(result, './/h3[1]//a/@href', 0)
        content = extract_text(eval_xpath(result, './/div[@class="gs_rs"]'))
        authors, journal, publisher, publishedDate = parse_gs_a(
            extract_text(eval_xpath(result, './/div[@class="gs_a"]'))
        )
        if publisher in url:
            publisher = None

        # cited by
        comments = extract_text(eval_xpath(result, './/div[@class="gs_fl"]/a[starts-with(@href,"/scholar?cites=")]'))

        # link to the html or pdf document
        html_url = None
        pdf_url = None
        doc_url = eval_xpath_getindex(result, './/div[@class="gs_or_ggsm"]/a/@href', 0, default=None)
        doc_type = extract_text(eval_xpath(result, './/span[@class="gs_ctg2"]'))
        if doc_type == "[PDF]":
            pdf_url = doc_url
        else:
            html_url = doc_url

        results.append(
            {
                'template': 'paper.html',
                'type': pub_type,
                'url': url,
                'title': title,
                'authors': authors,
                'publisher': publisher,
                'journal': journal,
                'publishedDate': publishedDate,
                'content': content,
                'comments': comments,
                'html_url': html_url,
                'pdf_url': pdf_url,
            }
        )

    # parse suggestion
    for suggestion in eval_xpath(dom, '//div[contains(@class, "gs_qsuggest_wrap")]//li//a'):
        # append suggestion
        results.append({'suggestion': extract_text(suggestion)})

    for correction in eval_xpath(dom, '//div[@class="gs_r gs_pda"]/a'):
        results.append({'correction': extract_text(correction)})

    return results
