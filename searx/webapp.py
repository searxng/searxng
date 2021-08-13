#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-function-docstring
"""WebbApp

"""
import hashlib
import hmac
import json
import os
import sys
import asyncio

from typing import Optional, List
from functools import partial
from datetime import datetime, timedelta
from timeit import default_timer
from html import escape
from io import StringIO
from urllib.parse import urlencode

import aiohttp

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import (
    FileResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
    StreamingResponse
)
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette_context import context
from starlette_context.middleware import RawContextMiddleware
from starlette_i18n import i18n

from searx import (
    logger,
    get_setting,
    settings,
    searx_debug,
    searx_dir,
)
from searx.i18n import (
    initialize_i18n,
    gettext,
    format_date,
    format_decimal
)
from searx.templates import (
    I18NTemplates,
    get_current_theme_name,
    get_result_template,
    global_favicons,
    themes
)
from searx.settings_defaults import OUTPUT_FORMATS
from searx.exceptions import SearxParameterException
from searx.engines import (
    categories,
    engines,
    engine_shortcuts,
)
from searx.webutils import (
    UnicodeWriter,
    highlight_content,
    prettify_url,
    new_hmac,
)
from searx.webadapter import (
    get_search_query_from_webapp,
    get_selected_categories,
)
from searx.utils import (
    html_to_text,
    gen_useragent,
    dict_subset,
    match_language,
)
from searx.version import VERSION_STRING, GIT_URL
from searx.query import RawTextQuery
from searx.plugins import plugins
from searx.plugins.oa_doi_rewrite import get_doi_resolver
from searx.preferences import (
    Preferences,
    ValidationException,
    LANGUAGE_CODES,
)
from searx.answerers import answerers, ask
from searx.metrics import (
    get_engines_stats,
    get_engine_errors,
    get_reliabilities,
    histogram,
    counter,
)

import searx.network.client
import searx.network.network

# renaming names from searx imports ...
from searx.autocomplete import search_autocomplete, backends as autocomplete_backends
from searx.languages import language_codes as languages
from searx.locales import LOCALE_NAMES, UI_LOCALE_CODES, RTL_LOCALES
from searx.search import SearchWithPlugins, initialize as search_initialize
from searx.search.checker import get_result as checker_get_result


logger = logger.getChild('webapp')

# used when translating category names
_category_names = (
    gettext('files'),
    gettext('general'),
    gettext('music'),
    gettext('social media'),
    gettext('images'),
    gettext('videos'),
    gettext('it'),
    gettext('news'),
    gettext('map'),
    gettext('onions'),
    gettext('science')
)

#
timeout_text = gettext('timeout')
parsing_error_text = gettext('parsing error')
http_protocol_error_text = gettext('HTTP protocol error')
network_error_text = gettext('network error')
exception_classname_to_text = {
    None: gettext('unexpected crash'),
    'timeout': timeout_text,
    'asyncio.TimeoutError': timeout_text,
    'httpx.TimeoutException': timeout_text,
    'httpx.ConnectTimeout': timeout_text,
    'httpx.ReadTimeout': timeout_text,
    'httpx.WriteTimeout': timeout_text,
    'httpx.HTTPStatusError': gettext('HTTP error'),
    'httpx.ConnectError': gettext("HTTP connection error"),
    'httpx.RemoteProtocolError': http_protocol_error_text,
    'httpx.LocalProtocolError': http_protocol_error_text,
    'httpx.ProtocolError': http_protocol_error_text,
    'httpx.ReadError': network_error_text,
    'httpx.WriteError': network_error_text,
    'httpx.ProxyError': gettext("proxy error"),
    'searx.exceptions.SearxEngineCaptchaException': gettext("CAPTCHA"),
    'searx.exceptions.SearxEngineTooManyRequestsException': gettext("too many requests"),
    'searx.exceptions.SearxEngineAccessDeniedException': gettext("access denied"),
    'searx.exceptions.SearxEngineAPIException': gettext("server API error"),
    'searx.exceptions.SearxEngineXPathException': parsing_error_text,
    'KeyError': parsing_error_text,
    'json.decoder.JSONDecodeError': parsing_error_text,
    'lxml.etree.ParserError': parsing_error_text,
}

STATS_SORT_PARAMETERS = {
    'name': (False, 'name', ''),
    'score': (True, 'score', 0),
    'result_count': (True, 'result_count', 0),
    'time': (False, 'total', 0),
    'reliability': (False, 'reliability', 100),
}
AIOHTTP_SESSION: Optional[aiohttp.ClientSession] = None

templates = I18NTemplates(directory=settings['ui']['templates_path'])

routes = [
    Mount('/static', app=StaticFiles(directory=settings['ui']['static_path']), name="static"),
]

def on_startup():
    global AIOHTTP_SESSION  # pylint: disable=global-statement
    # check secret_key
    if not searx_debug and settings['server']['secret_key'] == 'ultrasecretkey':
        logger.error('server.secret_key is not changed. Please use something else instead of ultrasecretkey.')
        sys.exit(1)
    searx.network.client.set_loop(asyncio.get_event_loop())
    initialize_i18n(os.path.join(searx_dir, 'translations'))
    search_initialize(enable_checker=True)
    #
    AIOHTTP_SESSION = aiohttp.ClientSession(auto_decompress=False)


async def on_shutdown():
    await searx.network.network.Network.aclose_all()


app = Starlette(routes=routes, debug=searx_debug, on_startup=[on_startup], on_shutdown=[on_shutdown])


@app.middleware("http")
async def pre_post_request(request: Request, call_next):
    # pre-request
    context.clear()
    context.request = request
    context.start_time = default_timer()
    context.render_time = 0
    context.timings = []
    i18n.set_locale('en')
    # call endpoint
    response = await call_next(request)
    # set default http headers
    for header, value in settings['server']['default_http_headers'].items():
        if header not in response.headers:
            response.headers[header] = value
    # set timing Server-Timing header
    total_time = default_timer() - context.start_time
    timings_all = ['total;dur=' + str(round(total_time * 1000, 3)),
                'render;dur=' + str(round(context.render_time * 1000, 3))]
    if len(context.timings) > 0:
        timings = sorted(context.timings, key=lambda v: v['total'])
        timings_total = [
            'total_' + str(i) + '_' + v['engine'] +  ';dur=' + str(round(v['total'] * 1000, 3))
            for i, v in enumerate(timings)
        ]
        timings_load = [
            'load_' + str(i) + '_' + v['engine'] + ';dur=' + str(round(v['load'] * 1000, 3))
            for i, v in enumerate(timings) if v.get('load')
        ]
        timings_all = timings_all + timings_total + timings_load
    response.headers['Server-Timing'] = ', '.join(timings_all)
    return response


app.add_middleware(RawContextMiddleware)


def _get_browser_or_settings_language(req : Request, lang_list: List[str]):
    for lang in req.headers.get("Accept-Language", "en").split(","):
        if ';' in lang:
            lang = lang.split(';')[0]
        if '-' in lang:
            lang_parts = lang.split('-')
            lang = "{}-{}".format(lang_parts[0], lang_parts[-1].upper())
        locale = match_language(lang, lang_list, fallback=None)
        if locale is not None:
            return locale
    return settings['search']['default_lang'] or 'en'


def proxify(url: str) -> str:
    if url.startswith('//'):
        url = 'https:' + url

    if not settings.get('result_proxy'):
        return url

    url_params = dict(mortyurl=url.encode())

    if settings['result_proxy'].get('key'):
        url_params['mortyhash'] = hmac.new(
            settings['result_proxy']['key'],
            url.encode(),
            hashlib.sha256
        ).hexdigest()

    return '{0}?{1}'.format(
        settings['result_proxy']['url'],
        urlencode(url_params)
    )


def image_proxify(request: Request, url: str):

    if url.startswith('//'):
        url = 'https:' + url

    if not context.preferences.get_value('image_proxy'):
        return url

    if url.startswith('data:image/'):
        # 50 is an arbitrary number to get only the beginning of the image.
        partial_base64 = url[len('data:image/'):50].split(';')
        if len(partial_base64) == 2 \
           and partial_base64[0] in ['gif', 'png', 'jpeg', 'pjpeg', 'webp', 'tiff', 'bmp']\
           and partial_base64[1].startswith('base64,'):
            return url
        return None

    if settings.get('result_proxy'):
        return proxify(url)

    h = new_hmac(settings['server']['secret_key'], url.encode())

    return '{0}?{1}'.format(request.url_for('image_proxy'),
                            urlencode(dict(url=url.encode(), h=h)))


def get_translations():
    return {
        # when there is autocompletion
        'no_item_found': str(gettext('No item found'))
    }


def _get_ordered_categories():
    ordered_categories = list(settings['ui']['categories_order'])
    ordered_categories.extend(x for x in sorted(categories.keys()) if x not in ordered_categories)
    return ordered_categories


def _get_enable_categories(all_categories):
    disabled_engines = context.preferences.engines.get_disabled()
    enabled_categories = set(
        # pylint: disable=consider-using-dict-items
        category for engine_name in engines
        for category in engines[engine_name].categories
        if (engine_name, category) not in disabled_engines
    )
    return [x for x in all_categories if x in enabled_categories]


def render(request: Request,
           template_name: str,
           override_theme: bool = None,
           status_code: int = 200,
           headers: dict = None,
           media_type: str = None,
           **kwargs) -> Response:
    # values from the HTTP requests
    kwargs['request'] = request
    kwargs['endpoint'] = 'results' if 'q' in kwargs else request.scope['path']
    kwargs['cookies'] = request.cookies
    kwargs['errors'] = context.errors

    # values from the preferences
    kwargs['preferences'] = context.preferences
    kwargs['method'] = context.preferences.get_value('method')
    kwargs['autocomplete'] = context.preferences.get_value('autocomplete')
    kwargs['results_on_new_tab'] = context.preferences.get_value('results_on_new_tab')
    kwargs['advanced_search'] = context.preferences.get_value('advanced_search')
    kwargs['safesearch'] = str(context.preferences.get_value('safesearch'))
    kwargs['theme'] = get_current_theme_name(request, override=override_theme)
    kwargs['all_categories'] = _get_ordered_categories()
    kwargs['categories'] = _get_enable_categories(kwargs['all_categories'])

    # i18n
    kwargs['language_codes'] = languages  # from searx.languages
    kwargs['translations'] = json.dumps(get_translations(), separators=(',', ':'))

    locale = context.preferences.get_value('locale')
    if locale in RTL_LOCALES and 'rtl' not in kwargs:
        kwargs['rtl'] = True
    if 'current_language' not in kwargs:
        kwargs['current_language'] = match_language(
            context.preferences.get_value('language'), LANGUAGE_CODES )

    # values from settings
    kwargs['search_formats'] = [
        x for x in settings['search']['formats'] if x != 'html'
    ]
    kwargs['instance_name'] = settings['general']['instance_name']
    kwargs['searx_version'] = VERSION_STRING
    kwargs['searx_git_url'] = GIT_URL
    kwargs['get_setting'] = get_setting

   # helpers to create links to other pages
    kwargs['image_proxify'] = partial(image_proxify, request)
    kwargs['proxify'] = proxify if settings.get('result_proxy', {}).get('url') else None
    kwargs['proxify_results'] = settings.get('result_proxy', {}).get('proxify_results', True)
    kwargs['get_result_template'] = get_result_template
    kwargs['opensearch_url'] = (
        request.url_for('opensearch')
        + '?'
        + urlencode({'method': kwargs['method'], 'autocomplete': kwargs['autocomplete']})
    )

    # scripts from plugins
    kwargs['scripts'] = set()
    for plugin in context.user_plugins:
        for script in plugin.js_dependencies:
            kwargs['scripts'].add(script)

    # styles from plugins
    kwargs['styles'] = set()
    for plugin in context.user_plugins:
        for css in plugin.css_dependencies:
            kwargs['styles'].add(css)

    start_time = default_timer()
    result = templates.TemplateResponse(
        '{}/{}'.format(kwargs['theme'], template_name),
        kwargs,
        status_code=status_code,
        headers=headers,
        media_type=media_type
    )
    context.render_time += default_timer() - start_time  # pylint: disable=assigning-non-slot

    return result


async def set_context(request: Request):
    context.errors = []  # pylint: disable=assigning-non-slot

    preferences = Preferences(themes, list(categories.keys()), engines, plugins)  # pylint: disable=redefined-outer-name
    user_agent = request.headers.get('User-Agent', '').lower()
    if 'webkit' in user_agent and 'android' in user_agent:
        preferences.key_value_settings['method'].value = 'GET'
    context.preferences = preferences  # pylint: disable=assigning-non-slot

    try:
        preferences.parse_dict(request.cookies)
    except Exception as e:  # pylint: disable=broad-except
        logger.exception(e, exc_info=True)
        context.errors.append(gettext('Invalid settings, please edit your preferences'))

    # merge GET, POST vars
    # context.form
    context.form = dict(await request.form())  # pylint: disable=assigning-non-slot
    for k, v in request.query_params.items():
        if k not in context.form:
            context.form[k] = v
    if context.form.get('preferences'):
        preferences.parse_encoded_data(context.form['preferences'])
    else:
        try:
            preferences.parse_dict(context.form)
        except Exception as e:  # pylint: disable=broad-except
            logger.exception(e, exc_info=True)
            context.errors.append(gettext('Invalid settings'))

    # set search language
    if not preferences.get_value("language"):
        preferences.parse_dict({"language": _get_browser_or_settings_language(request, LANGUAGE_CODES)})

    # set UI locale
    locale_source = 'preferences or query'
    if not preferences.get_value("locale"):
        locale = _get_browser_or_settings_language(request, UI_LOCALE_CODES)
        locale = locale.replace('-', '_')
        preferences.parse_dict({"locale": locale})
        locale_source = 'browser'

    logger.debug(
        "%s uses locale `%s` from %s",
        str(request.scope['path']),
        preferences.get_value("locale"),
        locale_source
    )

    # set starlette.i18n locale (get_text)
    i18n.set_locale(code=preferences.get_value("locale"))

    # context.user_plugins
    context.user_plugins = []  # pylint: disable=assigning-non-slot
    allowed_plugins = preferences.plugins.get_enabled()
    disabled_plugins = preferences.plugins.get_disabled()
    for plugin in plugins:
        if ((plugin.default_on and plugin.id not in disabled_plugins)
                or plugin.id in allowed_plugins):
            context.user_plugins.append(plugin)


def search_error(request, output_format, error_message):
    if output_format == 'json':
        return JSONResponse({'error': error_message})
    if output_format == 'csv':
        cont_disp = 'attachment;Filename=searx.csv'
        return Response('', media_type='application/csv', headers= {'Content-Disposition': cont_disp})
    if output_format == 'rss':
        response_rss = render(
            request,
            'opensearch_response_rss.xml',
            results=[],
            q=context.form['q'] if 'q' in context.form else '',
            number_of_results=0,
            error_message=error_message,
            override_theme='__common__',
        )
        return Response(response_rss, media_type='text/xml')

    # html
    context.errors.append(gettext('search error'))
    return render(
        request,
        'index.html',
        selected_categories=get_selected_categories(context.preferences, context.form),
    )


@app.route('/', methods=['GET', 'POST'])
async def index(request: Request):
    await set_context(request)
    return render(
        request,
        'index.html',
        selected_categories=get_selected_categories(context.preferences, context.form)
    )


@app.route('/search', methods=['GET', 'POST'])
async def search(request: Request):
    """Search query in q and return results.

    Supported outputs: html, json, csv, rss.
    """
    # pylint: disable=too-many-locals, too-many-return-statements, too-many-branches
    # pylint: disable=too-many-statements

    await set_context(request)

    # output_format
    output_format = context.form.get('format', 'html')
    if output_format not in OUTPUT_FORMATS:
        output_format = 'html'

    if output_format not in settings['search']['formats']:
        return PlainTextResponse('', status_code=403)

    # check if there is query (not None and not an empty string)
    if not context.form.get('q'):
        if output_format == 'html':
            return render(
                request,
                'index.html',
                selected_categories=get_selected_categories(context.preferences, context.form),
            )
        return search_error(request, output_format, 'No query'), 400

    # search
    search_query = None
    raw_text_query = None
    result_container = None
    try:
        search_query, raw_text_query, _, _ = get_search_query_from_webapp(
            context.preferences, context.form
        )
        # search = Search(search_query) #  without plugins
        search = SearchWithPlugins(search_query, context.user_plugins, request)  # pylint: disable=redefined-outer-name

        result_container = await search.search()

    except SearxParameterException as e:
        logger.exception('search error: SearxParameterException')
        return search_error(request, output_format, e.message), 400
    except Exception as e:  # pylint: disable=broad-except
        logger.exception(e, exc_info=True)
        return search_error(request, output_format, gettext('search error')), 500

    # results
    results = result_container.get_ordered_results()
    number_of_results = result_container.results_number()
    if number_of_results < result_container.results_length():
        number_of_results = 0

    # checkin for a external bang
    if result_container.redirect_url:
        return RedirectResponse(result_container.redirect_url)

    # Server-Timing header
    context.timings = result_container.get_timings()  # pylint: disable=assigning-non-slot

    # output
    for result in results:
        if output_format == 'html':
            if 'content' in result and result['content']:
                result['content'] = highlight_content(escape(result['content'][:1024]), search_query.query)
            if 'title' in result and result['title']:
                result['title'] = highlight_content(escape(result['title'] or ''), search_query.query)
        else:
            if result.get('content'):
                result['content'] = html_to_text(result['content']).strip()
            # removing html content and whitespace duplications
            result['title'] = ' '.join(html_to_text(result['title']).strip().split())

        if 'url' in result:
            result['pretty_url'] = prettify_url(result['url'])

        # TODO, check if timezone is calculated right  # pylint: disable=fixme
        if result.get('publishedDate'):  # do not try to get a date from an empty string or a None type
            try:  # test if publishedDate >= 1900 (datetime module bug)
                result['pubdate'] = result['publishedDate'].strftime('%Y-%m-%d %H:%M:%S%z')
            except ValueError:
                result['publishedDate'] = None
            else:
                if result['publishedDate'].replace(tzinfo=None) >= datetime.now() - timedelta(days=1):
                    timedifference = datetime.now() - result['publishedDate'].replace(tzinfo=None)
                    minutes = int((timedifference.seconds / 60) % 60)
                    hours = int(timedifference.seconds / 60 / 60)
                    if hours == 0:
                        result['publishedDate'] = gettext('{minutes} minute(s) ago').format(minutes=minutes)
                    else:
                        result['publishedDate'] = gettext(
                            '{hours} hour(s), {minutes} minute(s) ago').format(
                                hours=hours, minutes=minutes
                            )
                else:
                    result['publishedDate'] = format_date(result['publishedDate'])

    if output_format == 'json':
        x = {
            'query': search_query.query,
            'number_of_results': number_of_results,
            'results': results,
            'answers': list(result_container.answers),
            'corrections': list(result_container.corrections),
            'infoboxes': result_container.infoboxes,
            'suggestions': list(result_container.suggestions),
            'unresponsive_engines': __get_translated_errors(result_container.unresponsive_engines)
        }
        response = json.dumps(
            x,  default = lambda item: list(item) if isinstance(item, set) else item
        )
        return JSONResponse(response)

    if output_format == 'csv':
        csv = UnicodeWriter(StringIO())
        keys = ('title', 'url', 'content', 'host', 'engine', 'score', 'type')
        csv.writerow(keys)
        for row in results:
            row['host'] = row['parsed_url'].netloc
            row['type'] = 'result'
            csv.writerow([row.get(key, '') for key in keys])
        for a in result_container.answers:
            row = {'title': a, 'type': 'answer'}
            csv.writerow([row.get(key, '') for key in keys])
        for a in result_container.suggestions:
            row = {'title': a, 'type': 'suggestion'}
            csv.writerow([row.get(key, '') for key in keys])
        for a in result_container.corrections:
            row = {'title': a, 'type': 'correction'}
            csv.writerow([row.get(key, '') for key in keys])
        csv.stream.seek(0)
        response = Response(csv.stream.read(), media_type='application/csv')
        cont_disp = 'attachment;Filename=searx_-_{0}.csv'.format(search_query.query)
        response.headers['Content-Disposition'] = cont_disp
        return response

    if output_format == 'rss':
        return render(
            request,
            'opensearch_response_rss.xml',
            media_type='text/xml',
            results=results,
            answers=result_container.answers,
            corrections=result_container.corrections,
            suggestions=result_container.suggestions,
            q=context.form['q'],
            number_of_results=number_of_results,
            override_theme='__common__',
        )

    # HTML output format

    # suggestions: use RawTextQuery to get the suggestion URLs with the same bang
    suggestion_urls = list(
        map(
            lambda suggestion: {
                'url': raw_text_query.changeQuery(suggestion).getFullQuery(),
                'title': suggestion
            },
            result_container.suggestions
        ))

    correction_urls = list(
        map(
            lambda correction: {
                'url': raw_text_query.changeQuery(correction).getFullQuery(),
                'title': correction
            },
            result_container.corrections
        ))

    return render(
        request,
        'results.html',
        results = results,
        q=context.form['q'],
        selected_categories = search_query.categories,
        pageno = search_query.pageno,
        time_range = search_query.time_range,
        number_of_results = format_decimal(number_of_results),
        suggestions = suggestion_urls,
        answers = result_container.answers,
        corrections = correction_urls,
        infoboxes = result_container.infoboxes,
        engine_data = result_container.engine_data,
        paging = result_container.paging,
        unresponsive_engines = __get_translated_errors(
            result_container.unresponsive_engines
        ),
        current_language = match_language(
            search_query.lang,
            LANGUAGE_CODES,
            fallback=context.preferences.get_value("language")
        ),
        theme = get_current_theme_name(request),
        favicons = global_favicons[themes.index(get_current_theme_name(request))],
        timeout_limit = context.form.get('timeout_limit', None)
    )


def __get_translated_errors(unresponsive_engines):
    translated_errors = []

    # make a copy unresponsive_engines to avoid "RuntimeError: Set changed size
    # during iteration" it happens when an engine modifies the ResultContainer
    # after the search_multiple_requests method has stopped waiting

    for unresponsive_engine in list(unresponsive_engines):
        error_user_text = exception_classname_to_text.get(unresponsive_engine[1])
        if not error_user_text:
            error_user_text = exception_classname_to_text[None]
        error_msg = gettext(error_user_text)
        if unresponsive_engine[2]:
            error_msg = "{} {}".format(error_msg, unresponsive_engine[2])
        if unresponsive_engine[3]:
            error_msg = gettext('Suspended') + ': ' + error_msg
        translated_errors.append((unresponsive_engine[0], error_msg))

    return sorted(translated_errors, key=lambda e: e[0])


@app.route('/about', methods=['GET'])
async def about(request):
    """Render about page"""
    await set_context(request)
    return render(request, 'about.html')


@app.route('/autocompleter', methods=['GET', 'POST'])
async def autocompleter(request):
    """Return autocompleter results"""

    await set_context(request)

    # run autocompleter
    results = []

    # set blocked engines
    disabled_engines = context.preferences.engines.get_disabled()

    # parse query
    raw_text_query = RawTextQuery(context.form.get('q', ''), disabled_engines)
    sug_prefix = raw_text_query.getQuery()

    # normal autocompletion results only appear if no inner results returned
    # and there is a query part
    if len(raw_text_query.autocomplete_list) == 0 and len(sug_prefix) > 0:

        # get language from cookie
        language = context.preferences.get_value('language')
        if not language or language == 'all':
            language = 'en'
        else:
            language = language.split('-')[0]

        # run autocompletion
        raw_results = search_autocomplete(
            context.preferences.get_value('autocomplete'), sug_prefix, language
        )
        for result in raw_results:
            # attention: this loop will change raw_text_query object and this is
            # the reason why the sug_prefix was stored before (see above)
            results.append(raw_text_query.changeQuery(result).getFullQuery())

    if len(raw_text_query.autocomplete_list) > 0:
        for autocomplete_text in raw_text_query.autocomplete_list:
            results.append(raw_text_query.get_autocomplete_full_query(autocomplete_text))

    for answers in ask(raw_text_query):
        for answer in answers:
            results.append(str(answer['answer']))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # the suggestion request comes from the searx search form
        suggestions = json.dumps(results)
        mimetype = 'application/json'
    else:
        # the suggestion request comes from browser's URL bar
        suggestions = json.dumps([sug_prefix, results])
        mimetype = 'application/x-suggestions+json'

    return Response(suggestions, media_type=mimetype)


@app.route('/preferences', methods=['GET', 'POST'])
async def preferences(request: Request):
    """Render preferences page && save user preferences"""

    # pylint: disable=too-many-locals, too-many-return-statements, too-many-branches
    # pylint: disable=too-many-statements

    await set_context(request)

    # save preferences
    if request.method == 'POST':
        resp = RedirectResponse(url=request.url_for('index'))
        try:
            context.preferences.parse_form(context.form)
        except ValidationException:
            context.errors.append(gettext('Invalid settings, please edit your preferences'))
            return resp
        for cookie_name in request.cookies:
            resp.delete_cookie(cookie_name)
        context.preferences.save(resp)
        return resp

    # render preferences
    image_proxy = context.preferences.get_value('image_proxy')  # pylint: disable=redefined-outer-name
    disabled_engines = context.preferences.engines.get_disabled()
    allowed_plugins = context.preferences.plugins.get_enabled()

    # stats for preferences page
    filtered_engines = dict(
        filter(
            lambda kv: (kv[0], context.preferences.validate_token(kv[1])),
            engines.items()
        )
    )

    engines_by_category = {}

    for c in categories: # pylint: disable=consider-using-dict-items
        engines_by_category[c] = [e for e in categories[c] if e.name in filtered_engines]
        # sort the engines alphabetically since the order in settings.yml is meaningless.
        list.sort(engines_by_category[c], key=lambda e: e.name)

    # get first element [0], the engine time,
    # and then the second element [1] : the time (the first one is the label)
    stats = {}  # pylint: disable=redefined-outer-name
    max_rate95 = 0
    for _, e in filtered_engines.items():
        h = histogram('engine', e.name, 'time', 'total')
        median = round(h.percentage(50), 1) if h.count > 0 else None
        rate80 = round(h.percentage(80), 1) if h.count > 0 else None
        rate95 = round(h.percentage(95), 1) if h.count > 0 else None

        max_rate95 = max(max_rate95, rate95 or 0)

        result_count_sum = histogram('engine', e.name, 'result', 'count').sum
        successful_count = counter('engine', e.name, 'search', 'count', 'successful')
        result_count = int(result_count_sum / float(successful_count)) if successful_count else 0

        stats[e.name] = {
            'time': median,
            'rate80': rate80,
            'rate95': rate95,
            'warn_timeout': e.timeout > settings['outgoing']['request_timeout'],
            'supports_selected_language': _is_selected_language_supported(e, context.preferences),
            'result_count': result_count,
        }
    # end of stats

    # reliabilities
    reliabilities = {}
    engine_errors = get_engine_errors(filtered_engines)
    checker_full_results = checker_get_result()
    checker_results = {}
    if checker_full_results and checker_full_results['status'] == 'ok' and 'engines' in checker_full_results:
        checker_results = checker_results['engines']
    for _, e in filtered_engines.items():
        checker_result = checker_results.get(e.name, {})
        checker_success = checker_result.get('success', True)
        errors = engine_errors.get(e.name) or []
        if counter('engine', e.name, 'search', 'count', 'sent') == 0:
            # no request
            reliablity = None
        elif checker_success and not errors:
            reliablity = 100
        elif 'simple' in checker_result.get('errors', {}):
            # the basic (simple) test doesn't work: the engine is broken accoding to the checker
            # even if there is no exception
            reliablity = 0
        else:
            reliablity = 100 - sum([error['percentage'] for error in errors if not error.get('secondary')])

        reliabilities[e.name] = {
            'reliablity': reliablity,
            'errors': [],
            'checker': checker_results.get(e.name, {}).get('errors', {}).keys(),
        }
        # keep the order of the list checker_results[e.name]['errors'] and deduplicate.
        # the first element has the highest percentage rate.
        reliabilities_errors = []
        for error in errors:
            error_user_text = None
            if error.get('secondary') or 'exception_classname' not in error:
                continue
            error_user_text = exception_classname_to_text.get(error.get('exception_classname'))
            if not error:
                error_user_text = exception_classname_to_text[None]
            if error_user_text not in reliabilities_errors:
                reliabilities_errors.append(error_user_text)
        reliabilities[e.name]['errors'] = reliabilities_errors

    # supports
    supports = {}
    for _, e in filtered_engines.items():
        supports_selected_language = _is_selected_language_supported(e, context.preferences)
        safesearch = e.safesearch
        time_range_support = e.time_range_support
        for checker_test_name in checker_results.get(e.name, {}).get('errors', {}):
            if supports_selected_language and checker_test_name.startswith('lang_'):
                supports_selected_language = '?'
            elif safesearch and checker_test_name == 'safesearch':
                safesearch = '?'
            elif time_range_support and checker_test_name == 'time_range':
                time_range_support = '?'
        supports[e.name] = {
            'supports_selected_language': supports_selected_language,
            'safesearch': safesearch,
            'time_range_support': time_range_support,
        }

    return render(
        request,
        'preferences.html',
        selected_categories = get_selected_categories(context.preferences, context.form),
        locales = LOCALE_NAMES,
        current_locale = context.preferences.get_value("locale"),
        image_proxy = image_proxy,
        engines_by_category = engines_by_category,
        stats = stats,
        max_rate95 = max_rate95,
        reliabilities = reliabilities,
        supports = supports,
        answerers = [
            {'info': a.self_info(), 'keywords': a.keywords}
            for a in answerers
        ],
        disabled_engines = disabled_engines,
        autocomplete_backends = autocomplete_backends,
        shortcuts = {y: x for x, y in engine_shortcuts.items()},
        themes = themes,
        plugins = plugins,
        doi_resolvers = settings['doi_resolvers'],
        current_doi_resolver = get_doi_resolver(
            context.form, context.preferences.get_value('doi_resolver')
        ),
        allowed_plugins = allowed_plugins,
        theme = get_current_theme_name(request),
        preferences_url_params = context.preferences.get_as_url_params(),
        locked_preferences = settings['preferences']['lock'],
        preferences = True
    )


def _is_selected_language_supported(engine, preferences):  # pylint: disable=redefined-outer-name
    language = preferences.get_value('language')
    if language == 'all':
        return True
    x = match_language(
        language,
        getattr(engine, 'supported_languages', []),
        getattr(engine, 'language_aliases', {}),
        None
    )
    return bool(x)


@app.route('/image_proxy', methods=['GET'])
async def image_proxy(request: Request):
    # pylint: disable=too-many-return-statements, too-many-branches

    url = request.query_params.get('url')
    if not url:
        return PlainTextResponse('No URL', status_code=400)

    h = new_hmac(settings['server']['secret_key'], url.encode())
    if h != request.query_params.get('h'):
        return PlainTextResponse('Wrong k', status_code=400)

    maximum_size = 5 * 1024 * 1024
    do_forward = False
    try:
        request_headers = {
            'User-Agent': gen_useragent(),
            'Accept': 'image/webp,*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-GPC': '1',
            'DNT': '1',
        }
        resp = await AIOHTTP_SESSION.get(url, headers=request_headers).__aenter__()
        content_length = resp.headers.get('Content-Length')
        if (content_length
            and content_length.isdigit()
            and int(content_length) > maximum_size):
            return PlainTextResponse('Max size', status_code=400)

        if resp.status == 304:
            return Response(None, status_code=resp.status, media_type=resp.content_type)

        if resp.status != 200:
            logger.debug('image-proxy: wrong response code: {0}'.format(resp.status))
            if resp.status >= 400:
                return PlainTextResponse('Status code', status_code=resp.status)
            return PlainTextResponse('Status code', status_code=400)

        if not resp.headers.get('content-type', '').startswith('image/'):
            logger.debug(
                'image-proxy: wrong content-type: {0}'.format(
                    resp.headers.get('content-type')))
            return PlainTextResponse('Wrong content type', status_code=400)

        do_forward = True
    except aiohttp.ClientError:
        logger.exception('HTTP error')
        return PlainTextResponse('HTTP Error', status_code=400)
    finally:
        if not do_forward and resp:
            try:
                resp.close()
            except aiohttp.ClientError:
                logger.exception('HTTP error on closing')

    # forward image
    try:
        async def forward_chunk(resp):
            total_length = 0
            try:
                chunk = await resp.content.readany()
                while chunk:
                    yield chunk
                    total_length += len(chunk)
                    if total_length > maximum_size:
                        break
                    chunk = await resp.content.readany()
            except aiohttp.client.ClientError:
                logger.exception('Error reading URL')
            finally:
                resp.close()

        headers = dict_subset(
            resp.headers,
            {'Content-Type', 'Content-Encoding', 'Content-Length', 'Length'}
        )

        return StreamingResponse(forward_chunk(resp), headers=headers)
    except aiohttp.ClientError:
        logger.exception('HTTP error')
        return PlainTextResponse('HTTP Error', status_code=400)


@app.route('/stats', methods=['GET'])
async def stats(request: Request):
    """Render engine statistics page."""
    await set_context(request)

    sort_order = request.query_params.get('sort', 'name')
    selected_engine_name = request.query_params.get('engine', None)

    filtered_engines = dict(
        filter(
            lambda kv: (kv[0], context.preferences.validate_token(kv[1])),
            engines.items()
        ))
    if selected_engine_name:
        if selected_engine_name not in filtered_engines:
            selected_engine_name = None
        else:
            filtered_engines = [selected_engine_name]

    checker_results = checker_get_result()
    checker_results = (
        checker_results['engines']
        if checker_results['status'] == 'ok' and 'engines' in checker_results else {}
    )

    engine_stats = get_engines_stats(filtered_engines)
    engine_reliabilities = get_reliabilities(filtered_engines, checker_results)

    if sort_order not in STATS_SORT_PARAMETERS:
        sort_order = 'name'

    reverse, key_name, default_value = STATS_SORT_PARAMETERS[sort_order]

    def get_key(engine_stat):
        reliability = engine_reliabilities.get(engine_stat['name']).get('reliablity', 0)
        reliability_order = 0 if reliability else 1
        if key_name == 'reliability':
            key = reliability
            reliability_order = 0
        else:
            key = engine_stat.get(key_name) or default_value
            if reverse:
                reliability_order = 1 - reliability_order
        return (reliability_order, key, engine_stat['name'])

    engine_stats['time'] = sorted(engine_stats['time'], reverse=reverse, key=get_key)
    return render(
        request,
        'stats.html',
        sort_order = sort_order,
        engine_stats = engine_stats,
        engine_reliabilities = engine_reliabilities,
        selected_engine_name = selected_engine_name,
    )


@app.route('/stats/errors', methods=['GET'])
async def stats_errors(request: Request):
    await set_context(request)
    filtered_engines = dict(
        filter(
            lambda kv: (kv[0], context.preferences.validate_token(kv[1])),
            engines.items()
        ))
    result = get_engine_errors(filtered_engines)
    return JSONResponse(result)


@app.route('/stats/checker', methods=['GET'])
async def stats_checker(request: Request):  # pylint: disable=unused-argument
    result = checker_get_result()
    return JSONResponse(result)


@app.route('/robots.txt', methods=['GET'])
async def robots(request: Request):  # pylint: disable=unused-argument
    return PlainTextResponse("""User-agent: *
Allow: /
Allow: /about
Disallow: /stats
Disallow: /preferences
Disallow: /*?*q=*
""", media_type='text/plain')


@app.route('/opensearch.xml', methods=['GET'])
async def opensearch(request: Request):
    await set_context(request)
    method = 'post'

    if context.preferences.get_value('method') == 'GET':
        method = 'get'

    # chrome/chromium only supports HTTP GET....
    if request.headers.get('User-Agent', '').lower().find('webkit') >= 0:
        method = 'get'

    return render(
        request,
        'opensearch.xml',
        status = 200,
        media_type = "application/opensearchdescription+xml",
        opensearch_method=method,
        override_theme='__common__'
    )


@app.route('/favicon.ico')
async def favicon(request: Request):
    await set_context(request)
    return FileResponse(
        os.path.join(
            searx_dir,
            settings['ui']['static_path'],
            'themes',
            get_current_theme_name(request),
            'img',
            'favicon.png'
        ),
        media_type = 'image/vnd.microsoft.icon'
    )


@app.route('/clear_cookies')
def clear_cookies(request: Request):
    resp = RedirectResponse(request.url_for('index'))
    for cookie_name in request.cookies:
        resp.delete_cookie(cookie_name)
    return resp


@app.route('/config')
async def config(request: Request):
    """Return configuration in JSON format."""
    await set_context(request)

    _engines = []
    for name, engine in engines.items():
        if not context.preferences.validate_token(engine):
            continue

        supported_languages = engine.supported_languages
        if isinstance(engine.supported_languages, dict):
            supported_languages = list(engine.supported_languages.keys())

        _engines.append({
            'name': name,
            'categories': engine.categories,
            'shortcut': engine.shortcut,
            'enabled': not engine.disabled,
            'paging': engine.paging,
            'language_support': engine.language_support,
            'supported_languages': supported_languages,
            'safesearch': engine.safesearch,
            'time_range_support': engine.time_range_support,
            'timeout': engine.timeout
        })

    _plugins = []
    for _ in plugins:
        _plugins.append({'name': _.name, 'enabled': _.default_on})

    return JSONResponse({
        'categories': list(categories.keys()),
        'engines': _engines,
        'plugins': _plugins,
        'instance_name': settings['general']['instance_name'],
        'locales': LOCALE_NAMES,
        'default_locale': settings['ui']['default_locale'],
        'autocomplete': settings['search']['autocomplete'],
        'safe_search': settings['search']['safe_search'],
        'default_theme': settings['ui']['default_theme'],
        'version': VERSION_STRING,
        'brand': {
            'CONTACT_URL': get_setting('general.contact_url'),
            'GIT_URL': GIT_URL,
            'DOCS_URL': get_setting('brand.docs_url'),
        },
        'doi_resolvers': list(settings['doi_resolvers'].keys()),
        'default_doi_resolver': settings['default_doi_resolver'],
    })


@app.exception_handler(404)
async def page_not_found(request: Request, exc):
    await set_context(request)
    return render(
        request,
        '404.html',
        status_code=exc.status_code
    )


def run():
    # pylint: disable=import-outside-toplevel
    logger.debug(
        'starting webserver on %s:%s',
        settings['server']['bind_address'],
        settings['server']['port']
    )
    if searx_debug:
        from searx.run import run_debug
        run_debug()
    else:
        from searx.run import run_production
        run_production(app)

application = app

if __name__ == "__main__":
    run()
