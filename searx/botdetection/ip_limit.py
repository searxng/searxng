""".. _botdetection.ip_limit:

Method ``ip_limit``
-------------------

The ``ip_limit`` method counts request from an IP in *sliding windows*.  If
there are to many requests in a sliding window, the request is evaluated as a
bot request.  This method requires a redis DB and needs a HTTP X-Forwarded-For_
header.  To take privacy only the hash value of an IP is stored in the redis DB
and at least for a maximum of 10 minutes.

The :py:obj:`.link_token` method can be used to investigate whether a request is
*suspicious*.  To activate the :py:obj:`.link_token` method in the
:py:obj:`.ip_limit` method add the following to your
``/etc/searxng/limiter.toml``:

.. code:: toml

   [botdetection.ip_limit]
   link_token = true

If the :py:obj:`.link_token` method is activated and a request is *suspicious*
the request rates are reduced:

- :py:obj:`BURST_MAX` -> :py:obj:`BURST_MAX_SUSPICIOUS`
- :py:obj:`LONG_MAX` -> :py:obj:`LONG_MAX_SUSPICIOUS`

.. _X-Forwarded-For:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Forwarded-For

"""

from typing import Optional, Tuple
import flask
from searx.tools import config


from searx import redisdb
from searx import logger
from searx.redislib import incr_sliding_window

from . import link_token

logger = logger.getChild('botdetection.ip_limit')

BURST_WINDOW = 20
"""Time (sec) before sliding window for *burst* requests expires."""

BURST_MAX = 15
"""Maximum requests from one IP in the :py:obj:`BURST_WINDOW`"""

BURST_MAX_SUSPICIOUS = 2
"""Maximum of suspicious requests from one IP in the :py:obj:`BURST_WINDOW`"""

LONG_WINDOW = 600
"""Time (sec) before the longer sliding window expires."""

LONG_MAX = 150
"""Maximum requests from one IP in the :py:obj:`LONG_WINDOW`"""

LONG_MAX_SUSPICIOUS = 10
"""Maximum suspicious requests from one IP in the :py:obj:`LONG_WINDOW`"""

API_WONDOW = 3600
"""Time (sec) before sliding window for API requests (format != html) expires."""

API_MAX = 4
"""Maximum requests from one IP in the :py:obj:`API_WONDOW`"""


def filter_request(request: flask.Request, cfg: config.Config) -> Optional[Tuple[int, str]]:
    redis_client = redisdb.client()

    x_forwarded_for = request.headers.get('X-Forwarded-For', '')
    if not x_forwarded_for:
        logger.error("missing HTTP header X-Forwarded-For")

    if request.args.get('format', 'html') != 'html':
        c = incr_sliding_window(redis_client, 'IP limit - API_WONDOW:' + x_forwarded_for, API_WONDOW)
        if c > API_MAX:
            return 429, "BLOCK %s: API limit exceeded"

    suspicious = False
    if cfg['botdetection.ip_limit.link_token']:
        suspicious = link_token.is_suspicious(request)

    if suspicious:
        c = incr_sliding_window(redis_client, 'IP limit - BURST_WINDOW:' + x_forwarded_for, BURST_WINDOW)
        if c > BURST_MAX_SUSPICIOUS:
            return 429, f"bot detected, too many request from {x_forwarded_for} in BURST_MAX_SUSPICIOUS"

        c = incr_sliding_window(redis_client, 'IP limit - LONG_WINDOW:' + x_forwarded_for, LONG_WINDOW)
        if c > LONG_MAX_SUSPICIOUS:
            return 429, f"bot detected, too many request from {x_forwarded_for} in LONG_MAX_SUSPICIOUS"

    else:
        c = incr_sliding_window(redis_client, 'IP limit - BURST_WINDOW:' + x_forwarded_for, BURST_WINDOW)
        if c > BURST_MAX:
            return 429, f"bot detected, too many request from {x_forwarded_for} in BURST_MAX"

        c = incr_sliding_window(redis_client, 'IP limit - LONG_WINDOW:' + x_forwarded_for, LONG_WINDOW)
        if c > LONG_MAX:
            return 429, f"bot detected, too many request from {x_forwarded_for} in LONG_MAX"
    return None
