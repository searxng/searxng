# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Method ``http_accept_encoding``
-------------------------------

The ``http_accept_encoding`` method evaluates a request as the request of a
bot if the Accept-Encoding_ header ..

- did not contain ``gzip`` AND ``deflate`` (if both values are missed)
- did not contain ``text/html``

.. _Accept-Encoding:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept-Encoding

"""


from ipaddress import (
    IPv4Network,
    IPv6Network,
)

import werkzeug
import flask

from . import config
from ._helpers import too_many_requests


def filter_request(
    network: IPv4Network | IPv6Network,
    request: flask.Request,
    cfg: config.Config,  # pylint: disable=unused-argument
) -> werkzeug.Response | None:

    accept_list = [l.strip() for l in request.headers.get('Accept-Encoding', '').split(',')]
    if not ('gzip' in accept_list or 'deflate' in accept_list):
        return too_many_requests(network, "HTTP header Accept-Encoding did not contain gzip nor deflate")
    return None
