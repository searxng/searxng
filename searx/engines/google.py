# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This is the implementation of the google WEB engine.  Some of this
implementations are shared by other engines:

- :ref:`google images engine`
- :ref:`google news engine`
- :ref:`google videos engine`

The google WEB engine itself has a special setup option:

.. code:: yaml

  - name: google
    ...
    use_mobile_ui: false

``use_mobile_ui``: (default: ``false``)
  Enables to use *mobile endpoint* to bypass the google blocking (see
  :issue:`159`).  On the mobile UI of Google Search, the button :guilabel:`More
  results` is not affected by Google rate limiting and we can still do requests
  while actively blocked by the original Google search.  By activate
  ``use_mobile_ui`` this behavior is simulated by adding the parameter
  ``async=use_ac:true,_fmt:pc`` to the :py:func:`request`.

"""

from urllib.parse import urlencode
from lxml import html
from searx.utils import match_language, extract_text, eval_xpath, eval_xpath_list, eval_xpath_getindex
from searx.exceptions import SearxEngineCaptchaException

# about
about = {
    "website": 'https://www.google.com',
    "wikidata_id": 'Q9366',
    "official_api_documentation": 'https://developers.google.com/custom-search/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['general', 'web']
paging = True
time_range_support = True
safesearch = True
use_mobile_ui = False
supported_languages_url = 'https://www.google.com/preferences?#languages'

# based on https://en.wikipedia.org/wiki/List_of_Google_domains and tests
google_domains = {
    'BG': 'google.bg',  # Bulgaria
    'CZ': 'google.cz',  # Czech Republic
    'DE': 'google.de',  # Germany
    'DK': 'google.dk',  # Denmark
    'AT': 'google.at',  # Austria
    'CH': 'google.ch',  # Switzerland
    'GR': 'google.gr',  # Greece
    'AU': 'google.com.au',  # Australia
    'CA': 'google.ca',  # Canada
    'GB': 'google.co.uk',  # United Kingdom
    'ID': 'google.co.id',  # Indonesia
    'IE': 'google.ie',  # Ireland
    'IN': 'google.co.in',  # India
    'MY': 'google.com.my',  # Malaysia
    'NZ': 'google.co.nz',  # New Zealand
    'PH': 'google.com.ph',  # Philippines
    'SG': 'google.com.sg',  # Singapore
    'US': 'google.com',  # United States (google.us) redirects to .com
    'ZA': 'google.co.za',  # South Africa
    'AR': 'google.com.ar',  # Argentina
    'CL': 'google.cl',  # Chile
    'ES': 'google.es',  # Spain
    'MX': 'google.com.mx',  # Mexico
    'EE': 'google.ee',  # Estonia
    'FI': 'google.fi',  # Finland
    'BE': 'google.be',  # Belgium
    'FR': 'google.fr',  # France
    'IL': 'google.co.il',  # Israel
    'HR': 'google.hr',  # Croatia
    'HU': 'google.hu',  # Hungary
    'IT': 'google.it',  # Italy
    'JP': 'google.co.jp',  # Japan
    'KR': 'google.co.kr',  # South Korea
    'LT': 'google.lt',  # Lithuania
    'LV': 'google.lv',  # Latvia
    'NO': 'google.no',  # Norway
    'NL': 'google.nl',  # Netherlands
    'PL': 'google.pl',  # Poland
    'BR': 'google.com.br',  # Brazil
    'PT': 'google.pt',  # Portugal
    'RO': 'google.ro',  # Romania
    'RU': 'google.ru',  # Russia
    'SK': 'google.sk',  # Slovakia
    'SI': 'google.si',  # Slovenia
    'SE': 'google.se',  # Sweden
    'TH': 'google.co.th',  # Thailand
    'TR': 'google.com.tr',  # Turkey
    'UA': 'google.com.ua',  # Ukraine
    'CN': 'google.com.hk',  # There is no google.cn, we use .com.hk for zh-CN
    'HK': 'google.com.hk',  # Hong Kong
    'TW': 'google.com.tw',  # Taiwan
}

time_range_dict = {'day': 'd', 'week': 'w', 'month': 'm', 'year': 'y'}

# Filter results. 0: None, 1: Moderate, 2: Strict
filter_mapping = {0: 'off', 1: 'medium', 2: 'high'}

# specific xpath variables
# ------------------------

# google results are grouped into <div class="jtfYYd ..." ../>
results_xpath = '//div[@class="jtfYYd"]'

# google *sections* are no usual *results*, we ignore them
g_section_with_header = './g-section-with-header'

# the title is a h3 tag relative to the result group
title_xpath = './/h3[1]'

# in the result group there is <div class="yuRUbf" ../> it's first child is a <a
# href=...>
href_xpath = './/div[@class="yuRUbf"]//a/@href'

# in the result group there is <div class="VwiC3b ..." ../> containing the *content*
content_xpath = './/div[contains(@class, "VwiC3b")]'

# Suggestions are links placed in a *card-section*, we extract only the text
# from the links not the links itself.
suggestion_xpath = '//div[contains(@class, "EIaa9b")]//a'


def get_lang_info(params, lang_list, custom_aliases, supported_any_language):
    """Composing various language properties for the google engines.

    This function is called by the various google engines (:ref:`google web
    engine`, :ref:`google images engine`, :ref:`google news engine` and
    :ref:`google videos engine`).

    :param dict param: request parameters of the engine

    :param list lang_list: list of supported languages of the engine
        :py:obj:`ENGINES_LANGUAGES[engine-name] <searx.data.ENGINES_LANGUAGES>`

    :param dict lang_list: custom aliases for non standard language codes
        (used when calling :py:func:`searx.utils.match_language`)

    :param bool supported_any_language: When a language is not specified, the
        language interpretation is left up to Google to decide how the search
        results should be delivered.  This argument is ``True`` for the google
        engine and ``False`` for the other engines (google-images, -news,
        -scholar, -videos).

    :rtype: dict
    :returns:
        Py-Dictionary with the key/value pairs:

        language:
            Return value from :py:func:`searx.utils.match_language`

        country:
            The country code (e.g. US, AT, CA, FR, DE ..)

        subdomain:
            Google subdomain :py:obj:`google_domains` that fits to the country
            code.

        params:
            Py-Dictionary with additional request arguments (can be passed to
            :py:func:`urllib.parse.urlencode`).

        headers:
            Py-Dictionary with additional HTTP headers (can be passed to
            request's headers)
    """
    ret_val = {
        'language': None,
        'country': None,
        'subdomain': None,
        'params': {},
        'headers': {},
    }

    # language ...

    _lang = params['language']
    _any_language = _lang.lower() == 'all'
    if _any_language:
        _lang = 'en-US'
    language = match_language(_lang, lang_list, custom_aliases)
    ret_val['language'] = language

    # country ...

    _l = _lang.split('-')
    if len(_l) == 2:
        country = _l[1]
    else:
        country = _l[0].upper()
        if country == 'EN':
            country = 'US'
    ret_val['country'] = country

    # subdomain ...

    ret_val['subdomain'] = 'www.' + google_domains.get(country.upper(), 'google.com')

    # params & headers

    lang_country = '%s-%s' % (language, country)  # (en-US, en-EN, de-DE, de-AU, fr-FR ..)

    # hl parameter:
    #   https://developers.google.com/custom-search/docs/xml_results#hlsp The
    # Interface Language:
    #   https://developers.google.com/custom-search/docs/xml_results_appendices#interfaceLanguages

    ret_val['params']['hl'] = lang_list.get(lang_country, language)

    # lr parameter:
    #   The lr (language restrict) parameter restricts search results to
    #   documents written in a particular language.
    #   https://developers.google.com/custom-search/docs/xml_results#lrsp
    #   Language Collection Values:
    #   https://developers.google.com/custom-search/docs/xml_results_appendices#languageCollections

    if _any_language and supported_any_language:

        # interpretation is left up to Google (based on whoogle)
        #
        # - add parameter ``source=lnt``
        # - don't use parameter ``lr``
        # - don't add a ``Accept-Language`` HTTP header.

        ret_val['params']['source'] = 'lnt'

    else:

        # restricts search results to documents written in a particular
        # language.
        ret_val['params']['lr'] = "lang_" + lang_list.get(lang_country, language)

        # Accept-Language: fr-CH, fr;q=0.8, en;q=0.6, *;q=0.5
        ret_val['headers']['Accept-Language'] = ','.join(
            [
                lang_country,
                language + ';q=0.8,',
                'en;q=0.6',
                '*;q=0.5',
            ]
        )

    return ret_val


def detect_google_sorry(resp):
    if resp.url.host == 'sorry.google.com' or resp.url.path.startswith('/sorry'):
        raise SearxEngineCaptchaException()


def request(query, params):
    """Google search request"""

    offset = (params['pageno'] - 1) * 10

    lang_info = get_lang_info(params, supported_languages, language_aliases, True)

    additional_parameters = {}
    if use_mobile_ui:
        additional_parameters = {
            'asearch': 'arc',
            'async': 'use_ac:true,_fmt:pc',
        }

    # https://www.google.de/search?q=corona&hl=de&lr=lang_de&start=0&tbs=qdr%3Ad&safe=medium
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
                'start': offset,
                'filter': '0',
                **additional_parameters,
            }
        )
    )

    if params['time_range'] in time_range_dict:
        query_url += '&' + urlencode({'tbs': 'qdr:' + time_range_dict[params['time_range']]})
    if params['safesearch']:
        query_url += '&' + urlencode({'safe': filter_mapping[params['safesearch']]})
    params['url'] = query_url

    params['headers'].update(lang_info['headers'])
    if use_mobile_ui:
        params['headers']['Accept'] = '*/*'
    else:
        params['headers']['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'

    return params


def response(resp):
    """Get response from google's search request"""

    detect_google_sorry(resp)

    results = []

    # convert the text to dom
    dom = html.fromstring(resp.text)
    # results --> answer
    answer_list = eval_xpath(dom, '//div[contains(@class, "LGOjhe")]')
    if answer_list:
        answer_list = [_.xpath("normalize-space()") for _ in answer_list]
        results.append({'answer': ' '.join(answer_list)})
    else:
        logger.debug("did not find 'answer'")

        # results --> number_of_results
        if not use_mobile_ui:
            try:
                _txt = eval_xpath_getindex(dom, '//div[@id="result-stats"]//text()', 0)
                _digit = ''.join([n for n in _txt if n.isdigit()])
                number_of_results = int(_digit)
                results.append({'number_of_results': number_of_results})
            except Exception as e:  # pylint: disable=broad-except
                logger.debug("did not 'number_of_results'")
                logger.error(e, exc_info=True)

    # parse results

    for result in eval_xpath_list(dom, results_xpath):

        # google *sections*
        if extract_text(eval_xpath(result, g_section_with_header)):
            logger.debug("ingoring <g-section-with-header>")
            continue

        try:
            title_tag = eval_xpath_getindex(result, title_xpath, 0, default=None)
            if title_tag is None:
                # this not one of the common google results *section*
                logger.debug('ingoring item from the result_xpath list: missing title')
                continue
            title = extract_text(title_tag)
            url = eval_xpath_getindex(result, href_xpath, 0, None)
            if url is None:
                continue
            content = extract_text(eval_xpath_getindex(result, content_xpath, 0, default=None), allow_none=True)
            if content is None:
                logger.debug('ingoring item from the result_xpath list: missing content of title "%s"', title)
                continue

            logger.debug('add link to results: %s', title)
            results.append({'url': url, 'title': title, 'content': content})

        except Exception as e:  # pylint: disable=broad-except
            logger.error(e, exc_info=True)
            continue

    # parse suggestion
    for suggestion in eval_xpath_list(dom, suggestion_xpath):
        # append suggestion
        results.append({'suggestion': extract_text(suggestion)})

    # return results
    return results


# get supported languages from their site
def _fetch_supported_languages(resp):
    ret_val = {}
    dom = html.fromstring(resp.text)

    radio_buttons = eval_xpath_list(dom, '//*[@id="langSec"]//input[@name="lr"]')

    for x in radio_buttons:
        name = x.get("data-name")
        code = x.get("value").split('_')[-1]
        ret_val[code] = {"name": name}

    return ret_val
