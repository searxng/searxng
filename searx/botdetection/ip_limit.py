# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
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

To intercept bots that get their IPs from a range of IPs, there is a
:py:obj:`SUSPICIOUS_IP_WINDOW`.  In this window the suspicious IPs are stored
for a longer time.  IPs stored in this sliding window have a maximum of
:py:obj:`SUSPICIOUS_IP_MAX` accesses before they are blocked.  As soon as the IP
makes a request that is not suspicious, the sliding window for this IP is
droped.

.. _X-Forwarded-For:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Forwarded-For

"""
from __future__ import annotations
from ipaddress import (
    IPv4Network,
    IPv6Network,
)

import flask
import werkzeug
from searx.tools import config

from searx import redisdb
from searx.redislib import incr_sliding_window, drop_counter

from . import link_token
from ._helpers import (
    too_many_requests,
    logger,
)


logger = logger.getChild('ip_limit')

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

SUSPICIOUS_IP_WINDOW = 3600 * 24 * 30
"""Time (sec) before sliding window for one suspicious IP expires."""

SUSPICIOUS_IP_MAX = 3
"""Maximum requests from one suspicious IP in the :py:obj:`SUSPICIOUS_IP_WINDOW`."""


def filter_request(
    network: IPv4Network | IPv6Network,
    request: flask.Request,
    cfg: config.Config,
) -> werkzeug.Response | None:

    # pylint: disable=too-many-return-statements
    redis_client = redisdb.client()

    if network.is_link_local and not cfg['botdetection.ip_limit.filter_link_local']:
        logger.debug("network %s is link-local -> not monitored by ip_limit method", network.compressed)
        return None

    if request.args.get('format', 'html') != 'html':
        c = incr_sliding_window(redis_client, 'ip_limit.API_WONDOW:' + network.compressed, API_WONDOW)
        if c > API_MAX:
            return too_many_requests(network, "too many request in API_WINDOW")

    if cfg['botdetection.ip_limit.link_token']:

        suspicious = link_token.is_suspicious(network, request, True)

        if not suspicious:
            # this IP is no longer suspicious: release ip again / delete the counter of this IP
            drop_counter(redis_client, 'ip_limit.SUSPICIOUS_IP_WINDOW' + network.compressed)
            return None

        # this IP is suspicious: count requests from this IP
        c = incr_sliding_window(
            redis_client, 'ip_limit.SUSPICIOUS_IP_WINDOW' + network.compressed, SUSPICIOUS_IP_WINDOW
        )
        if c > SUSPICIOUS_IP_MAX:
            logger.error("BLOCK: too many request from %s in SUSPICIOUS_IP_WINDOW (redirect to /)", network)
            return flask.redirect(flask.url_for('index'), code=302)

        c = incr_sliding_window(redis_client, 'ip_limit.BURST_WINDOW' + network.compressed, BURST_WINDOW)
        if c > BURST_MAX_SUSPICIOUS:
            return too_many_requests(network, "too many request in BURST_WINDOW (BURST_MAX_SUSPICIOUS)")

        c = incr_sliding_window(redis_client, 'ip_limit.LONG_WINDOW' + network.compressed, LONG_WINDOW)
        if c > LONG_MAX_SUSPICIOUS:
            return too_many_requests(network, "too many request in LONG_WINDOW (LONG_MAX_SUSPICIOUS)")

        return None

    # vanilla limiter without extensions counts BURST_MAX and LONG_MAX
    c = incr_sliding_window(redis_client, 'ip_limit.BURST_WINDOW' + network.compressed, BURST_WINDOW)
    if c > BURST_MAX:
        return too_many_requests(network, "too many request in BURST_WINDOW (BURST_MAX)")

    c = incr_sliding_window(redis_client, 'ip_limit.LONG_WINDOW' + network.compressed, LONG_WINDOW)
    if c > LONG_MAX:
        return too_many_requests(network, "too many request in LONG_WINDOW (LONG_MAX)")

    return None
