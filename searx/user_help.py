from typing import Dict
import os.path
import pkg_resources

import flask
from flask.helpers import url_for
import mistletoe

from . import get_setting
from .version import GIT_URL

HELP: Dict[str, str] = {}
""" Maps a filename under help/ without the file extension to the rendered HTML. """


def render(app: flask.Flask):
    """
    Renders the user documentation. Must be called after all Flask routes have been
    registered, because the documentation might try to link to them with Flask's `url_for`.

    We render the user documentation once on startup to improve performance.
    """

    link_targets = {
        'brand.git_url': GIT_URL,
        'brand.public_instances': get_setting('brand.public_instances'),
        'brand.docs_url': get_setting('brand.docs_url'),
    }

    base_url = get_setting('server.base_url') or None
    # we specify base_url so that url_for works for base_urls that have a non-root path

    with app.test_request_context(base_url=base_url):
        link_targets['url_for:index'] = url_for('index')
        link_targets['url_for:preferences'] = url_for('preferences')
        link_targets['url_for:stats'] = url_for('stats')

    define_link_targets = ''.join(f'[{name}]: {url}\n' for name, url in link_targets.items())

    for filename in pkg_resources.resource_listdir(__name__, 'help'):
        rootname, ext = os.path.splitext(filename)

        if ext != '.md':
            continue

        markdown = pkg_resources.resource_string(__name__, 'help/' + filename).decode()
        markdown = define_link_targets + markdown
        HELP[rootname] = mistletoe.markdown(markdown)
