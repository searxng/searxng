# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from urllib.parse import urlparse

from werkzeug.serving import WSGIRequestHandler

from searx import settings


class ReverseProxyPathFix:
    '''Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.

    http://flask.pocoo.org/snippets/35/

    In nginx:
    location /myprefix {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Script-Name /myprefix;
        }

    :param wsgi_app: the WSGI application
    '''

    # pylint: disable=too-few-public-methods

    def __init__(self, wsgi_app):

        self.wsgi_app = wsgi_app
        self.script_name = None
        self.scheme = None
        self.server = None

        if settings['server']['base_url']:

            # If base_url is specified, then these values from are given
            # preference over any Flask's generics.

            base_url = urlparse(settings['server']['base_url'])
            self.script_name = base_url.path
            if self.script_name.endswith('/'):
                # remove trailing slash to avoid infinite redirect on the index
                # see https://github.com/searx/searx/issues/2729
                self.script_name = self.script_name[:-1]
            self.scheme = base_url.scheme
            self.server = base_url.netloc

    def __call__(self, environ, start_response):
        script_name = self.script_name or environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name) :]

        scheme = self.scheme or environ.get('HTTP_X_SCHEME') or environ.get('HTTP_X_FORWARDED_PROTO')
        if scheme:
            environ['wsgi.url_scheme'] = scheme

        server = self.server or environ.get('HTTP_X_FORWARDED_HOST', '')
        if server:
            environ['HTTP_HOST'] = server
        return self.wsgi_app(environ, start_response)


def patch_application(app):
    # serve pages with HTTP/1.1
    WSGIRequestHandler.protocol_version = "HTTP/{}".format(settings['server']['http_protocol_version'])
    # patch app to handle non root url-s behind proxy
    app.wsgi_app = ReverseProxyPathFix(app.wsgi_app)
