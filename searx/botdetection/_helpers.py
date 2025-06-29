# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring, invalid-name
from __future__ import annotations

from ipaddress import (
    IPv4Network,
    IPv6Network,
    IPv4Address,
    IPv6Address,
    ip_network,
    ip_address,
)

import flask
import werkzeug

from searx import logger
from searx.extended_types import SXNG_Request

from . import config
from .ip_lists import trusted_proxies  # pylint: disable=cyclic-import

logger = logger.getChild('botdetection')


def dump_request(request: SXNG_Request):
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


def get_network(real_ip: IPv4Address | IPv6Address) -> IPv4Network | IPv6Network:
    """Returns the (client) network of whether the real_ip is part of."""

    cfg = config.get_cfg()

    if real_ip.version == 6:
        prefix = cfg['real_ip.ipv6_prefix']
    else:
        prefix = cfg['real_ip.ipv4_prefix']
    network = ip_network(f"{real_ip}/{prefix}", strict=False)
    # logger.debug("get_network(): %s", network.compressed)
    return network


_logged_errors = []


def _log_error_only_once(err_msg):
    if err_msg not in _logged_errors:
        logger.error(err_msg)
        _logged_errors.append(err_msg)


def get_real_ip(request: SXNG_Request) -> IPv4Address | IPv6Address:
    """Returns real IP of the request.

    This function tries to get the remote IP in the order listed below,
    additional tests are done and if inconsistencies or errors are
    detected, they are logged.

    The remote IP of the request is taken from (first match):

    - X-Forwarded-For_ header (if from a trusted proxy)
    - X-Real-IP_ header (if from a trusted proxy)
    - :py:obj:`flask.Request.remote_addr`

    .. _X-Forwarded-For:
      https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Forwarded-For
    .. _X-Real-IP:
      https://github.com/searxng/searxng/issues/1237#issuecomment-1147564516
    """

    cfg = config.get_cfg()
    remote_addr = ip_address(request.remote_addr or "0.0.0.0")
    request_ip = remote_addr

    if trusted_proxies(remote_addr, cfg):
        forwarded_for = request.headers.get("X-Forwarded-For")
        real_ip = request.headers.get("X-Real-IP")

        logger.debug(
            "X-Forwarded-For: %s || X-Real-IP: %s || request.remote_addr: %s",
            forwarded_for,
            real_ip,
            remote_addr.compressed,
        )

        if not forwarded_for:
            _log_error_only_once("X-Forwarded-For header is not set!")
        else:
            try:
                forwarded_for = ip_address(forwarded_for.split(",")[0].strip()).compressed
            except ValueError:
                forwarded_for = None

        if not real_ip:
            _log_error_only_once("X-Real-IP header is not set!")
        else:
            try:
                real_ip = ip_address(real_ip).compressed
            except ValueError:
                real_ip = None

        if forwarded_for and real_ip and forwarded_for != real_ip:
            logger.warning(
                "IP from X-Real-IP (%s) is not equal to IP from X-Forwarded-For (%s)",
                real_ip,
                forwarded_for,
            )

        request_ip = ip_address(forwarded_for or real_ip or remote_addr)

    if request_ip.version == 6 and request_ip.ipv4_mapped:
        request_ip = request_ip.ipv4_mapped

    logger.debug("get_real_ip() -> %s", request_ip.compressed)
    return request_ip
