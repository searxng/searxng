# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pyright: basic
"""Some bot protection / rate limitation

To monitor rate limits and protect privacy the IP addresses are getting stored
with a hash so the limiter plugin knows who to block.  A redis database is
needed to store the hash values.

Enable the plugin in ``settings.yml``:

- ``server.limiter: true``
- ``redis.url: ...`` check the value, see :ref:`settings redis`
"""

import re
from flask import request

from searx import redisdb
from searx.plugins import logger
from searx.redislib import incr_sliding_window

name = "Request limiter"
description = "Limit the number of request"
default_on = False
preference_section = 'service'
logger = logger.getChild('limiter')

re_bot = re.compile(
    r'('
    + r'[Cc][Uu][Rr][Ll]|[wW]get|Scrapy|splash|JavaFX|FeedFetcher|python-requests|Go-http-client|Java|Jakarta|okhttp'
    + r'|HttpClient|Jersey|Python|libwww-perl|Ruby|SynHttpClient|UniversalFeedParser|Googlebot|GoogleImageProxy'
    + r'|bingbot|Baiduspider|yacybot|YandexMobileBot|YandexBot|Yahoo! Slurp|MJ12bot|AhrefsBot|archive.org_bot|msnbot'
    + r'|MJ12bot|SeznamBot|linkdexbot|Netvibes|SMTBot|zgrab|James BOT|Sogou|Abonti|Pixray|Spinn3r|SemrushBot|Exabot'
    + r'|ZmEu|BLEXBot|bitlybot'
    + r')'
)


def is_accepted_request() -> bool:
    # pylint: disable=too-many-return-statements
    redis_client = redisdb.client()
    user_agent = request.headers.get('User-Agent', '')
    x_forwarded_for = request.headers.get('X-Forwarded-For', '')

    if re_bot.match(user_agent):
        logger.debug("BLOCK %s: detected bot", x_forwarded_for)
        return False

    if request.path == '/search':
        c_burst = incr_sliding_window(redis_client, 'IP limit, burst' + x_forwarded_for, 20)
        c_10min = incr_sliding_window(redis_client, 'IP limit, 10 minutes' + x_forwarded_for, 600)
        if c_burst > 15 or c_10min > 150:
            logger.debug("BLOCK %s: to many request", x_forwarded_for)
            return False

        if len(request.headers.get('Accept-Language', '').strip()) == '':
            logger.debug("BLOCK %s: missing Accept-Language", x_forwarded_for)
            return False

        if request.headers.get('Connection') == 'close':
            logger.debug("BLOCK %s: got Connection=close", x_forwarded_for)
            return False

        accept_encoding_list = [l.strip() for l in request.headers.get('Accept-Encoding', '').split(',')]
        if 'gzip' not in accept_encoding_list and 'deflate' not in accept_encoding_list:
            logger.debug("BLOCK %s: suspicious Accept-Encoding", x_forwarded_for)
            return False

        if 'text/html' not in request.accept_mimetypes:
            logger.debug("BLOCK %s: Accept-Encoding misses text/html", x_forwarded_for)
            return False

        if request.args.get('format', 'html') != 'html':
            c = incr_sliding_window(redis_client, 'API limit' + x_forwarded_for, 3600)
            if c > 4:
                logger.debug("BLOCK %s: API limit exceeded", x_forwarded_for)
                return False

    logger.debug(
        "OK %s: '%s'" % (x_forwarded_for, request.path)
        + " || form: %s" % request.form
        + " || Accept: %s" % request.headers.get('Accept', '')
        + " || Accept-Language: %s" % request.headers.get('Accept-Language', '')
        + " || Accept-Encoding: %s" % request.headers.get('Accept-Encoding', '')
        + " || Content-Type: %s" % request.headers.get('Content-Type', '')
        + " || Content-Length: %s" % request.headers.get('Content-Length', '')
        + " || Connection: %s" % request.headers.get('Connection', '')
        + " || User-Agent: %s" % user_agent
    )

    return True


def pre_request():
    if not is_accepted_request():
        return 'Too Many Requests', 429
    return None


def init(app, settings):
    if not settings['server']['limiter']:
        return False

    if not redisdb.client():
        logger.error("The limiter requires Redis")  # pylint: disable=undefined-variable
        return False

    app.before_request(pre_request)
    return True
