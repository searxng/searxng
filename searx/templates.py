import os
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlsplit


import jinja2
import babel.support

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter  # pylint: disable=no-name-in-module

from starlette.requests import Request
from starlette.templating import Jinja2Templates
from starlette_context import context
from starlette.routing import NoMatchFound
from starlette_i18n import i18n

from searx import logger, settings
from searx.webutils import (
    get_static_files,
    get_result_templates,
    get_themes,
)


# about static
logger.debug('static directory is %s', settings['ui']['static_path'])
static_files = get_static_files(settings['ui']['static_path'])

# about templates
logger.debug('templates directory is %s', settings['ui']['templates_path'])
default_theme = settings['ui']['default_theme']
templates_path = settings['ui']['templates_path']
themes = get_themes(templates_path)
result_templates = get_result_templates(templates_path)
global_favicons = []
for indice, theme in enumerate(themes):
    global_favicons.append([])
    theme_img_path = os.path.join(settings['ui']['static_path'], 'themes', theme, 'img', 'icons')
    for (dirpath, dirnames, filenames) in os.walk(theme_img_path):
        global_favicons[indice].extend(filenames)


def get_current_theme_name(request: Request, override: Optional[str] =None) -> str:
    """Returns theme name.

    Checks in this order:
    1. override
    2. cookies
    3. settings"""

    if override and (override in themes or override == '__common__'):
        return override
    theme_name = request.query_params.get('theme', context.preferences.get_value('theme'))  # pylint: disable=no-member
    if theme_name not in themes:
        theme_name = default_theme
    return theme_name


def get_result_template(theme_name: str, template_name: str) -> str:
    themed_path = theme_name + '/result_templates/' + template_name
    if themed_path in result_templates:
        return themed_path
    return 'result_templates/' + template_name


# code-highlighter
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

    # parse lines
    for line, code in codelines:
        if not last_line:
            line_code_start = line

        # new codeblock is detected
        if last_line is not None and\
           last_line + 1 != line:

            # highlight last codepart
            formatter = HtmlFormatter(
                linenos='inline', linenostart=line_code_start, cssclass="code-highlight"
            )
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


class I18NTemplates(Jinja2Templates):
    """Custom Jinja2Templates with i18n support
    """

    @staticmethod
    def url_for_theme(endpoint: str, override_theme=None, **values):
        request = context.request  # pylint: disable=no-member

        # starlette migration
        if '_external' in values:
            del values['_external']
        if 'filename' in values:
            values['path'] = values['filename']
            del values['filename']

        #
        if endpoint == 'static' and values.get('path'):
            theme_name = get_current_theme_name(request, override=override_theme)
            filename_with_theme = "themes/{}/{}".format(theme_name, values['path'])
            if filename_with_theme in static_files:
                values['path'] = filename_with_theme
            return request.url_for(endpoint, **values)
        try:
            url_for_args = {}
            for k in ('path', 'filename'):
                if k in values:
                    v = values.pop(k)
                    url_for_args[k] = v
            url = request.url_for(endpoint, **url_for_args)
            _url = urlsplit(url)
            _query = parse_qs(_url.query)
            _query.update(values)
            querystr = urlencode(_query, doseq=True)
            return _url._replace(query=querystr).geturl()
            # if anchor is not None:
            #     rv += f"#{url_quote(anchor)}"
        except NoMatchFound as e:
            error_message = "url_for, endpoint='%s' not found (values=%s)" % (endpoint, str(values))
            logger.error(error_message)
            context.errors.append(error_message)  # pylint: disable=no-member
            raise e

    @staticmethod
    def ugettext(message):
        translations = i18n.get_locale().translations
        if isinstance(message, babel.support.LazyProxy):
            message = message.value
        return translations.ugettext(message)

    @staticmethod
    def ungettext(*args):
        translations = i18n.get_locale().translations
        return translations.ungettext(*args)

    def _create_env(self, directory: str) -> "jinja2.Environment":
        loader = jinja2.FileSystemLoader(directory)
        env = jinja2.Environment(
            loader=loader,
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
            auto_reload=False,
            extensions=[
                'jinja2.ext.loopcontrols',
                'jinja2.ext.i18n'
            ],
        )
        env.filters["code_highlighter"] = code_highlighter
        env.globals["url_for"] = I18NTemplates.url_for_theme
        env.install_gettext_callables(  # pylint: disable=no-member
            I18NTemplates.ugettext,
            I18NTemplates.ungettext,
            newstyle=True
        )
        return env
