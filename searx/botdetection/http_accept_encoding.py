# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
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
# pylint: disable=unused-argument

from typing import Optional, Tuple
import flask

from searx.tools import config


def filter_request(request: flask.Request, cfg: config.Config) -> Optional[Tuple[int, str]]:
    accept_list = [l.strip() for l in request.headers.get('Accept-Encoding', '').split(',')]
    if not ('gzip' in accept_list or 'deflate' in accept_list):
        return 429, "bot detected, HTTP header Accept-Encoding did not contain gzip nor deflate"
    return None
