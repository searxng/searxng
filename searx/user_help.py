from typing import Dict
import os.path
import pkg_resources

import flask

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
    for filename in pkg_resources.resource_listdir(__name__, 'help'):
        rootname, ext = os.path.splitext(filename)
        if ext != '.html':
            continue

        text = pkg_resources.resource_string(__name__, 'help/' + filename).decode()

        base_url = get_setting('server.base_url') or None
        # we specify base_url so that url_for works for base_urls that have a non-root path

        with app.test_request_context(base_url=base_url):
            # the request context is needed for Flask's url_for
            # (otherwise we'd need to set app.config['SERVER_NAME'],
            # which we don't want)

            interpolated = flask.render_template_string(text, get_setting=get_setting, searx_git_url=GIT_URL)

            HELP[rootname] = interpolated
