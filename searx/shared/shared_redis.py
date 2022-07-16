# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Scheduler:
* use only the time from Redis
* use two HSET on Redis:
  * SearXNG_scheduler: for each function, the timestamp of the next call
  * SearXNG_scheduler_delay: for each function, the delay between the calls

Two Lua scripts:
* SCHEDULER_REGISTER_FUNCTION registers a new function to call
* SCHEDULER_NOW_SCRIPT has to be called in loop. It returns two values:
  * the number of seconds to wait before making a new call to this script
  * the list of function to call now. 
    This list won't be returned anymore: the script except the Python worker to call these functions.
    If there are multiple worker, the functions are called only once for all the worker. 
    This script can be called before the expected time without side effect.
    This is useful when a new function is scheduled.
"""

import threading
from typing import NamedTuple, Optional, Dict, List, Any
import logging

from . import shared_abstract
from .redisdb import client as get_redis_client
from ..redislib import lua_script_storage
from searx import redislib


logger = logging.getLogger('searx.shared.shared_redis')


class ScheduleInfo(NamedTuple):
    func: Any
    args: List[Any]


SCHEDULED_FUNCTIONS: Dict[str, ScheduleInfo] = {}
SCHEDULER_THREAD: Optional[threading.Thread] = None
SCHEDULER_EVENT = threading.Event()

SCHEDULER_COMMON_VARIABLES = """
local hash_key = 'SearXNG_scheduler_ts'
local hash_delay_key = 'SearXNG_scheduler_delay'
"""

SCHEDULER_REGISTER_FUNCTION = (
    SCHEDULER_COMMON_VARIABLES
    + """
local now = redis.call('TIME')[1]
local redis_key = KEYS[1]
local delay = ARGV[1]
redis.call('HSET', hash_key, redis_key, now + delay)
redis.call('HSET', hash_delay_key, redis_key, delay)
"""
)

SCHEDULER_NOW_SCRIPT = (
    SCHEDULER_COMMON_VARIABLES
    + """
local now = redis.call('TIME')[1]
local result = {}
local next_call_ts_list = {}

local flat_map = redis.call('HGETALL', hash_key)
for i = 1, #flat_map, 2 do
    -- 
    local redis_key = flat_map[i]
    local next_call_ts = flat_map[i + 1]
    -- do we have to call the function now?
    if next_call_ts <= now then
        -- the function must be called now
        table.insert(result, redis_key)
        -- schedule the next call of the function
        local delay = redis.call('HGET', hash_delay_key, redis_key)
        next_call_ts = redis.call('HINCRBY', hash_key, redis_key, delay)
    end
    -- update next_call_ts_list
    -- so later, we can get the minimum value of next_call_ts_list
    table.insert(next_call_ts_list, next_call_ts)
end

-- the first result contains the delay before the next call to this script
local next_call_min_ts = math.min(unpack(next_call_ts_list))
local next_call_delay = next_call_min_ts - now
table.insert(result, 1, next_call_delay)

return result
"""
)


def scheduler_loop():
    while SCHEDULER_THREAD == threading.current_thread():
        script = lua_script_storage(get_redis_client(), SCHEDULER_NOW_SCRIPT)
        result = script()

        next_call_delay = result.pop(0)

        # call functions
        for redis_key in result:
            redis_key = redis_key.decode()
            info = SCHEDULED_FUNCTIONS[redis_key]
            try:
                logger.debug('Run %s', redis_key)
                info.func(*info.args)
            except Exception:
                logger.exception("Error calling %s", redis_key)

        # wait for the time defined by the Redis script (next_call_delay)
        # or continue if another function has been scheduled (SCHEDULER_EVENT.set())
        SCHEDULER_EVENT.clear()
        SCHEDULER_EVENT.wait(timeout=next_call_delay)


def schedule(delay, func, *args):
    global SCHEDULER_THREAD

    redis_key = func.__module__ + '.' + func.__qualname__
    SCHEDULED_FUNCTIONS[redis_key] = ScheduleInfo(func, args)
    script = lua_script_storage(get_redis_client(), SCHEDULER_REGISTER_FUNCTION)
    script(args=[delay], keys=[redis_key])
    #
    if SCHEDULER_THREAD is not None:
        # the scheduler thread has been started : update the waiting time
        SCHEDULER_EVENT.set()
    else:
        # start the scheduler thread
        SCHEDULER_THREAD = threading.Thread(target=scheduler_loop, name='scheduler')
        SCHEDULER_THREAD.daemon = True
        SCHEDULER_THREAD.start()
    return True


def reset_scheduler():
    global SCHEDULER_THREAD
    # stop the scheduler thread
    SCHEDULER_THREAD = None
    SCHEDULER_EVENT.set()
    # erase Redis keys
    redislib.purge_by_prefix(get_redis_client(), 'SearXNG_scheduler_')


class RedisCacheSharedDict(shared_abstract.SharedDict):
    def get_int(self, key: str) -> Optional[int]:
        return int(get_redis_client().get(key))

    def set_int(self, key: str, value: int):
        get_redis_client().set(key, str(value).encode())

    def get_str(self, key: str) -> Optional[str]:
        value = get_redis_client().get(key)
        return None if value is None else value.decode()

    def set_str(self, key: str, value: str):
        get_redis_client().set(key, value.encode())
