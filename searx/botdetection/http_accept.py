# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
Method ``http_accept``
----------------------

The ``http_accept`` method evaluates a request as the request of a bot if the
Accept_ header ..

- did not contain ``text/html``

.. _Accept:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept

"""
# pylint: disable=unused-argument

from typing import Optional
import flask
import werkzeug

from searx.tools import config
from ._helpers import too_many_requests


def filter_request(request: flask.Request, cfg: config.Config) -> Optional[werkzeug.Response]:
    if 'text/html' not in request.accept_mimetypes:
        return too_many_requests(request, "HTTP header Accept did not contain text/html")
    return None
