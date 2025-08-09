# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring, invalid-name
from __future__ import annotations
import typing as t

__all__ = ["log_error_only_once", "dump_request", "get_network", "logger", "too_many_requests"]

from ipaddress import (
    IPv4Network,
    IPv6Network,
    IPv4Address,
    IPv6Address,
    ip_network,
)
import flask
import werkzeug

from searx import logger

if t.TYPE_CHECKING:
    from . import config

logger = logger.getChild('botdetection')


def dump_request(request: flask.Request):
    return (
        request.path
        + " || X-Forwarded-For: %s" % request.headers.get('X-Forwarded-For')
        + " || X-Real-IP: %s" % request.headers.get('X-Real-IP')
        + " || form: %s" % request.form
        + " || Accept: %s" % request.headers.get('Accept')
        + " || Accept-Language: %s" % request.headers.get('Accept-Language')
        + " || Accept-Encoding: %s" % request.headers.get('Accept-Encoding')
        + " || Content-Type: %s" % request.headers.get('Content-Type')
        + " || Content-Length: %s" % request.headers.get('Content-Length')
        + " || Connection: %s" % request.headers.get('Connection')
        + " || User-Agent: %s" % request.headers.get('User-Agent')
        + " || Sec-Fetch-Site: %s" % request.headers.get('Sec-Fetch-Site')
        + " || Sec-Fetch-Mode: %s" % request.headers.get('Sec-Fetch-Mode')
        + " || Sec-Fetch-Dest: %s" % request.headers.get('Sec-Fetch-Dest')
    )


def too_many_requests(network: IPv4Network | IPv6Network, log_msg: str) -> werkzeug.Response | None:
    """Returns a HTTP 429 response object and writes a ERROR message to the
    'botdetection' logger.  This function is used in part by the filter methods
    to return the default ``Too Many Requests`` response.

    """

    logger.debug("BLOCK %s: %s", network.compressed, log_msg)
    return flask.make_response(('Too Many Requests', 429))


def get_network(real_ip: IPv4Address | IPv6Address, cfg: config.Config) -> IPv4Network | IPv6Network:
    """Returns the (client) network of whether the ``real_ip`` is part of.

    The ``ipv4_prefix`` and ``ipv6_prefix`` define the number of leading bits in
    an address that are compared to determine whether or not an address is part
    of a (client) network.

    .. code:: toml

       [botdetection]

       ipv4_prefix = 32
       ipv6_prefix = 48

    """

    prefix: int = cfg["botdetection.ipv4_prefix"]
    if real_ip.version == 6:
        prefix: int = cfg["botdetection.ipv6_prefix"]
    network = ip_network(f"{real_ip}/{prefix}", strict=False)
    # logger.debug("get_network(): %s", network.compressed)
    return network


_logged_errors: list[str] = []


def log_error_only_once(err_msg: str):
    if err_msg not in _logged_errors:
        logger.error(err_msg)
        _logged_errors.append(err_msg)
