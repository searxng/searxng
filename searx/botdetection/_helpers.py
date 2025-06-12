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

       [real_ip]

       ipv4_prefix = 32
       ipv6_prefix = 48

    """

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


def get_real_ip(request: flask.Request, cfg: config.Config) -> IPv4Address | IPv6Address:
    """Returns real IP of the request.

    This function tries to get the remote IP in the order listed below,
    additional tests are done and if inconsistencies or errors are
    detected, they are logged.

    If the request comes via socket and/or the IP cannot be determined,
    the function will return "0.0.0.0" as a fallback value.

    The remote IP of the request is taken from (first match):

    - X-Forwarded-For_ if header comes from a network of ``real_ip.trusted_proxies``
    - X-Real-IP_ if header comes from a network of ``real_ip.trusted_proxies``
    - :py:obj:`flask.Request.remote_addr`

    .. _X-Forwarded-For:
      https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Forwarded-For
    .. _X-Real-IP:
      https://github.com/searxng/searxng/issues/1237#issuecomment-1147564516

    .. code:: toml

       [real_ip]

       trusted_proxies = [
         '127.0.0.0/8',     # IPv4 localhost network
         '::1',             # IPv6 localhost
         '192.168.0.0/16',  # IPv4 private network
       ]
    """

    remote_addr = ip_address(request.remote_addr or "0.0.0.0")
    request_ip = remote_addr

    if is_trusted_proxy(remote_addr, cfg):
        forwarded_for = request.headers.get("X-Forwarded-For")
        real_ip = request.headers.get("X-Real-IP")

        logger.debug(
            "X-Forwarded-For: %s || X-Real-IP: %s || request.remote_addr: %s",
            forwarded_for,
            real_ip,
            remote_addr.compressed,
        )

        if forwarded_for:
            try:
                forwarded_for = ip_address(forwarded_for.split(",")[0].strip())
            except ValueError:
                forwarded_for = None

        if real_ip:
            try:
                real_ip = ip_address(real_ip)
            except ValueError:
                real_ip = None

        request_ip = forwarded_for or real_ip or remote_addr

    logger.debug("get_real_ip() -> %s", request_ip)
    return request_ip


def is_trusted_proxy(remote_ip: IPv4Address | IPv6Address, cfg: config.Config) -> bool:
    """Checks if the ``remote_ip`` is a member of one of the networks in the
    ``real_ip.trusted_proxies`` list."""

    # probably from a socket
    if remote_ip.compressed == "0.0.0.0":
        return True

    trusted_proxy = cfg.get("real_ip.trusted_proxies", default=None)
    if trusted_proxy is None:
        logger.warning("missing real_ip.trusted_proxies config (default: loopback)")
        trusted_proxy = ["127.0.0.0/8", "::1"]

    logger.debug("real_ip.trusted_proxies: %s", trusted_proxy)
    for net in trusted_proxy:
        net = ip_network(net, strict=False)
        if remote_ip.version == net.version and remote_ip in net:
            logger.debug("remote_ip %s is member of %s", remote_ip, net)
            return True
    return False
