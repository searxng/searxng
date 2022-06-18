#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pyright: basic
"""WebbApp

"""
import hashlib
import hmac
import json
import os
import sys
import base64

from datetime import datetime, timedelta
from timeit import default_timer
from html import escape
from io import StringIO
import typing
from typing import List, Dict, Iterable

import urllib
import urllib.parse
from urllib.parse import urlencode, unquote

import httpx

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter  # pylint: disable=no-name-in-module

import flask

from flask import (
    Flask,
    render_template,
    url_for,
    make_response,
    redirect,
    send_from_directory,
)
from flask.wrappers import Response
from flask.json import jsonify

from flask_babel import (
    Babel,
    gettext,
    format_date,
    format_decimal,
)

from searx import (
    logger,
    get_setting,
    settings,
    searx_debug,
)

from searx import infopage
from searx.data import ENGINE_DESCRIPTIONS
from searx.results import Timing, UnresponsiveEngine
from searx.settings_defaults import OUTPUT_FORMATS
from searx.settings_loader import get_default_settings_path
from searx.exceptions import SearxParameterException
from searx.engines import (
    OTHER_CATEGORY,
    categories,
    engines,
    engine_shortcuts,
)
from searx.webutils import (
    UnicodeWriter,
    highlight_content,
    get_static_files,
    get_result_templates,
    get_themes,
    prettify_url,
    new_hmac,
    is_hmac_of,
    is_flask_run_cmdline,
    group_engines_in_tab,
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
from searx.version import VERSION_STRING, GIT_URL, GIT_BRANCH
from searx.query import RawTextQuery
from searx.plugins import Plugin, plugins, initialize as plugin_initialize
from searx.plugins.oa_doi_rewrite import get_doi_resolver
from searx.preferences import (
    Preferences,
    ValidationException,
)
from searx.answerers import (
    answerers,
    ask,
)
from searx.metrics import (
    get_engines_stats,
    get_engine_errors,
    get_reliabilities,
    histogram,
    counter,
)
from searx.flaskfix import patch_application

from searx.locales import (
    LOCALE_NAMES,
    RTL_LOCALES,
    localeselector,
    locales_initialize,
)

# renaming names from searx imports ...
from searx.autocomplete import search_autocomplete, backends as autocomplete_backends
from searx.languages import language_codes as languages
from searx.search import SearchWithPlugins, initialize as search_initialize
from searx.network import stream as http_stream, set_context_network_name
from searx.search.checker import get_result as checker_get_result

logger = logger.getChild('webapp')

# check secret_key
if not searx_debug and settings['server']['secret_key'] == 'ultrasecretkey':
    logger.error('server.secret_key is not changed. Please use something else instead of ultrasecretkey.')
    sys.exit(1)

# about static
logger.debug('static directory is %s', settings['ui']['static_path'])
static_files = get_static_files(settings['ui']['static_path'])

# about templates
logger.debug('templates directory is %s', settings['ui']['templates_path'])
default_theme = settings['ui']['default_theme']
templates_path = settings['ui']['templates_path']
themes = get_themes(templates_path)
result_templates = get_result_templates(templates_path)

STATS_SORT_PARAMETERS = {
    'name': (False, 'name', ''),
    'score': (True, 'score', 0),
    'result_count': (True, 'result_count', 0),
    'time': (False, 'total', 0),
    'reliability': (False, 'reliability', 100),
}

# Flask app
app = Flask(__name__, static_folder=settings['ui']['static_path'], template_folder=templates_path)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
app.jinja_env.add_extension('jinja2.ext.loopcontrols')  # pylint: disable=no-member
app.jinja_env.filters['group_engines_in_tab'] = group_engines_in_tab  # pylint: disable=no-member
app.secret_key = settings['server']['secret_key']

babel = Babel(app)

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


class ExtendedRequest(flask.Request):
    """This class is never initialized and only used for type checking."""

    preferences: Preferences
    errors: List[str]
    user_plugins: List[Plugin]
    form: Dict[str, str]
    start_time: float
    render_time: float
    timings: List[Timing]


request = typing.cast(ExtendedRequest, flask.request)


@babel.localeselector
def get_locale():
    locale = localeselector()
    logger.debug("%s uses locale `%s`", urllib.parse.quote(request.url), locale)
    return locale


def _get_browser_language(req, lang_list):
    for lang in req.headers.get("Accept-Language", "en").split(","):
        if ';' in lang:
            lang = lang.split(';')[0]
        if '-' in lang:
            lang_parts = lang.split('-')
            lang = "{}-{}".format(lang_parts[0], lang_parts[-1].upper())
        locale = match_language(lang, lang_list, fallback=None)
        if locale is not None:
            return locale
    return 'en'


def _get_locale_rfc5646(locale):
    """Get locale name for <html lang="...">
    Chrom* browsers don't detect the language when there is a subtag (ie a territory).
    For example "zh-TW" is detected but not "zh-Hant-TW".
    This function returns a locale without the subtag.
    """
    parts = locale.split('-')
    return parts[0].lower() + '-' + parts[-1].upper()


# code-highlighter
@app.template_filter('code_highlighter')
def code_highlighter(codelines, language=None):
    if not language:
        language = 'text'

    try:
        # find lexer by programing language
        lexer = get_lexer_by_name(language, stripall=True)

    except Exception as e:  # pylint: disable=broad-except
        logger.exception(e, exc_info=True)
        # if lexer is not found, using default one
        lexer = get_lexer_by_name('text', stripall=True)

    html_code = ''
    tmp_code = ''
    last_line = None
    line_code_start = None

    # parse lines
    for line, code in codelines:
        if not last_line:
            line_code_start = line

        # new codeblock is detected
        if last_line is not None and last_line + 1 != line:

            # highlight last codepart
            formatter = HtmlFormatter(linenos='inline', linenostart=line_code_start, cssclass="code-highlight")
            html_code = html_code + highlight(tmp_code, lexer, formatter)

            # reset conditions for next codepart
            tmp_code = ''
            line_code_start = line

        # add codepart
        tmp_code += code + '\n'

        # update line
        last_line = line

    # highlight last codepart
    formatter = HtmlFormatter(linenos='inline', linenostart=line_code_start, cssclass="code-highlight")
    html_code = html_code + highlight(tmp_code, lexer, formatter)

    return html_code


def get_result_template(theme_name: str, template_name: str):
    themed_path = theme_name + '/result_templates/' + template_name
    if themed_path in result_templates:
        return themed_path
    return 'result_templates/' + template_name


def custom_url_for(endpoint: str, **values):
    suffix = ""
    if endpoint == 'static' and values.get('filename'):
        file_hash = static_files.get(values['filename'])
        if not file_hash:
            # try file in the current theme
            theme_name = request.preferences.get_value('theme')
            filename_with_theme = "themes/{}/{}".format(theme_name, values['filename'])
            file_hash = static_files.get(filename_with_theme)
            if file_hash:
                values['filename'] = filename_with_theme
        if get_setting('ui.static_use_hash') and file_hash:
            suffix = "?" + file_hash
    if endpoint == 'info' and 'locale' not in values:
        locale = request.preferences.get_value('locale')
        if _INFO_PAGES.get_page(values['pagename'], locale) is None:
            locale = _INFO_PAGES.locale_default
        values['locale'] = locale
    return url_for(endpoint, **values) + suffix


def proxify(url: str):
    if url.startswith('//'):
        url = 'https:' + url

    if not settings.get('result_proxy'):
        return url

    url_params = dict(mortyurl=url)

    if settings['result_proxy'].get('key'):
        url_params['mortyhash'] = hmac.new(settings['result_proxy']['key'], url.encode(), hashlib.sha256).hexdigest()

    return '{0}?{1}'.format(settings['result_proxy']['url'], urlencode(url_params))


def image_proxify(url: str):

    if url.startswith('//'):
        url = 'https:' + url

    if not request.preferences.get_value('image_proxy'):
        return url

    if url.startswith('data:image/'):
        # 50 is an arbitrary number to get only the beginning of the image.
        partial_base64 = url[len('data:image/') : 50].split(';')
        if (
            len(partial_base64) == 2
            and partial_base64[0] in ['gif', 'png', 'jpeg', 'pjpeg', 'webp', 'tiff', 'bmp']
            and partial_base64[1].startswith('base64,')
        ):
            return url
        return None

    if settings.get('result_proxy'):
        return proxify(url)

    h = new_hmac(settings['server']['secret_key'], url.encode())

    return '{0}?{1}'.format(url_for('image_proxy'), urlencode(dict(url=url.encode(), h=h)))


def get_translations():
    return {
        # when there is autocompletion
        'no_item_found': gettext('No item found'),
        # /preferences: the source of the engine description (wikipedata, wikidata, website)
        'Source': gettext('Source'),
        # infinite scroll
        'error_loading_next_page': gettext('Error loading the next page'),
    }


def _get_enable_categories(all_categories: Iterable[str]):
    disabled_engines = request.preferences.engines.get_disabled()
    enabled_categories = set(
        # pylint: disable=consider-using-dict-items
        category
        for engine_name in engines
        for category in engines[engine_name].categories
        if (engine_name, category) not in disabled_engines
    )
    return [x for x in all_categories if x in enabled_categories]


def get_pretty_url(parsed_url: urllib.parse.ParseResult):
    path = parsed_url.path
    path = path[:-1] if len(path) > 0 and path[-1] == '/' else path
    path = unquote(path.replace("/", " › "))
    return [parsed_url.scheme + "://" + parsed_url.netloc, path]


def get_client_settings():
    req_pref = request.preferences
    return {
        'autocomplete_provider': req_pref.get_value('autocomplete'),
        'autocomplete_min': get_setting('search.autocomplete_min'),
        'http_method': req_pref.get_value('method'),
        'infinite_scroll': req_pref.get_value('infinite_scroll'),
        'translations': get_translations(),
        'search_on_category_select': req_pref.plugins.choices['searx.plugins.search_on_category_select'],
        'hotkeys': req_pref.plugins.choices['searx.plugins.vim_hotkeys'],
        'theme_static_path': custom_url_for('static', filename='themes/simple'),
    }


def render(template_name: str, **kwargs):

    kwargs['client_settings'] = str(
        base64.b64encode(
            bytes(
                json.dumps(get_client_settings()),
                encoding='utf-8',
            )
        ),
        encoding='utf-8',
    )

    # values from the HTTP requests
    kwargs['endpoint'] = 'results' if 'q' in kwargs else request.endpoint
    kwargs['cookies'] = request.cookies
    kwargs['errors'] = request.errors

    # values from the preferences
    kwargs['preferences'] = request.preferences
    kwargs['autocomplete'] = request.preferences.get_value('autocomplete')
    kwargs['infinite_scroll'] = request.preferences.get_value('infinite_scroll')
    kwargs['results_on_new_tab'] = request.preferences.get_value('results_on_new_tab')
    kwargs['advanced_search'] = request.preferences.get_value('advanced_search')
    kwargs['query_in_title'] = request.preferences.get_value('query_in_title')
    kwargs['safesearch'] = str(request.preferences.get_value('safesearch'))
    kwargs['theme'] = request.preferences.get_value('theme')
    kwargs['method'] = request.preferences.get_value('method')
    kwargs['categories_as_tabs'] = list(settings['categories_as_tabs'].keys())
    kwargs['categories'] = _get_enable_categories(categories.keys())
    kwargs['OTHER_CATEGORY'] = OTHER_CATEGORY

    # i18n
    kwargs['language_codes'] = [l for l in languages if l[0] in settings['search']['languages']]

    locale = request.preferences.get_value('locale')
    kwargs['locale_rfc5646'] = _get_locale_rfc5646(locale)

    if locale in RTL_LOCALES and 'rtl' not in kwargs:
        kwargs['rtl'] = True
    if 'current_language' not in kwargs:
        kwargs['current_language'] = match_language(
            request.preferences.get_value('language'), settings['search']['languages']
        )

    # values from settings
    kwargs['search_formats'] = [x for x in settings['search']['formats'] if x != 'html']
    kwargs['instance_name'] = get_setting('general.instance_name')
    kwargs['searx_version'] = VERSION_STRING
    kwargs['searx_git_url'] = GIT_URL
    kwargs['get_setting'] = get_setting
    kwargs['get_pretty_url'] = get_pretty_url

    # helpers to create links to other pages
    kwargs['url_for'] = custom_url_for  # override url_for function in templates
    kwargs['image_proxify'] = image_proxify
    kwargs['proxify'] = proxify if settings.get('result_proxy', {}).get('url') else None
    kwargs['proxify_results'] = settings.get('result_proxy', {}).get('proxify_results', True)
    kwargs['get_result_template'] = get_result_template
    kwargs['opensearch_url'] = (
        url_for('opensearch')
        + '?'
        + urlencode(
            {
                'method': request.preferences.get_value('method'),
                'autocomplete': request.preferences.get_value('autocomplete'),
            }
        )
    )

    # scripts from plugins
    kwargs['scripts'] = set()
    for plugin in request.user_plugins:
        for script in plugin.js_dependencies:
            kwargs['scripts'].add(script)

    # styles from plugins
    kwargs['styles'] = set()
    for plugin in request.user_plugins:
        for css in plugin.css_dependencies:
            kwargs['styles'].add(css)

    start_time = default_timer()
    result = render_template('{}/{}'.format(kwargs['theme'], template_name), **kwargs)
    request.render_time += default_timer() - start_time  # pylint: disable=assigning-non-slot

    return result


@app.before_request
def pre_request():
    request.start_time = default_timer()  # pylint: disable=assigning-non-slot
    request.render_time = 0  # pylint: disable=assigning-non-slot
    request.timings = []  # pylint: disable=assigning-non-slot
    request.errors = []  # pylint: disable=assigning-non-slot

    preferences = Preferences(themes, list(categories.keys()), engines, plugins)  # pylint: disable=redefined-outer-name
    user_agent = request.headers.get('User-Agent', '').lower()
    if 'webkit' in user_agent and 'android' in user_agent:
        preferences.key_value_settings['method'].value = 'GET'
    request.preferences = preferences  # pylint: disable=assigning-non-slot

    try:
        preferences.parse_dict(request.cookies)

    except Exception as e:  # pylint: disable=broad-except
        logger.exception(e, exc_info=True)
        request.errors.append(gettext('Invalid settings, please edit your preferences'))

    # merge GET, POST vars
    # request.form
    request.form = dict(request.form.items())  # pylint: disable=assigning-non-slot
    for k, v in request.args.items():
        if k not in request.form:
            request.form[k] = v

    if request.form.get('preferences'):
        preferences.parse_encoded_data(request.form['preferences'])
    else:
        try:
            preferences.parse_dict(request.form)
        except Exception as e:  # pylint: disable=broad-except
            logger.exception(e, exc_info=True)
            request.errors.append(gettext('Invalid settings'))

    # language is defined neither in settings nor in preferences
    # use browser headers
    if not preferences.get_value("language"):
        language = _get_browser_language(request, settings['search']['languages'])
        preferences.parse_dict({"language": language})
        logger.debug('set language %s (from browser)', preferences.get_value("language"))

    # locale is defined neither in settings nor in preferences
    # use browser headers
    if not preferences.get_value("locale"):
        locale = _get_browser_language(request, LOCALE_NAMES.keys())
        preferences.parse_dict({"locale": locale})
        logger.debug('set locale %s (from browser)', preferences.get_value("locale"))

    # request.user_plugins
    request.user_plugins = []  # pylint: disable=assigning-non-slot
    allowed_plugins = preferences.plugins.get_enabled()
    disabled_plugins = preferences.plugins.get_disabled()
    for plugin in plugins:
        if (plugin.default_on and plugin.id not in disabled_plugins) or plugin.id in allowed_plugins:
            request.user_plugins.append(plugin)


@app.after_request
def add_default_headers(response: flask.Response):
    # set default http headers
    for header, value in settings['server']['default_http_headers'].items():
        if header in response.headers:
            continue
        response.headers[header] = value
    return response


@app.after_request
def post_request(response: flask.Response):
    total_time = default_timer() - request.start_time
    timings_all = [
        'total;dur=' + str(round(total_time * 1000, 3)),
        'render;dur=' + str(round(request.render_time * 1000, 3)),
    ]
    if len(request.timings) > 0:
        timings = sorted(request.timings, key=lambda t: t.total)
        timings_total = [
            'total_' + str(i) + '_' + t.engine + ';dur=' + str(round(t.total * 1000, 3)) for i, t in enumerate(timings)
        ]
        timings_load = [
            'load_' + str(i) + '_' + t.engine + ';dur=' + str(round(t.load * 1000, 3))
            for i, t in enumerate(timings)
            if t.load
        ]
        timings_all = timings_all + timings_total + timings_load
    response.headers.add('Server-Timing', ', '.join(timings_all))
    return response


def index_error(output_format: str, error_message: str):
    if output_format == 'json':
        return Response(json.dumps({'error': error_message}), mimetype='application/json')
    if output_format == 'csv':
        response = Response('', mimetype='application/csv')
        cont_disp = 'attachment;Filename=searx.csv'
        response.headers.add('Content-Disposition', cont_disp)
        return response

    if output_format == 'rss':
        response_rss = render(
            'opensearch_response_rss.xml',
            results=[],
            q=request.form['q'] if 'q' in request.form else '',
            number_of_results=0,
            error_message=error_message,
        )
        return Response(response_rss, mimetype='text/xml')

    # html
    request.errors.append(gettext('search error'))
    return render(
        # fmt: off
        'index.html',
        selected_categories=get_selected_categories(request.preferences, request.form),
        # fmt: on
    )


@app.route('/', methods=['GET', 'POST'])
def index():
    """Render index page."""

    # redirect to search if there's a query in the request
    if request.form.get('q'):
        query = ('?' + request.query_string.decode()) if request.query_string else ''
        return redirect(url_for('search') + query, 308)

    return render(
        # fmt: off
        'index.html',
        selected_categories=get_selected_categories(request.preferences, request.form),
        current_locale = request.preferences.get_value("locale"),
        # fmt: on
    )


@app.route('/healthz', methods=['GET'])
def health():
    return Response('OK', mimetype='text/plain')


@app.route('/search', methods=['GET', 'POST'])
def search():
    """Search query in q and return results.

    Supported outputs: html, json, csv, rss.
    """
    # pylint: disable=too-many-locals, too-many-return-statements, too-many-branches
    # pylint: disable=too-many-statements

    # output_format
    output_format = request.form.get('format', 'html')
    if output_format not in OUTPUT_FORMATS:
        output_format = 'html'

    if output_format not in settings['search']['formats']:
        flask.abort(403)

    # check if there is query (not None and not an empty string)
    if not request.form.get('q'):
        if output_format == 'html':
            return render(
                # fmt: off
                'index.html',
                selected_categories=get_selected_categories(request.preferences, request.form),
                # fmt: on
            )
        return index_error(output_format, 'No query'), 400

    # search
    search_query = None
    raw_text_query = None
    result_container = None
    try:
        search_query, raw_text_query, _, _ = get_search_query_from_webapp(request.preferences, request.form)
        # search = Search(search_query) #  without plugins
        search = SearchWithPlugins(search_query, request.user_plugins, request)  # pylint: disable=redefined-outer-name

        result_container = search.search()

    except SearxParameterException as e:
        logger.exception('search error: SearxParameterException')
        return index_error(output_format, e.message), 400
    except Exception as e:  # pylint: disable=broad-except
        logger.exception(e, exc_info=True)
        return index_error(output_format, gettext('search error')), 500

    # results
    results = result_container.get_ordered_results()
    number_of_results = result_container.results_number()
    if number_of_results < result_container.results_length():
        number_of_results = 0

    # checkin for a external bang
    if result_container.redirect_url:
        return redirect(result_container.redirect_url)

    # Server-Timing header
    request.timings = result_container.get_timings()  # pylint: disable=assigning-non-slot

    current_template = None
    previous_result = None

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
                        result['publishedDate'] = gettext('{hours} hour(s), {minutes} minute(s) ago').format(
                            hours=hours, minutes=minutes
                        )
                else:
                    result['publishedDate'] = format_date(result['publishedDate'])

        # set result['open_group'] = True when the template changes from the previous result
        # set result['close_group'] = True when the template changes on the next result
        if current_template != result.get('template'):
            result['open_group'] = True
            if previous_result:
                previous_result['close_group'] = True  # pylint: disable=unsupported-assignment-operation
        current_template = result.get('template')
        previous_result = result

    if previous_result:
        previous_result['close_group'] = True

    if output_format == 'json':
        x = {
            'query': search_query.query,
            'number_of_results': number_of_results,
            'results': results,
            'answers': list(result_container.answers),
            'corrections': list(result_container.corrections),
            'infoboxes': result_container.infoboxes,
            'suggestions': list(result_container.suggestions),
            'unresponsive_engines': __get_translated_errors(result_container.unresponsive_engines),
        }
        response = json.dumps(x, default=lambda item: list(item) if isinstance(item, set) else item)
        return Response(response, mimetype='application/json')

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
        response = Response(csv.stream.read(), mimetype='application/csv')
        cont_disp = 'attachment;Filename=searx_-_{0}.csv'.format(search_query.query)
        response.headers.add('Content-Disposition', cont_disp)
        return response

    if output_format == 'rss':
        response_rss = render(
            'opensearch_response_rss.xml',
            results=results,
            answers=result_container.answers,
            corrections=result_container.corrections,
            suggestions=result_container.suggestions,
            q=request.form['q'],
            number_of_results=number_of_results,
        )
        return Response(response_rss, mimetype='text/xml')

    # HTML output format

    # suggestions: use RawTextQuery to get the suggestion URLs with the same bang
    suggestion_urls = list(
        map(
            lambda suggestion: {'url': raw_text_query.changeQuery(suggestion).getFullQuery(), 'title': suggestion},
            result_container.suggestions,
        )
    )

    correction_urls = list(
        map(
            lambda correction: {'url': raw_text_query.changeQuery(correction).getFullQuery(), 'title': correction},
            result_container.corrections,
        )
    )

    return render(
        # fmt: off
        'results.html',
        results = results,
        q=request.form['q'],
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
        current_locale = request.preferences.get_value("locale"),
        current_language = match_language(
            search_query.lang,
            settings['search']['languages'],
            fallback=request.preferences.get_value("language")
        ),
        timeout_limit = request.form.get('timeout_limit', None)
        # fmt: on
    )


def __get_translated_errors(unresponsive_engines: Iterable[UnresponsiveEngine]):
    translated_errors = []

    # make a copy unresponsive_engines to avoid "RuntimeError: Set changed size
    # during iteration" it happens when an engine modifies the ResultContainer
    # after the search_multiple_requests method has stopped waiting

    for unresponsive_engine in unresponsive_engines:
        error_user_text = exception_classname_to_text.get(unresponsive_engine.error_type)
        if not error_user_text:
            error_user_text = exception_classname_to_text[None]
        error_msg = gettext(error_user_text)
        if unresponsive_engine.suspended:
            error_msg = gettext('Suspended') + ': ' + error_msg
        translated_errors.append((unresponsive_engine.engine, error_msg))

    return sorted(translated_errors, key=lambda e: e[0])


@app.route('/about', methods=['GET'])
def about():
    """Redirect to about page"""
    # custom_url_for is going to add the locale
    return redirect(custom_url_for('info', pagename='about'))


@app.route('/info/<locale>/<pagename>', methods=['GET'])
def info(pagename, locale):
    """Render page of online user documentation"""
    page = _INFO_PAGES.get_page(pagename, locale)
    if page is None:
        flask.abort(404)

    user_locale = request.preferences.get_value('locale')
    return render(
        'info.html',
        all_pages=_INFO_PAGES.iter_pages(user_locale, fallback_to_default=True),
        active_page=page,
        active_pagename=pagename,
    )


@app.route('/autocompleter', methods=['GET', 'POST'])
def autocompleter():
    """Return autocompleter results"""

    # run autocompleter
    results = []

    # set blocked engines
    disabled_engines = request.preferences.engines.get_disabled()

    # parse query
    raw_text_query = RawTextQuery(request.form.get('q', ''), disabled_engines)
    sug_prefix = raw_text_query.getQuery()

    # normal autocompletion results only appear if no inner results returned
    # and there is a query part
    if len(raw_text_query.autocomplete_list) == 0 and len(sug_prefix) > 0:

        # get language from cookie
        language = request.preferences.get_value('language')
        if not language or language == 'all':
            language = 'en'
        else:
            language = language.split('-')[0]

        # run autocompletion
        raw_results = search_autocomplete(request.preferences.get_value('autocomplete'), sug_prefix, language)
        for result in raw_results:
            # attention: this loop will change raw_text_query object and this is
            # the reason why the sug_prefix was stored before (see above)
            if result != sug_prefix:
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

    suggestions = escape(suggestions, False)
    return Response(suggestions, mimetype=mimetype)


@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    """Render preferences page && save user preferences"""

    # pylint: disable=too-many-locals, too-many-return-statements, too-many-branches
    # pylint: disable=too-many-statements

    # save preferences using the link the /preferences?preferences=...&save=1
    if request.args.get('save') == '1':
        resp = make_response(redirect(url_for('index', _external=True)))
        return request.preferences.save(resp)

    # save preferences
    if request.method == 'POST':
        resp = make_response(redirect(url_for('index', _external=True)))
        try:
            request.preferences.parse_form(request.form)
        except ValidationException:
            request.errors.append(gettext('Invalid settings, please edit your preferences'))
            return resp
        return request.preferences.save(resp)

    # render preferences
    image_proxy = request.preferences.get_value('image_proxy')  # pylint: disable=redefined-outer-name
    disabled_engines = request.preferences.engines.get_disabled()
    allowed_plugins = request.preferences.plugins.get_enabled()

    # stats for preferences page
    filtered_engines = dict(filter(lambda kv: request.preferences.validate_token(kv[1]), engines.items()))

    engines_by_category = {}

    for c in categories:  # pylint: disable=consider-using-dict-items
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
            'supports_selected_language': _is_selected_language_supported(e, request.preferences),
            'result_count': result_count,
        }
    # end of stats

    # reliabilities
    reliabilities = {}
    engine_errors = get_engine_errors(filtered_engines)
    checker_results = checker_get_result()
    checker_results = (
        checker_results['engines'] if checker_results['status'] == 'ok' and 'engines' in checker_results else {}
    )
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
            # pylint: disable=consider-using-generator
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
        supports_selected_language = _is_selected_language_supported(e, request.preferences)
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
        # fmt: off
        'preferences.html',
        selected_categories = get_selected_categories(request.preferences, request.form),
        locales = LOCALE_NAMES,
        current_locale = request.preferences.get_value("locale"),
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
        current_doi_resolver = get_doi_resolver(request.preferences),
        allowed_plugins = allowed_plugins,
        preferences_url_params = request.preferences.get_as_url_params(),
        locked_preferences = settings['preferences']['lock'],
        preferences = True
        # fmt: on
    )


def _is_selected_language_supported(engine, preferences: Preferences):  # pylint: disable=redefined-outer-name
    language = preferences.get_value('language')
    if language == 'all':
        return True
    x = match_language(
        language, getattr(engine, 'supported_languages', []), getattr(engine, 'language_aliases', {}), None
    )
    return bool(x)


@app.route('/image_proxy', methods=['GET'])
def image_proxy():
    # pylint: disable=too-many-return-statements, too-many-branches

    url = request.args.get('url')
    if not url:
        return '', 400

    if not is_hmac_of(settings['server']['secret_key'], url.encode(), request.args.get('h', '')):
        return '', 400

    maximum_size = 5 * 1024 * 1024
    forward_resp = False
    resp = None
    try:
        request_headers = {
            'User-Agent': gen_useragent(),
            'Accept': 'image/webp,*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Sec-GPC': '1',
            'DNT': '1',
        }
        set_context_network_name('image_proxy')
        resp, stream = http_stream(method='GET', url=url, headers=request_headers, allow_redirects=True)
        content_length = resp.headers.get('Content-Length')
        if content_length and content_length.isdigit() and int(content_length) > maximum_size:
            return 'Max size', 400

        if resp.status_code != 200:
            logger.debug('image-proxy: wrong response code: %i', resp.status_code)
            if resp.status_code >= 400:
                return '', resp.status_code
            return '', 400

        if not resp.headers.get('Content-Type', '').startswith('image/') and not resp.headers.get(
            'Content-Type', ''
        ).startswith('binary/octet-stream'):
            logger.debug('image-proxy: wrong content-type: %s', resp.headers.get('Content-Type', ''))
            return '', 400

        forward_resp = True
    except httpx.HTTPError:
        logger.exception('HTTP error')
        return '', 400
    finally:
        if resp and not forward_resp:
            # the code is about to return an HTTP 400 error to the browser
            # we make sure to close the response between searxng and the HTTP server
            try:
                resp.close()
            except httpx.HTTPError:
                logger.exception('HTTP error on closing')

    def close_stream():
        nonlocal resp, stream
        try:
            if resp:
                resp.close()
            del resp
            del stream
        except httpx.HTTPError as e:
            logger.debug('Exception while closing response', e)

    try:
        headers = dict_subset(resp.headers, {'Content-Type', 'Content-Encoding', 'Content-Length', 'Length'})
        response = Response(stream, mimetype=resp.headers['Content-Type'], headers=headers, direct_passthrough=True)
        response.call_on_close(close_stream)
        return response
    except httpx.HTTPError:
        close_stream()
        return '', 400


@app.route('/engine_descriptions.json', methods=['GET'])
def engine_descriptions():
    locale = get_locale().split('_')[0]
    result = ENGINE_DESCRIPTIONS['en'].copy()
    if locale != 'en':
        for engine, description in ENGINE_DESCRIPTIONS.get(locale, {}).items():
            result[engine] = description
    for engine, description in result.items():
        if len(description) == 2 and description[1] == 'ref':
            ref_engine, ref_lang = description[0].split(':')
            description = ENGINE_DESCRIPTIONS[ref_lang][ref_engine]
        if isinstance(description, str):
            description = [description, 'wikipedia']
        result[engine] = description

    # overwrite by about:description (from settings)
    for engine_name, engine_mod in engines.items():
        descr = getattr(engine_mod, 'about', {}).get('description', None)
        if descr is not None:
            result[engine_name] = [descr, "SearXNG config"]

    return jsonify(result)


@app.route('/stats', methods=['GET'])
def stats():
    """Render engine statistics page."""
    sort_order = request.args.get('sort', default='name', type=str)
    selected_engine_name = request.args.get('engine', default=None, type=str)

    filtered_engines = dict(filter(lambda kv: request.preferences.validate_token(kv[1]), engines.items()))
    if selected_engine_name:
        if selected_engine_name not in filtered_engines:
            selected_engine_name = None
        else:
            filtered_engines = [selected_engine_name]

    checker_results = checker_get_result()
    checker_results = (
        checker_results['engines'] if checker_results['status'] == 'ok' and 'engines' in checker_results else {}
    )

    engine_stats = get_engines_stats(filtered_engines)
    engine_reliabilities = get_reliabilities(filtered_engines, checker_results)

    if sort_order not in STATS_SORT_PARAMETERS:
        sort_order = 'name'

    reverse, key_name, default_value = STATS_SORT_PARAMETERS[sort_order]

    def get_key(engine_stat):
        reliability = engine_reliabilities.get(engine_stat['name'], {}).get('reliablity', 0)
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
        # fmt: off
        'stats.html',
        sort_order = sort_order,
        engine_stats = engine_stats,
        engine_reliabilities = engine_reliabilities,
        selected_engine_name = selected_engine_name,
        searx_git_branch = GIT_BRANCH,
        # fmt: on
    )


@app.route('/stats/errors', methods=['GET'])
def stats_errors():
    filtered_engines = dict(filter(lambda kv: request.preferences.validate_token(kv[1]), engines.items()))
    result = get_engine_errors(filtered_engines)
    return jsonify(result)


@app.route('/stats/checker', methods=['GET'])
def stats_checker():
    result = checker_get_result()
    return jsonify(result)


@app.route('/robots.txt', methods=['GET'])
def robots():
    return Response(
        """User-agent: *
Allow: /info/en/about
Disallow: /stats
Disallow: /image_proxy
Disallow: /preferences
Disallow: /*?*q=*
""",
        mimetype='text/plain',
    )


@app.route('/opensearch.xml', methods=['GET'])
def opensearch():
    method = 'post'

    if request.preferences.get_value('method') == 'GET':
        method = 'get'

    # chrome/chromium only supports HTTP GET....
    if request.headers.get('User-Agent', '').lower().find('webkit') >= 0:
        method = 'get'

    autocomplete = request.preferences.get_value('autocomplete')

    ret = render('opensearch.xml', opensearch_method=method, autocomplete=autocomplete)

    resp = Response(response=ret, status=200, mimetype="application/opensearchdescription+xml")
    return resp


@app.route('/favicon.ico')
def favicon():
    theme = request.preferences.get_value("theme")
    return send_from_directory(
        os.path.join(app.root_path, settings['ui']['static_path'], 'themes', theme, 'img'),
        'favicon.png',
        mimetype='image/vnd.microsoft.icon',
    )


@app.route('/clear_cookies')
def clear_cookies():
    resp = make_response(redirect(url_for('index', _external=True)))
    for cookie_name in request.cookies:
        resp.delete_cookie(cookie_name)
    return resp


@app.route('/config')
def config():
    """Return configuration in JSON format."""
    _engines = []
    for name, engine in engines.items():
        if not request.preferences.validate_token(engine):
            continue

        supported_languages = engine.supported_languages
        if isinstance(engine.supported_languages, dict):
            supported_languages = list(engine.supported_languages.keys())

        _engines.append(
            {
                'name': name,
                'categories': engine.categories,
                'shortcut': engine.shortcut,
                'enabled': not engine.disabled,
                'paging': engine.paging,
                'language_support': engine.language_support,
                'supported_languages': supported_languages,
                'safesearch': engine.safesearch,
                'time_range_support': engine.time_range_support,
                'timeout': engine.timeout,
            }
        )

    _plugins = []
    for _ in plugins:
        _plugins.append({'name': _.name, 'enabled': _.default_on})

    return jsonify(
        {
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
                'PRIVACYPOLICY_URL': get_setting('general.privacypolicy_url'),
                'CONTACT_URL': get_setting('general.contact_url'),
                'GIT_URL': GIT_URL,
                'GIT_BRANCH': GIT_BRANCH,
                'DOCS_URL': get_setting('brand.docs_url'),
            },
            'doi_resolvers': list(settings['doi_resolvers'].keys()),
            'default_doi_resolver': settings['default_doi_resolver'],
        }
    )


@app.errorhandler(404)
def page_not_found(_e):
    return render('404.html'), 404


# see https://flask.palletsprojects.com/en/1.1.x/cli/
# True if "FLASK_APP=searx/webapp.py FLASK_ENV=development flask run"
flask_run_development = (
    os.environ.get("FLASK_APP") is not None and os.environ.get("FLASK_ENV") == 'development' and is_flask_run_cmdline()
)

# True if reload feature is activated of werkzeug, False otherwise (including uwsgi, etc..)
#  __name__ != "__main__" if searx.webapp is imported (make test, make docs, uwsgi...)
# see run() at the end of this file : searx_debug activates the reload feature.
werkzeug_reloader = flask_run_development or (searx_debug and __name__ == "__main__")

# initialize the engines except on the first run of the werkzeug server.
if not werkzeug_reloader or (werkzeug_reloader and os.environ.get("WERKZEUG_RUN_MAIN") == "true"):
    locales_initialize()
    _INFO_PAGES = infopage.InfoPageSet()
    plugin_initialize(app)
    search_initialize(enable_checker=True, check_network=True, enable_metrics=settings['general']['enable_metrics'])


def run():
    logger.debug('starting webserver on %s:%s', settings['server']['bind_address'], settings['server']['port'])
    app.run(
        debug=searx_debug,
        use_debugger=searx_debug,
        port=settings['server']['port'],
        host=settings['server']['bind_address'],
        threaded=True,
        extra_files=[get_default_settings_path()],
    )


application = app
patch_application(app)

if __name__ == "__main__":
    run()
