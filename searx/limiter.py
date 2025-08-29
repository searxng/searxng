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
  behavior of the requests.  For dynamically changeable IP lists a Valkey
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

and set the valkey-url connection. Check the value, it depends on your valkey DB
(see :ref:`settings valkey`), by example:

.. code:: yaml

   valkey:
     url: valkey://localhost:6379/0


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

from ipaddress import ip_address
import sys

from pathlib import Path
import flask
import werkzeug

import searx.compat
from searx import (
    logger,
    valkeydb,
)
from searx import botdetection
from searx.extended_types import SXNG_Request, sxng_request
from searx.botdetection import (
    config,
    http_accept,
    http_accept_encoding,
    http_accept_language,
    http_user_agent,
    http_sec_fetch,
    ip_limit,
    ip_lists,
    get_network,
    dump_request,
)

# the configuration are limiter.toml and "limiter" in settings.yml so, for
# coherency, the logger is "limiter"
logger = logger.getChild('limiter')

CFG: config.Config | None = None
_INSTALLED = False

LIMITER_CFG_SCHEMA = Path(__file__).parent / "limiter.toml"
"""Base configuration (schema) of the botdetection."""


def get_cfg() -> config.Config:
    """Returns SearXNG's global limiter configuration."""
    global CFG  # pylint: disable=global-statement

    if CFG is None:
        from . import settings_loader  # pylint: disable=import-outside-toplevel

        cfg_file = (settings_loader.get_user_cfg_folder() or Path("/etc/searxng")) / "limiter.toml"
        CFG = config.Config.from_toml(LIMITER_CFG_SCHEMA, cfg_file, searx.compat.LIMITER_CFG_DEPRECATED)
        searx.compat.limiter_fix_cfg(CFG, cfg_file)

    return CFG


def filter_request(request: SXNG_Request) -> werkzeug.Response | None:
    # pylint: disable=too-many-return-statements

    cfg = get_cfg()
    real_ip = ip_address(request.remote_addr)
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

    # methods applied on all requests

    for func in [
        http_user_agent,
    ]:
        val = func.filter_request(network, request, cfg)
        if val is not None:
            logger.debug(f"NOT OK ({func.__name__}): {network}: %s", dump_request(sxng_request))
            return val

    # methods applied on /search requests

    if request.path == '/search':

        for func in [
            http_accept,
            http_accept_encoding,
            http_accept_language,
            http_user_agent,
            http_sec_fetch,
            ip_limit,
        ]:
            val = func.filter_request(network, request, cfg)
            if val is not None:
                logger.debug(f"NOT OK ({func.__name__}): {network}: %s", dump_request(sxng_request))
                return val

    logger.debug(f"OK {network}: %s", dump_request(sxng_request))
    return None


def pre_request():
    """See :py:obj:`flask.Flask.before_request`"""
    return filter_request(sxng_request)


def is_installed():
    """Returns ``True`` if limiter is active and a valkey DB is available."""
    return _INSTALLED


def initialize(app: flask.Flask, settings):
    """Install the limiter"""
    global _INSTALLED  # pylint: disable=global-statement

    # even if the limiter is not activated, the botdetection must be activated
    # (e.g. the self_info plugin uses the botdetection to get client IP)

    cfg = get_cfg()
    valkey_client = valkeydb.client()
    botdetection.init(cfg, valkey_client)

    if not (settings['server']['limiter'] or settings['server']['public_instance']):
        return

    if not valkey_client:
        logger.error(
            "The limiter requires Valkey, please consult the documentation: "
            "https://docs.searxng.org/admin/searx.limiter.html"
        )
        if settings['server']['public_instance']:
            sys.exit(1)
        return

    _INSTALLED = True

    if settings['server']['public_instance']:
        # overwrite limiter.toml setting
        cfg.set('botdetection.ip_limit.link_token', True)

    app.before_request(pre_request)
