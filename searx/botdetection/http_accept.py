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

from typing import Optional, Tuple
import flask


def filter_request(request: flask.Request) -> Optional[Tuple[int, str]]:
    if 'text/html' not in request.accept_mimetypes:
        return 429, "bot detected, HTTP header Accept did not contain text/html"
    return None
