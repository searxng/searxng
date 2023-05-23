# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
""".. _limiter src:

Limiter
=======

.. sidebar:: info

   The limiter requires a :ref:`Redis <settings redis>` database.

Bot protection / IP rate limitation.  The intention of rate limitation is to
limit suspicious requests from an IP.  The motivation behind this is the fact
that SearXNG passes through requests from bots and is thus classified as a bot
itself.  As a result, the SearXNG engine then receives a CAPTCHA or is blocked
by the search engine (the origin) in some other way.

To avoid blocking, the requests from bots to SearXNG must also be blocked, this
is the task of the limiter.  To perform this task, the limiter uses the methods
from the :py:obj:`searx.botdetection`.

To enable the limiter activate:

.. code:: yaml

   server:
     ...
     limiter: true  # rate limit the number of request on the instance, block some bots

and set the redis-url connection. Check the value, it depends on your redis DB
(see :ref:`settings redis`), by example:

.. code:: yaml

   redis:
     url: unix:///usr/local/searxng-redis/run/redis.sock?db=0

"""

from typing import Optional, Tuple
import flask

from searx.botdetection import (
    http_accept,
    http_accept_encoding,
    http_accept_language,
    http_connection,
    http_user_agent,
    ip_limit,
)


def filter_request(request: flask.Request) -> Optional[Tuple[int, str]]:

    if request.path == '/healthz':
        return None

    for func in [
        http_user_agent,
    ]:
        val = func.filter_request(request)
        if val is not None:
            return val

    if request.path == '/search':

        for func in [
            http_accept,
            http_accept_encoding,
            http_accept_language,
            http_connection,
            http_user_agent,
            ip_limit,
        ]:
            val = func.filter_request(request)
            if val is not None:
                return val

    return None
