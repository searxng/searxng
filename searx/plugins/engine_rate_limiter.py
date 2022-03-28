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

    key = f'rate_limiter_{engine_name}_{limit}r/{interval}s'.encode()
    requestsCounter = redis_client.evalsha(script_sha, 1, key, limit, interval)
    return int(requestsCounter)


def below_rate_limit(engine_name):
    engine = engines[engine_name]
    is_below_rate_limit = True
    for rate_limit in engine.rate_limit:
        max_requests = rate_limit['max_requests']
        interval = rate_limit['interval']
        if max_requests == float('inf'):
            continue
        if max_requests < check_rate_limiter(engine_name, max_requests, interval):
            is_below_rate_limit = False
            logger.debug(f"{engine_name} exceeded rate limit of {max_requests} requests per {interval} seconds")  # pylint: disable=undefined-variable

    return is_below_rate_limit


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
