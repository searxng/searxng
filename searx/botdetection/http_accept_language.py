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

from typing import Optional, Tuple
import flask

from searx.tools import config


def filter_request(request: flask.Request, cfg: config.Config) -> Optional[Tuple[int, str]]:
    if request.headers.get('Accept-Language', '').strip() == '':
        return 429, "bot detected, missing HTTP header Accept-Language"
    return None
