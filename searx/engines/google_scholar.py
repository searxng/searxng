# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This is the implementation of the Google Scholar engine.

Compared to other Google services the Scholar engine has a simple GET REST-API
and there does not exists `async` API.  Even though the API slightly vintage we
can make use of the :ref:`google API` to assemble the arguments of the GET
request.
"""

from typing import TYPE_CHECKING
from typing import Optional

from urllib.parse import urlencode
from datetime import datetime
from lxml import html

from searx.utils import (
    eval_xpath,
    eval_xpath_getindex,
    eval_xpath_list,
    extract_text,
)

from searx.exceptions import SearxEngineCaptchaException

from searx.engines.google import fetch_traits  # pylint: disable=unused-import
from searx.engines.google import (
    get_google_info,
    time_range_dict,
)
from searx.enginelib.traits import EngineTraits

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

traits: EngineTraits

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
time_range_support = True
safesearch = False
send_accept_language_header = True


def time_range_args(params):
    """Returns a dictionary with a time range arguments based on
    ``params['time_range']``.

    Google Scholar supports a detailed search by year.  Searching by *last
    month* or *last week* (as offered by SearXNG) is uncommon for scientific
    publications and is not supported by Google Scholar.

    To limit the result list when the users selects a range, all the SearXNG
    ranges (*day*, *week*, *month*, *year*) are mapped to *year*.  If no range
    is set an empty dictionary of arguments is returned.  Example;  when
    user selects a time range (current year minus one in 2022):

    .. code:: python

        { 'as_ylo' : 2021 }

    """
    ret_val = {}
    if params['time_range'] in time_range_dict:
        ret_val['as_ylo'] = datetime.now().year - 1
    return ret_val


def detect_google_captcha(dom):
    """In case of CAPTCHA Google Scholar open its own *not a Robot* dialog and is
    not redirected to ``sorry.google.com``.
    """
    if eval_xpath(dom, "//form[@id='gs_captcha_f']"):
        raise SearxEngineCaptchaException()


def request(query, params):
    """Google-Scholar search request"""

    google_info = get_google_info(params, traits)
    # subdomain is: scholar.google.xy
    google_info['subdomain'] = google_info['subdomain'].replace("www.", "scholar.")

    args = {
        'q': query,
        **google_info['params'],
        'start': (params['pageno'] - 1) * 10,
        'as_sdt': '2007',  # include patents / to disable set '0,5'
        'as_vis': '0',  # include citations / to disable set '1'
    }
    args.update(time_range_args(params))

    params['url'] = 'https://' + google_info['subdomain'] + '/scholar?' + urlencode(args)
    params['cookies'] = google_info['cookies']
    params['headers'].update(google_info['headers'])
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
    """Parse response from Google Scholar"""
    results = []

    # convert the text to dom
    dom = html.fromstring(resp.text)
    detect_google_captcha(dom)

    # parse results
    for result in eval_xpath_list(dom, '//div[@data-rp]'):

        title = extract_text(eval_xpath(result, './/h3[1]//a'))

        if not title:
            # this is a [ZITATION] block
            continue

        pub_type = extract_text(eval_xpath(result, './/span[@class="gs_ctg2"]'))
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
