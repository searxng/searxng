# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implementation of a middleware to determine the real IP of an HTTP request
(:py:obj:`flask.request.remote_addr`) behind a proxy chain."""
# pylint: disable=too-many-branches

from __future__ import annotations
import typing as t

from collections import abc
from ipaddress import IPv4Address, IPv6Address, ip_address, ip_network, IPv4Network, IPv6Network
from werkzeug.http import parse_list_header

from . import config
from ._helpers import log_error_only_once, logger

if t.TYPE_CHECKING:
    from _typeshed.wsgi import StartResponse
    from _typeshed.wsgi import WSGIApplication
    from _typeshed.wsgi import WSGIEnvironment


class ProxyFix:
    """A middleware like the ProxyFix_ class, where the ``x_for`` argument is
    replaced by a method that determines the number of trusted proxies via the
    ``botdetection.trusted_proxies`` setting.

    .. sidebar:: :py:obj:`flask.Request.remote_addr`

       SearXNG uses Werkzeug's ProxyFix_ (with it default ``x_for=1``).

    The remote IP (:py:obj:`flask.Request.remote_addr`) of the request is taken
    from (first match):

    - X-Forwarded-For_: If the header is set, the first untrusted IP that comes
      before the IPs that are still part of the ``botdetection.trusted_proxies``
      is used.

    - `X-Real-IP <https://github.com/searxng/searxng/issues/1237#issuecomment-1147564516>`__:
      If X-Forwarded-For_ is not set, `X-Real-IP` is used
      (``botdetection.trusted_proxies`` is ignored).

    If none of the header is set, the REMOTE_ADDR_ from the WSGI layer is used.
    If (for whatever reasons) none IP can be determined, an error message is
    displayed and ``100::`` is used instead (:rfc:`6666`).

    .. _ProxyFix:
       https://werkzeug.palletsprojects.com/middleware/proxy_fix/

    .. _X-Forwarded-For:
       https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Forwarded-For

    .. _REMOTE_ADDR:
       https://wsgi.readthedocs.io/en/latest/proposals-2.0.html#making-some-keys-required

    """

    def __init__(self, wsgi_app: WSGIApplication) -> None:
        self.wsgi_app = wsgi_app

    def trusted_proxies(self) -> list[IPv4Network | IPv6Network]:
        cfg = config.get_global_cfg()
        proxy_list: list[str] = cfg.get("botdetection.trusted_proxies", default=[])
        return [ip_network(net, strict=False) for net in proxy_list]

    def trusted_remote_addr(
        self,
        x_forwarded_for: list[IPv4Address | IPv6Address],
        trusted_proxies: list[IPv4Network | IPv6Network],
    ) -> str:
        # always rtl
        for addr in reversed(x_forwarded_for):
            trust: bool = False

            for net in trusted_proxies:
                if addr.version == net.version and addr in net:
                    logger.debug("trust proxy %s (member of %s)", addr, net)
                    trust = True
                    break

            # client address
            if not trust:
                return addr.compressed

        # fallback to first address
        return x_forwarded_for[0].compressed

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> abc.Iterable[bytes]:
        # pylint: disable=too-many-statements

        trusted_proxies = self.trusted_proxies()

        # We do not rely on the REMOTE_ADDR from the WSGI environment / the
        # variable is first removed from the WSGI environment and explicitly set
        # in this function!

        orig_remote_addr: str | None = environ.pop("REMOTE_ADDR")

        # Validate the IPs involved in this game and delete all invalid ones
        # from the WSGI environment.

        if orig_remote_addr:
            try:
                addr = ip_address(orig_remote_addr)
                if addr.version == 6 and addr.ipv4_mapped:
                    addr = addr.ipv4_mapped
                orig_remote_addr = addr.compressed
            except ValueError as exc:
                logger.error("REMOTE_ADDR: %s / discard REMOTE_ADDR from WSGI environment", exc)
                orig_remote_addr = None

        x_real_ip: str | None = environ.get("HTTP_X_REAL_IP")
        if x_real_ip:
            try:
                addr = ip_address(x_real_ip)
                if addr.version == 6 and addr.ipv4_mapped:
                    addr = addr.ipv4_mapped
                x_real_ip = addr.compressed
            except ValueError as exc:
                logger.error("X-Real-IP: %s / discard HTTP_X_REAL_IP from WSGI environment", exc)
                environ.pop("HTTP_X_REAL_IP")
                x_real_ip = None

        x_forwarded_for: list[IPv4Address | IPv6Address] = []
        if environ.get("HTTP_X_FORWARDED_FOR"):
            for x_for_ip in parse_list_header(str(environ.get("HTTP_X_FORWARDED_FOR"))):
                try:
                    addr = ip_address(x_for_ip)
                except ValueError as exc:
                    logger.error("X-Forwarded-For: %s / discard HTTP_X_FORWARDED_FOR from WSGI environment", exc)
                    environ.pop("HTTP_X_FORWARDED_FOR")
                    x_forwarded_for = []
                    break

                if addr.version == 6 and addr.ipv4_mapped:
                    addr = addr.ipv4_mapped
                x_forwarded_for.append(addr)

        # log questionable WSGI environments

        if not x_forwarded_for and not x_real_ip:
            log_error_only_once("X-Forwarded-For nor X-Real-IP header is set!")

        if x_forwarded_for and not trusted_proxies:
            log_error_only_once("missing botdetection.trusted_proxies config")
            # without trusted_proxies, this variable is useless for determining
            # the real IP
            x_forwarded_for = []

        # securing the WSGI environment variables that are adjusted

        environ.update({"botdetection.trusted_proxies.orig": {"REMOTE_ADDR": orig_remote_addr}})

        # determine *the real IP*

        if x_forwarded_for:
            environ["REMOTE_ADDR"] = self.trusted_remote_addr(x_forwarded_for, trusted_proxies)

        elif x_real_ip:
            environ["REMOTE_ADDR"] = x_real_ip

        elif orig_remote_addr:
            environ["REMOTE_ADDR"] = orig_remote_addr

        else:
            logger.error("No remote IP could be determined, use black-hole address: 100::")
            environ["REMOTE_ADDR"] = "100::"

        try:
            _ = ip_address(environ["REMOTE_ADDR"])
        except ValueError as exc:
            logger.error("REMOTE_ADDR: %s, use black-hole address: 100::", exc)
            environ["REMOTE_ADDR"] = "100::"

        logger.debug("final REMOTE_ADDR is: %s", environ["REMOTE_ADDR"])
        return self.wsgi_app(environ, start_response)
