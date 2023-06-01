# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
Method ``http_user_agent``
--------------------------

The ``http_user_agent`` method evaluates a request as the request of a bot if
the User-Agent_ header is unset or matches the regular expression
:py:obj:`USER_AGENT`.

.. _User-Agent:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent

"""
# pylint: disable=unused-argument

from __future__ import annotations
import re
from ipaddress import (
    IPv4Network,
    IPv6Network,
)

import flask
import werkzeug

from searx.tools import config
from ._helpers import too_many_requests


USER_AGENT = (
    r'('
    + r'unknown'
    + r'|[Cc][Uu][Rr][Ll]|[wW]get|Scrapy|splash|JavaFX|FeedFetcher|python-requests|Go-http-client|Java|Jakarta|okhttp'
    + r'|HttpClient|Jersey|Python|libwww-perl|Ruby|SynHttpClient|UniversalFeedParser|Googlebot|GoogleImageProxy'
    + r'|bingbot|Baiduspider|yacybot|YandexMobileBot|YandexBot|Yahoo! Slurp|MJ12bot|AhrefsBot|archive.org_bot|msnbot'
    + r'|MJ12bot|SeznamBot|linkdexbot|Netvibes|SMTBot|zgrab|James BOT|Sogou|Abonti|Pixray|Spinn3r|SemrushBot|Exabot'
    + r'|ZmEu|BLEXBot|bitlybot'
    # unmaintained Farside instances
    + r'|'
    + re.escape(r'Mozilla/5.0 (compatible; Farside/0.1.0; +https://farside.link)')
    # other bots and client to block
    + '|.*PetalBot.*'
    + r')'
)
"""Regular expression that matches to User-Agent_ from known *bots*"""

_regexp = None


def regexp_user_agent():
    global _regexp  # pylint: disable=global-statement
    if not _regexp:
        _regexp = re.compile(USER_AGENT)
    return _regexp


def filter_request(
    network: IPv4Network | IPv6Network,
    request: flask.Request,
    cfg: config.Config,
) -> werkzeug.Response | None:

    user_agent = request.headers.get('User-Agent', 'unknown')
    if regexp_user_agent().match(user_agent):
        return too_many_requests(network, f"bot detected, HTTP header User-Agent: {user_agent}")
    return None
