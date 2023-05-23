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


from typing import Optional, Tuple
import flask


def filter_request(request: flask.Request) -> Optional[Tuple[int, str]]:
    if request.headers.get('Connection', '').strip() == 'close':
        return 429, "bot detected, HTTP header 'Connection=close'"
    return None
