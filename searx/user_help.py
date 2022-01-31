# pyright: basic
from typing import Dict, NamedTuple
import pkg_resources
import string
import sys

import flask
from flask.helpers import url_for
import mistletoe

from . import get_setting
from .version import GIT_URL


class HelpPage(NamedTuple):
    title: str
    content: str


# Whenever a new .md file is added to help/ it needs to be added here
_TOC = (
    'about',
    'search-syntax',
)

PAGES: Dict[str, HelpPage] = {}
""" Maps a filename under help/ without the file extension to the rendered page. """


class Template(string.Template):
    idpattern = '(:?[a-z._:]+)'


def render(markdown: str, variables=Dict[str, str], filename='') -> HelpPage:
    first_line, markdown = markdown.split('\n', maxsplit=1)
    assert first_line.startswith('# ')

    try:
        markdown = Template(markdown).substitute(variables)
    except KeyError as e:
        print('[FATAL ERROR] undefined variable ${} in {}'.format(e.args[0], filename))
        print('available variables are:')
        for key in variables:
            print('\t' + key)
        sys.exit(1)

    content: str = mistletoe.markdown(markdown)
    return HelpPage(title=first_line.strip('# '), content=content)


def get_variables(app: flask.Flask):
    variables = {
        'brand.git_url': GIT_URL,
        'brand.public_instances': get_setting('brand.public_instances'),
        'brand.docs_url': get_setting('brand.docs_url'),
    }

    base_url = get_setting('server.base_url') or None
    # we specify base_url so that url_for works for base_urls that have a non-root path

    with app.test_request_context(base_url=base_url):
        variables['index'] = url_for('index')
        variables['preferences'] = url_for('preferences')
        variables['stats'] = url_for('stats')
        variables['search'] = url_for('search')

    return variables


def initialize(app: flask.Flask):
    """
    Renders the user documentation. Must be called after all Flask routes have been
    registered, because the documentation might try to link to them with Flask's `url_for`.

    We render the user documentation once on startup to improve performance.
    """

    variables = get_variables(app)

    for pagename in _TOC:
        filename = 'help/en/' + pagename + '.md'
        file_content = pkg_resources.resource_string(__name__, filename).decode()

        if pagename == 'about':
            try:
                file_content += pkg_resources.resource_string(
                    __name__, 'templates/__common__/aboutextend.html'
                ).decode()
            except FileNotFoundError:
                pass
        PAGES[pagename] = render(file_content, variables, filename=filename)
