# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pyright: basic
"""Some bot protection / rate limitation

Enable the plugin in ``settings.yml``:

- ``server.limiter: true``
- ``redis.url: ...`` check the value, see :ref:`settings redis`
"""

import hmac
import re
from flask import request

from searx.shared import redisdb

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


def is_accepted_request(inc_get_counter) -> bool:
    # pylint: disable=too-many-return-statements
    user_agent = request.headers.get('User-Agent', '')
    x_forwarded_for = request.headers.get('X-Forwarded-For', '')

    if request.path == '/image_proxy':
        if re_bot.match(user_agent):
            return False
        return True

    if request.path == '/search' and ('q' in request.args or 'q' in request.form):
        c = inc_get_counter(interval=20, keys=[b'IP limit, burst', x_forwarded_for])
        if c > 30:
            return False

        c = inc_get_counter(interval=600, keys=[b'IP limit, 10 minutes', x_forwarded_for])
        if c > 300:
            return False

        if re_bot.match(user_agent):
            return False

        if 'Accept-Language' not in request.headers:
            return False

        if request.headers.get('Connection') == 'close':
            return False

        accept_encoding_list = [l.strip() for l in request.headers.get('Accept-Encoding', '').split(',')]
        if 'gzip' not in accept_encoding_list or 'deflate' not in accept_encoding_list:
            return False

        if 'text/html' not in request.accept_mimetypes:
            return False

        if request.args.get('format', 'html') != 'html':
            c = inc_get_counter(interval=3600, keys=[b'API limit', x_forwarded_for])
            if c > 4:
                return False
    return True


def create_inc_get_counter(redis_client, secret_key_bytes):
    lua_script = """
    local slidingWindow = KEYS[1]
    local key = KEYS[2]
    local now = tonumber(redis.call('TIME')[1])
    local id = redis.call('INCR', 'counter')
    if (id > 2^46)
    then
        redis.call('SET', 'count', 0)
    end
    redis.call('ZREMRANGEBYSCORE', key, 0, now - slidingWindow)
    redis.call('ZADD', key, now, id)
    local result = redis.call('ZCOUNT', key, 0, now+1)
    redis.call('EXPIRE', key, slidingWindow)
    return result
    """
    script_sha = redis_client.script_load(lua_script)

    def inc_get_counter(interval, keys):
        m = hmac.new(secret_key_bytes, digestmod='sha256')
        for k in keys:
            m.update(bytes(str(k), encoding='utf-8') or b'')
            m.update(b"\0")
        key = m.digest()
        return redis_client.evalsha(script_sha, 2, interval, key)

    return inc_get_counter


def create_pre_request(get_aggregation_count):
    def pre_request():
        if not is_accepted_request(get_aggregation_count):
            return '', 429
        return None

    return pre_request


def init(app, settings):

    if not settings['server']['limiter']:
        return False

    logger.debug("init limiter DB")  # pylint: disable=undefined-variable
    if not redisdb.init():
        logger.error("init limiter DB failed!!!")  # pylint: disable=undefined-variable
        return False

    redis_client = redisdb.client()
    secret_key_bytes = bytes(settings['server']['secret_key'], encoding='utf-8')
    inc_get_counter = create_inc_get_counter(redis_client, secret_key_bytes)
    app.before_request(create_pre_request(inc_get_counter))
    return True
