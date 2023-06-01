# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
Method ``http_connection``
--------------------------

The ``http_connection`` method evaluates a request as the request of a bot if
the Connection_ header is set to ``close``.

.. _Connection:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Connection

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

    if request.headers.get('Connection', '').strip() == 'close':
        return too_many_requests(network, "HTTP header 'Connection=close")
    return None
