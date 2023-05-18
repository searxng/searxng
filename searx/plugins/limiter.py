# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pyright: basic
"""Some bot protection / rate limitation

To monitor rate limits and protect privacy the IP addresses are getting stored
with a hash so the limiter plugin knows who to block.  A redis database is
needed to store the hash values.

It is also possible to bypass the limiter for a specific IP address or subnet
using the `whitelist_ip` and `whitelist_subnet` settings.

Enable the plugin in ``settings.yml``:

- ``server.limiter: true``
- ``server.limiter.whitelist_ip: ['127.0.0.1']``
- ``server.limiter_whitelist_subnet: ['192.168.0.0/24']``
- ``redis.url: ...`` check the value, see :ref:`settings redis`



"""

import ipaddress
import re
from typing import List, cast
from flask import request

from searx import get_setting, redisdb
from searx.redislib import incr_sliding_window

name = "Request limiter"
description = "Limit the number of request"
default_on = False
preference_section = 'service'


re_bot = re.compile(
    r'('
    + r'[Cc][Uu][Rr][Ll]|[wW]get|Scrapy|splash|JavaFX|FeedFetcher|python-requests|Go-http-client|Java|Jakarta|okhttp'
    + r'|HttpClient|Jersey|Python|libwww-perl|Ruby|SynHttpClient|UniversalFeedParser|Googlebot|GoogleImageProxy'
    + r'|bingbot|Baiduspider|yacybot|YandexMobileBot|YandexBot|Yahoo! Slurp|MJ12bot|AhrefsBot|archive.org_bot|msnbot'
    + r'|MJ12bot|SeznamBot|linkdexbot|Netvibes|SMTBot|zgrab|James BOT|Sogou|Abonti|Pixray|Spinn3r|SemrushBot|Exabot'
    + r'|ZmEu|BLEXBot|bitlybot'
    + r')'
)


WHITELISTED_IPS = []
WHITELISTED_SUBNET = []


def is_whitelist_ip(ip_str: str) -> bool:
    """Check if the given IP address belongs to the whitelisted list of IP addresses or subnets."""
    # if ip is empty use the source ip
    try:
        ip_a = ipaddress.ip_address(ip_str)
    except ValueError as e:
        logger.error("Error while checking ratelimiter whitelist: %s", e)
        return False
    return ip_a in WHITELISTED_IPS or any(ip_a in subnet for subnet in WHITELISTED_SUBNET)


def get_remote_addr() -> str:
    x_forwarded_for = request.headers.getlist('X-Forwarded-For')
    if len(x_forwarded_for) > 0:
        return x_forwarded_for[-1]
    return request.remote_addr or ''


def is_accepted_request() -> bool:
    # pylint: disable=too-many-return-statements
    redis_client = redisdb.client()
    user_agent = request.headers.get('User-Agent', '')
    remote_addr = get_remote_addr()

    # if the request source ip belongs to the whitelisted list of ip addresses or subnets
    if is_whitelist_ip(remote_addr):
        logger.debug("whitelist IP")
        return True

    if request.path == '/image_proxy':
        if re_bot.match(user_agent):
            return False
        return True

    if request.path == '/search':
        c_burst = incr_sliding_window(redis_client, 'IP limit, burst' + remote_addr, 20)
        c_10min = incr_sliding_window(redis_client, 'IP limit, 10 minutes' + remote_addr, 600)
        if c_burst > 15 or c_10min > 150:
            logger.debug("to many request")  # pylint: disable=undefined-variable
            return False

        if re_bot.match(user_agent):
            logger.debug("detected bot")  # pylint: disable=undefined-variable
            return False

        if len(request.headers.get('Accept-Language', '').strip()) == '':
            logger.debug("missing Accept-Language")  # pylint: disable=undefined-variable
            return False

        if request.headers.get('Connection') == 'close':
            logger.debug("got Connection=close")  # pylint: disable=undefined-variable
            return False

        accept_encoding_list = [l.strip() for l in request.headers.get('Accept-Encoding', '').split(',')]
        if 'gzip' not in accept_encoding_list and 'deflate' not in accept_encoding_list:
            logger.debug("suspicious Accept-Encoding")  # pylint: disable=undefined-variable
            return False

        if 'text/html' not in request.accept_mimetypes:
            logger.debug("Accept-Encoding misses text/html")  # pylint: disable=undefined-variable
            return False

        if request.args.get('format', 'html') != 'html':
            c = incr_sliding_window(redis_client, 'API limit' + remote_addr, 3600)
            if c > 4:
                logger.debug("API limit exceeded")  # pylint: disable=undefined-variable
                return False
    return True


def pre_request():
    if not is_accepted_request():
        return 'Too Many Requests', 429
    return None


def init_whitelist(limiter_whitelist_ip: List[str], limiter_whitelist_subnet: List[str]):
    global WHITELISTED_IPS, WHITELISTED_SUBNET  # pylint: disable=global-statement
    if isinstance(limiter_whitelist_ip, str):
        limiter_whitelist_ip = [limiter_whitelist_ip]
    if isinstance(limiter_whitelist_subnet, str):
        limiter_whitelist_subnet = [limiter_whitelist_subnet]
    if not isinstance(limiter_whitelist_ip, list):
        raise ValueError('server.limiter_whitelist_ip is not a list')
    if not isinstance(limiter_whitelist_subnet, list):
        raise ValueError('server.limiter_whitelist_subnet is not a list')
    WHITELISTED_IPS = [ipaddress.ip_address(ip) for ip in limiter_whitelist_ip]
    WHITELISTED_SUBNET = [ipaddress.ip_network(subnet, strict=False) for subnet in limiter_whitelist_subnet]


def init(app, settings):
    if not settings['server']['limiter']:
        return False

    if not redisdb.client():
        logger.error("The limiter requires Redis")  # pylint: disable=undefined-variable
        return False

    init_whitelist(
        cast(list, get_setting('server.limiter_whitelist_ip', default=[])),
        cast(list, get_setting('server.limiter_whitelist_subnet', default=[])),
    )

    app.before_request(pre_request)
    return True
