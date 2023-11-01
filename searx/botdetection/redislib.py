# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""A collection of convenient functions and redis/lua scripts.

This code was partial inspired by the `Bullet-Proofing Lua Scripts in RedisPy`_
article.

.. _Bullet-Proofing Lua Scripts in RedisPy:
   https://redis.com/blog/bullet-proofing-lua-scripts-in-redispy/

Config
~~~~~~

.. code:: toml

   [botdetection.redis]

   # FQDN of a function definition. A function with which the DB keys of the Redis
   # DB are to be annonymized.
   secret_hash = ''

   # A prefix to all keys store by the botdetection in the redis DB
   REDIS_KEY_PREFIX = 'botdetection_'


Implementations
~~~~~~~~~~~~~~~
"""

from __future__ import annotations

from . import ctx

REDIS_KEY_PREFIX = 'botdetection'
"""A prefix applied to all keys store by the botdetection in the redis DB."""

LUA_SCRIPT_STORAGE = {}
"""A global dictionary to cache client's ``Script`` objects, used by
:py:obj:`lua_script_storage`"""


def secret_hash(name: str) -> str:
    """Returns a annonymized name if ``secret_hash`` is configured, otherwise
    the ``name`` is returned unchanged."""
    func = ctx.cfg.pyobj('botdetection.redis.secret_hash', default=None)  # type: ignore
    if not func:
        return name
    return func(name)


def _prefix(val: str | None = None) -> str:
    if val is None:
        val = ctx.cfg.get('botdetection.redis.REDIS_KEY_PREFIX', default=REDIS_KEY_PREFIX)  # type: ignore
    return str(val)


def lua_script_storage(client, script):
    """Returns a redis :py:obj:`Script
    <redis.commands.core.CoreCommands.register_script>` instance.

    Due to performance reason the ``Script`` object is instantiated only once
    for a client (``client.register_script(..)``) and is cached in
    :py:obj:`LUA_SCRIPT_STORAGE`.

    """

    # redis connection can be closed, lets use the id() of the redis connector
    # as key in the script-storage:
    client_id = id(client)

    if LUA_SCRIPT_STORAGE.get(client_id) is None:
        LUA_SCRIPT_STORAGE[client_id] = {}

    if LUA_SCRIPT_STORAGE[client_id].get(script) is None:
        LUA_SCRIPT_STORAGE[client_id][script] = client.register_script(script)

    return LUA_SCRIPT_STORAGE[client_id][script]


PURGE_BY_PREFIX = """
local prefix = tostring(ARGV[1])
for i, name in ipairs(redis.call('KEYS', prefix .. '*')) do
    redis.call('EXPIRE', name, 0)
end
"""


def purge_by_prefix(client, prefix: str | None):
    """Purge all keys with ``prefix`` from database.

    Queries all keys in the database by the given prefix and set expire time to
    zero.  The default prefix will drop all keys which has been set by
    :py:obj:`REDIS_KEY_PREFIX`.

    The implementation is the lua script from string :py:obj:`PURGE_BY_PREFIX`.
    The lua script uses EXPIRE_ instead of DEL_: if there are a lot keys to
    delete and/or their values are big, `DEL` could take more time and blocks
    the command loop while `EXPIRE` turns back immediate.

    :param prefix: prefix of the key to delete (default: :py:obj:`REDIS_KEY_PREFIX`)
    :type name: str

    .. _EXPIRE: https://redis.io/commands/expire/
    .. _DEL: https://redis.io/commands/del/

    """
    script = lua_script_storage(client, PURGE_BY_PREFIX)
    script(args=[_prefix(prefix)])


INCR_COUNTER = """
local limit = tonumber(ARGV[1])
local expire = tonumber(ARGV[2])
local c_name = KEYS[1]

local c = redis.call('GET', c_name)

if not c then
    c = redis.call('INCR', c_name)
    if expire > 0 then
        redis.call('EXPIRE', c_name, expire)
    end
else
    c = tonumber(c)
    if limit == 0 or c < limit then
       c = redis.call('INCR', c_name)
    end
end
return c
"""


def incr_counter(client, name: str, limit: int = 0, expire: int = 0):
    """Increment a counter and return the new value.

    If counter with redis key :py:obj:`REDIS_KEY_PREFIX` + ``counter_<name>``
    does not exists it is created with initial value 1 returned.  The
    replacement ``<name>`` is a *secret hash* of the value from argument
    ``name`` (see :py:func:`secret_hash`).

    The implementation of the redis counter is the lua script from string
    :py:obj:`INCR_COUNTER`.

    :param name: name of the counter
    :type name: str

    :param expire: live-time of the counter in seconds (default ``None`` means
      infinite).
    :type expire: int / see EXPIRE_

    :param limit: limit where the counter stops to increment (default ``None``)
    :type limit: int / limit is 2^64 see INCR_

    :return: value of the incremented counter
    :type return: int

    .. _EXPIRE: https://redis.io/commands/expire/
    .. _INCR: https://redis.io/commands/incr/

    A simple demo of a counter with expire time and limit::

      >>> for i in range(6):
      ...   i, incr_counter(client, "foo", 3, 5) # max 3, duration 5 sec
      ...   time.sleep(1) # from the third call on max has been reached
      ...
      (0, 1)
      (1, 2)
      (2, 3)
      (3, 3)
      (4, 3)
      (5, 1)

    """
    script = lua_script_storage(client, INCR_COUNTER)
    name = _prefix() + "counter_" + secret_hash(name)
    c = script(args=[limit, expire], keys=[name])
    return c


def drop_counter(client, name):
    """Drop counter with redis key :py:obj:`REDIS_KEY_PREFIX` +
    ``counter_<name>``

    The replacement ``<name>`` is a *secret hash* of the value from argument
    ``name`` (see :py:func:`incr_counter` and :py:func:`incr_sliding_window`).

    """
    name = _prefix() + "counter_" + secret_hash(name)
    client.delete(name)


INCR_SLIDING_WINDOW = """
local expire = tonumber(ARGV[1])
local name = KEYS[1]
local current_time = redis.call('TIME')

redis.call('ZREMRANGEBYSCORE', name, 0, current_time[1] - expire)
redis.call('ZADD', name, current_time[1], current_time[1] .. current_time[2])
local result = redis.call('ZCOUNT', name, 0, current_time[1] + 1)
redis.call('EXPIRE', name, expire)
return result
"""


def incr_sliding_window(client, name: str, duration: int):
    """Increment a sliding-window counter and return the new value.

    If counter with redis key :py:obj:`REDIS_KEY_PREFIX` + ``counter_<name>``
    does not exists it is created with initial value 1 returned.  The
    replacement ``<name>`` is a *secret hash* of the value from argument
    ``name`` (see :py:func:`secret_hash`).

    :param name: name of the counter
    :type name: str

    :param duration: live-time of the sliding window in seconds
    :typeduration: int

    :return: value of the incremented counter
    :type return: int

    The implementation of the redis counter is the lua script from string
    :py:obj:`INCR_SLIDING_WINDOW`.  The lua script uses `sorted sets in Redis`_
    to implement a sliding window for the redis key :py:obj:`REDIS_KEY_PREFIX` +
    ``counter_<name>`` (ZADD_).  The current TIME_ is used to score the items in
    the sorted set and the time window is moved by removing items with a score
    lower current time minus *duration* time (ZREMRANGEBYSCORE_).

    The EXPIRE_ time (the duration of the sliding window) is refreshed on each
    call (increment) and if there is no call in this duration, the sorted
    set expires from the redis DB.

    The return value is the amount of items in the sorted set (ZCOUNT_), what
    means the number of calls in the sliding window.

    .. _Sorted sets in Redis:
       https://redis.com/ebook/part-1-getting-started/chapter-1-getting-to-know-redis/1-2-what-redis-data-structures-look-like/1-2-5-sorted-sets-in-redis/
    .. _TIME: https://redis.io/commands/time/
    .. _ZADD: https://redis.io/commands/zadd/
    .. _EXPIRE: https://redis.io/commands/expire/
    .. _ZREMRANGEBYSCORE: https://redis.io/commands/zremrangebyscore/
    .. _ZCOUNT: https://redis.io/commands/zcount/

    A simple demo of the sliding window::

      >>> for i in range(5):
      ...   incr_sliding_window(client, "foo", 3) # duration 3 sec
      ...   time.sleep(1) # from the third call (second) on the window is moved
      ...
      1
      2
      3
      3
      3
      >>> time.sleep(3)  # wait until expire
      >>> incr_sliding_window(client, "foo", 3)
      1

    """
    script = lua_script_storage(client, INCR_SLIDING_WINDOW)
    name = _prefix() + "counter_" + secret_hash(name)
    c = script(args=[duration], keys=[name])
    return c
