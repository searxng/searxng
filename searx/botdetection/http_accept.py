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

from __future__ import annotations
from ipaddress import (
    IPv4Network,
    IPv6Network,
)

import flask
import werkzeug

from searx.tools import config
from ._helpers import too_many_requests


def filter_request(
    network: IPv4Network | IPv6Network,
    request: flask.Request,
    cfg: config.Config,
) -> werkzeug.Response | None:

    if 'text/html' not in request.accept_mimetypes:
        return too_many_requests(network, "HTTP header Accept did not contain text/html")
    return None
