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

from __future__ import annotations

from pathlib import Path
from ipaddress import ip_address
import flask
import werkzeug

from searx.tools import config
from searx import logger

from . import (
    http_accept,
    http_accept_encoding,
    http_accept_language,
    http_connection,
    http_user_agent,
    ip_limit,
    ip_lists,
)

from ._helpers import (
    get_network,
    get_real_ip,
    dump_request,
)

logger = logger.getChild('botdetection.limiter')

CFG: config.Config = None  # type: ignore

LIMITER_CFG_SCHEMA = Path(__file__).parent / "limiter.toml"
"""Base configuration (schema) of the botdetection."""

LIMITER_CFG = Path('/etc/searxng/limiter.toml')
"""Lokal Limiter configuration."""

CFG_DEPRECATED = {
    # "dummy.old.foo": "config 'dummy.old.foo' exists only for tests.  Don't use it in your real project config."
}


def get_cfg() -> config.Config:
    global CFG  # pylint: disable=global-statement
    if CFG is None:
        CFG = config.Config.from_toml(LIMITER_CFG_SCHEMA, LIMITER_CFG, CFG_DEPRECATED)
    return CFG


def filter_request(request: flask.Request) -> werkzeug.Response | None:
    # pylint: disable=too-many-return-statements

    cfg = get_cfg()
    real_ip = ip_address(get_real_ip(request))
    network = get_network(real_ip, cfg)

    if request.path == '/healthz':
        return None

    # link-local

    if network.is_link_local:
        return None

    # block- & pass- lists
    #
    # 1. The IP of the request is first checked against the pass-list; if the IP
    #    matches an entry in the list, the request is not blocked.
    # 2. If no matching entry is found in the pass-list, then a check is made against
    #    the block list; if the IP matches an entry in the list, the request is
    #    blocked.
    # 3. If the IP is not in either list, the request is not blocked.

    match, msg = ip_lists.pass_ip(real_ip, cfg)
    if match:
        logger.warning("PASS %s: matched PASSLIST - %s", network.compressed, msg)
        return None

    match, msg = ip_lists.block_ip(real_ip, cfg)
    if match:
        logger.error("BLOCK %s: matched BLOCKLIST - %s", network.compressed, msg)
        return flask.make_response(('IP is on BLOCKLIST - %s' % msg, 429))

    # methods applied on /

    for func in [
        http_user_agent,
    ]:
        val = func.filter_request(network, request, cfg)
        if val is not None:
            return val

    # methods applied on /search

    if request.path == '/search':

        for func in [
            http_accept,
            http_accept_encoding,
            http_accept_language,
            http_connection,
            http_user_agent,
            ip_limit,
        ]:
            val = func.filter_request(network, request, cfg)
            if val is not None:
                return val
    logger.debug(f"OK {network}: %s", dump_request(flask.request))
    return None
