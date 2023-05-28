# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
Method ``http_accept_language``
-------------------------------

The ``http_accept_language`` method evaluates a request as the request of a bot
if the Accept-Language_ header is unset.

.. _Accept-Language:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent

"""
# pylint: disable=unused-argument

from typing import Optional
import flask
import werkzeug

from searx.tools import config
from ._helpers import too_many_requests


def filter_request(request: flask.Request, cfg: config.Config) -> Optional[werkzeug.Response]:
    if request.headers.get('Accept-Language', '').strip() == '':
        return too_many_requests(request, "missing HTTP header Accept-Language")
    return None
