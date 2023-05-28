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
from pathlib import Path
import flask
import pytomlpp as toml

from searx import logger
from searx.tools import config
from searx.botdetection import (
    http_accept,
    http_accept_encoding,
    http_accept_language,
    http_connection,
    http_user_agent,
    ip_limit,
)

LIMITER_CFG_SCHEMA = Path(__file__).parent / "limiter.toml"
"""Base configuration (schema) of the botdetection."""

LIMITER_CFG = Path('/etc/searxng/limiter.toml')
"""Lokal Limiter configuration."""

CFG_DEPRECATED = {
    # "dummy.old.foo": "config 'dummy.old.foo' exists only for tests.  Don't use it in your real project config."
}

CFG = None


def get_cfg() -> config.Config:
    if CFG is None:
        init_cfg(logger)
    return CFG


def init_cfg(log):
    global CFG  # pylint: disable=global-statement
    CFG = config.Config(cfg_schema=toml.load(LIMITER_CFG_SCHEMA), deprecated=CFG_DEPRECATED)

    if not LIMITER_CFG.exists():
        log.warning("missing config file: %s", LIMITER_CFG)
        return

    log.info("load config file: %s", LIMITER_CFG)
    try:
        upd_cfg = toml.load(LIMITER_CFG)
    except toml.DecodeError as exc:
        msg = str(exc).replace('\t', '').replace('\n', ' ')
        log.error("%s: %s", LIMITER_CFG, msg)
        raise

    is_valid, issue_list = CFG.validate(upd_cfg)
    for msg in issue_list:
        log.error(str(msg))
    if not is_valid:
        raise TypeError(f"schema of {LIMITER_CFG} is invalid, can't cutomize limiter configuration from!")
    CFG.update(upd_cfg)


def filter_request(request: flask.Request) -> Optional[Tuple[int, str]]:

    if request.path == '/healthz':
        return None

    for func in [
        http_user_agent,
    ]:
        val = func.filter_request(request, CFG)
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
            val = func.filter_request(request, CFG)
            if val is not None:
                return val

    return None
