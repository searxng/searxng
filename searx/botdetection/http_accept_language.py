# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Method ``http_accept_language``
-------------------------------

The ``http_accept_language`` method evaluates a request as the request of a bot
if the Accept-Language_ header is unset.

.. _Accept-Language:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent

"""

from __future__ import annotations
from ipaddress import (
    IPv4Network,
    IPv6Network,
)

import werkzeug

from searx.extended_types import SXNG_Request

from . import config
from ._helpers import too_many_requests


def filter_request(
    network: IPv4Network | IPv6Network,
    request: SXNG_Request,
    cfg: config.Config,  # pylint: disable=unused-argument
) -> werkzeug.Response | None:
    if request.headers.get('Accept-Language', '').strip() == '':
        return too_many_requests(network, "missing HTTP header Accept-Language")
    return None
