# SPDX-License-Identifier: AGPL-3.0-or-later
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
import flask
import werkzeug

from botdetection import (
    install_botdetection,
    RouteFilter,
    Config,
    PredefinedRequestFilter,
    RequestContext,
    RequestInfo,
    too_many_requests,
)
from searx import logger, redisdb

try:
    import tomllib

    pytomlpp = None
    USE_TOMLLIB = True
except ImportError:
    import pytomlpp

    tomllib = None
    USE_TOMLLIB = False


# the configuration are limiter.toml and "limiter" in settings.yml so, for
# coherency, the logger is "limiter"
logger = logger.getChild('limiter')

CFG: Config = None  # type: ignore
_INSTALLED = False

LIMITER_CFG_SCHEMA = Path(__file__).parent / "limiter.toml"
"""Base configuration (schema) of the botdetection."""

LIMITER_CFG = Path('/etc/searxng/limiter.toml')
"""Local Limiter configuration."""

API_WINDOW = 3600
"""Time (sec) before sliding window for API requests (format != html) expires."""

API_MAX = 4
"""Maximum requests from one IP in the :py:obj:`API_WINDOW`"""


def toml_load(file_name):
    if USE_TOMLLIB:
        # Python >= 3.11
        try:
            with open(file_name, "rb") as f:
                return tomllib.load(f)
        except tomllib.TOMLDecodeError as exc:
            msg = str(exc).replace('\t', '').replace('\n', ' ')
            logger.error("%s: %s", file_name, msg)
            raise
    # fallback to pytomlpp for Python < 3.11
    try:
        return pytomlpp.load(file_name)
    except pytomlpp.DecodeError as exc:
        msg = str(exc).replace('\t', '').replace('\n', ' ')
        logger.error("%s: %s", file_name, msg)
        raise


def get_config() -> Config:
    global CFG  # pylint: disable=global-statement
    if CFG is None:
        if LIMITER_CFG.is_file():
            data = toml_load(LIMITER_CFG)
        else:
            data = toml_load(LIMITER_CFG_SCHEMA)
        CFG = Config(real_ip=data["real_ip"], botdetection=data["botdetection"])
    return CFG


def api_rate_filter_request(
    context: RequestContext,
    request_info: RequestInfo,
    request: flask.Request,
) -> werkzeug.Response | None:
    if request.args.get("format", "html") != "html":
        c = context.redislib.incr_sliding_window("ip_limit.API_WINDOW:" + request_info.network.compressed, API_WINDOW)
        if c > API_MAX:
            return too_many_requests(request_info, "too many request in API_WINDOW")
    return None


route_filter = RouteFilter(
    {
        "/healthz": [],
        "/search": [
            PredefinedRequestFilter.HTTP_ACCEPT,
            PredefinedRequestFilter.HTTP_ACCEPT_ENCODING,
            PredefinedRequestFilter.HTTP_ACCEPT_LANGUAGE,
            PredefinedRequestFilter.HTTP_USER_AGENT,
            api_rate_filter_request,
            PredefinedRequestFilter.IP_LIMIT,
        ],
        "*": [
            PredefinedRequestFilter.HTTP_USER_AGENT,
        ],
    }
)


def is_installed():
    """Returns ``True`` if limiter is active and a redis DB is available."""
    return _INSTALLED


def initialize(app: flask.Flask, settings):
    """Install the limiter"""
    global _INSTALLED  # pylint: disable=global-statement

    # even if the limiter is not activated, the botdetection must be activated
    # (e.g. the self_info plugin uses the botdetection to get client IP)

    if not (settings['server']['limiter'] or settings['server']['public_instance']):
        return

    redis_client = redisdb.client()
    if not redis_client:
        logger.error(
            "The limiter requires Redis, please consult the documentation: "
            "https://docs.searxng.org/admin/searx.limiter.html"
        )
        if settings['server']['public_instance']:
            sys.exit(1)
        return

    # install botdetection
    _INSTALLED = True

    config = get_config()
    if settings['server']['public_instance']:
        # overwrite limiter.toml setting
        config.botdetection.ip_limit.link_token = True

    install_botdetection(app, redis_client, config, route_filter)
