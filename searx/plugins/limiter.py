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

from searx.shared import redisdb
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


def is_accepted_request() -> bool:
    # pylint: disable=too-many-return-statements
    redis_client = redisdb.client()
    user_agent = request.headers.get('User-Agent', '')
    x_forwarded_for = request.headers.get('X-Forwarded-For', '')

    if request.path == '/image_proxy':
        if re_bot.match(user_agent):
            return False
        return True

    if request.path == '/search':
        c_burst = incr_sliding_window(redis_client, 'IP limit, burst' + x_forwarded_for, 20)
        c_10min = incr_sliding_window(redis_client, 'IP limit, 10 minutes' + x_forwarded_for, 600)
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
        if 'gzip' not in accept_encoding_list or 'deflate' not in accept_encoding_list:
            logger.debug("suspicious Accept-Encoding")  # pylint: disable=undefined-variable
            return False

        if 'text/html' not in request.accept_mimetypes:
            logger.debug("Accept-Encoding misses text/html")  # pylint: disable=undefined-variable
            return False

        if request.args.get('format', 'html') != 'html':
            c = incr_sliding_window(redis_client, 'API limit' + x_forwarded_for, 3600)
            if c > 4:
                logger.debug("API limit exceeded")  # pylint: disable=undefined-variable
                return False
    return True


def pre_request():
    if not is_accepted_request():
        return '', 429
    return None


def init(app, settings):
    if not settings['server']['limiter']:
        return False

    logger.debug("init limiter DB")  # pylint: disable=undefined-variable
    if not redisdb.init():
        logger.error("init limiter DB failed!!!")  # pylint: disable=undefined-variable
        return False

    app.before_request(pre_request)
    return True
