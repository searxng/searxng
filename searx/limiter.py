# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Bot protection / IP rate limitation.  The intention of rate limitation is to
limit suspicious requests from an IP.  The motivation behind this is the fact
that SearXNG passes through requests from bots and is thus classified as a bot
itself.  As a result, the SearXNG engine then receives a CAPTCHA or is blocked
by the search engine (the origin) in some other way.

To avoid blocking, the requests from bots to SearXNG must also be blocked, this
is the task of the limiter.  To perform this task, the limiter uses the methods
from the :ref:`botdetection`:

- Analysis of the HTTP header in the request / :ref:`botdetection probe headers`
  can be easily bypassed.

- Block and pass lists in which IPs are listed / :ref:`botdetection ip_lists`
  are hard to maintain, since the IPs of bots are not all known and change over
  the time.

- Detection & dynamically :ref:`botdetection rate limit` of bots based on the
  behavior of the requests.  For dynamically changeable IP lists a Redis
  database is needed.

The prerequisite for IP based methods is the correct determination of the IP of
the client. The IP of the client is determined via the X-Forwarded-For_ HTTP
header.

.. attention::

   A correct setup of the HTTP request headers ``X-Forwarded-For`` and
   ``X-Real-IP`` is essential to be able to assign a request to an IP correctly:

   - `NGINX RequestHeader`_
   - `Apache RequestHeader`_

.. _X-Forwarded-For:
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Forwarded-For
.. _NGINX RequestHeader:
    https://docs.searxng.org/admin/installation-nginx.html#nginx-s-searxng-site
.. _Apache RequestHeader:
    https://docs.searxng.org/admin/installation-apache.html#apache-s-searxng-site

Enable Limiter
==============

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


Configure Limiter
=================

The methods of :ref:`botdetection` the limiter uses are configured in a local
file ``/etc/searxng/limiter.toml``.  The defaults are shown in limiter.toml_ /
Don't copy all values to your local configuration, just enable what you need by
overwriting the defaults.  For instance to activate the ``link_token`` method in
the :ref:`botdetection.ip_limit` you only need to set this option to ``true``:

.. code:: toml

   [botdetection.ip_limit]
   link_token = true

.. _limiter.toml:

``limiter.toml``
================

In this file the limiter finds the configuration of the :ref:`botdetection`:

- :ref:`botdetection ip_lists`
- :ref:`botdetection rate limit`
- :ref:`botdetection probe headers`

.. kernel-include:: $SOURCEDIR/limiter.toml
   :code: toml

Implementation
==============

"""

from __future__ import annotations
import sys

from pathlib import Path
from ipaddress import ip_address
import flask
import werkzeug

import botdetection
from botdetection import (
    http_accept,
    http_accept_encoding,
    http_accept_language,
    http_user_agent,
    ip_limit,
    ip_lists,
    get_network,
    get_real_ip,
    dump_request,
)

from searx import (
    logger,
    redisdb,
)

# the configuration are limiter.toml and "limiter" in settings.yml so, for
# coherency, the logger is "limiter"
logger = logger.getChild('limiter')

_FULLY_INSTALLED = False

DEFAULT_CFG = Path(__file__).parent / "limiter.toml"
"""Base configuration (schema) of the botdetection."""

LIMITER_CFG = Path('/etc/searxng/limiter.toml')
"""Local Limiter configuration."""

SEARXNG_ORG = [
    # https://github.com/searxng/searxng/pull/2484#issuecomment-1576639195
    '167.235.158.251',  # IPv4 check.searx.space
    '2a01:04f8:1c1c:8fc2::/64',  # IPv6 check.searx.space
]
"""Passlist of IPs from the SearXNG organization, e.g. `check.searx.space`."""


def filter_request(request: flask.Request) -> werkzeug.Response | None:
    # pylint: disable=too-many-return-statements

    cfg = botdetection.ctx.cfg
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
            http_user_agent,
            ip_limit,
        ]:
            val = func.filter_request(network, request, cfg)
            if val is not None:
                return val
    logger.debug(f"OK {network}: %s", dump_request(flask.request))
    return None


def pre_request():
    """See :py:obj:`flask.Flask.before_request`"""
    return filter_request(flask.request)


def is_fully_installed():
    """Returns ``True`` if limiter is active and a redis DB is available."""
    return _FULLY_INSTALLED


def initialize(app: flask.Flask, settings):
    """Install the limiter"""
    global _FULLY_INSTALLED  # pylint: disable=global-statement

    # even if the limiter is not activated, the botdetection must be activated
    # (e.g. the self_info plugin uses the botdetection to get client IP)

    redis_client = redisdb.client()
    botdetection.ctx.init(DEFAULT_CFG, redis_client)
    cfg = botdetection.ctx.cfg

    if settings['server']['public_instance']:
        # overwrite SearXNG and limiter.toml settings
        settings['server']['limiter'] = True
        settings['server']['pass_searxng_org'] = True
        cfg.set('botdetection.ip_limit.link_token', True)

    if settings['server']['pass_searxng_org']:
        cfg.get('botdetection.ip_lists.pass_ip').extend(SEARXNG_ORG)

    if settings['server']['limiter']:
        app.before_request(pre_request)

    if redis_client:
        _FULLY_INSTALLED = True

    else:
        logger.error(
            "The limiter requires Redis, please consult the documentation: "
            "https://docs.searxng.org/admin/searx.limiter.html"
        )
        if settings['server']['public_instance']:
            logger.error('server:public_instance activated but redis DB is missed')
            sys.exit()
