# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pyright: basic
"""Rate limit outgoing requests per engine

Enable ``settings.yml``:

- ``redis.url: ...`` check the value, see :ref:`settings redis`
- ``rate_limit: ...`` max_requests and interval, as specified below
- ``max_requests: ...`` max number of requests for that engine per interval
- ``interval: ...`` number of seconds before rate limiting resets (optional, by default 1 second)
"""

import hmac

from searx import settings
from searx.engines import engines
from searx.shared import redisdb

name = "Engine rate limiter"
description = "Limit the number of outgoing requests per engine"
default_on = True
preference_section = 'service'


def check_rate_limiter(engine_name, limit, interval):
    redis_client = redisdb.client()
    lua_script = """
    local engine = KEYS[1]
    local limit = ARGV[1]
    local interval = ARGV[2]

    local count = redis.call('GET', engine)
    if count and count > limit then
        return count
    else
        local newCount = redis.call('INCR', engine)
        if newCount == 1 then
            redis.call('EXPIRE', engine, interval)
        end
        return newCount
    end
    """
    script_sha = redis_client.script_load(lua_script)

    secret_key_bytes = bytes(settings['server']['secret_key'], encoding='utf-8')
    m = hmac.new(secret_key_bytes, digestmod='sha256')
    m.update(bytes(engine_name, encoding='utf-8'))
    key = m.digest()

    requestsCounter = redis_client.evalsha(script_sha, 1, key, limit, interval)
    return int(requestsCounter)


def below_rate_limit(engine_name):
    engine = engines[engine_name]
    max_requests = engine.rate_limit['max_requests']
    interval = engine.rate_limit['interval']

    if max_requests == float('inf'):
        return True
    if max_requests >= check_rate_limiter(engine_name, max_requests, interval):
        return True
    logger.debug(f"{engine_name} exceeded rate limit of {max_requests} requests per {interval} seconds")  # pylint: disable=undefined-variable
    return False


def pre_search(_, search):
    allowed_engines = list(filter(lambda e: below_rate_limit(e.name), search.search_query.engineref_list))
    search.search_query.engineref_list = allowed_engines
    return bool(allowed_engines)


def init(*args, **kwargs):  # pylint: disable=unused-argument
    logger.debug("init engine rate limiter DB")  # pylint: disable=undefined-variable
    if not redisdb.init():
        logger.error("init engine rate limiter DB failed!!!")  # pylint: disable=undefined-variable
        return False
    return True
