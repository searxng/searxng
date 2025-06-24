# SPDX-License-Identifier: AGPL-3.0-or-later
"""A collection of convenient functions and valkey/lua scripts.

This code was partial inspired by the `Bullet-Proofing Lua Scripts in ValkeyPy`_
article.

.. _Bullet-Proofing Lua Scripts in ValkeyPy:
   https://redis.com/blog/bullet-proofing-lua-scripts-in-redispy/

"""

import hmac

from searx import get_setting

LUA_SCRIPT_STORAGE = {}
"""A global dictionary to cache client's ``Script`` objects, used by
:py:obj:`lua_script_storage`"""


def lua_script_storage(client, script):
    """Returns a valkey :py:obj:`Script
    <valkey.commands.core.CoreCommands.register_script>` instance.

    Due to performance reason the ``Script`` object is instantiated only once
    for a client (``client.register_script(..)``) and is cached in
    :py:obj:`LUA_SCRIPT_STORAGE`.

    """

    # valkey connection can be closed, lets use the id() of the valkey connector
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


def purge_by_prefix(client, prefix: str = "SearXNG_"):
    """Purge all keys with ``prefix`` from database.

    Queries all keys in the database by the given prefix and set expire time to
    zero.  The default prefix will drop all keys which has been set by SearXNG
    (drops SearXNG schema entirely from database).

    The implementation is the lua script from string :py:obj:`PURGE_BY_PREFIX`.
    The lua script uses EXPIRE_ instead of DEL_: if there are a lot keys to
    delete and/or their values are big, `DEL` could take more time and blocks
    the command loop while `EXPIRE` turns back immediate.

    :param prefix: prefix of the key to delete (default: ``SearXNG_``)
    :type name: str

    .. _EXPIRE: https://valkey.io/commands/expire/
    .. _DEL: https://valkey.io/commands/del/

    """
    script = lua_script_storage(client, PURGE_BY_PREFIX)
    script(args=[prefix])


def secret_hash(name: str):
    """Creates a hash of the ``name``.

    Combines argument ``name`` with the ``secret_key`` from :ref:`settings
    server`.  This function can be used to get a more anonymized name of a Valkey
    KEY.

    :param name: the name to create a secret hash for
    :type name: str
    """
    m = hmac.new(bytes(name, encoding='utf-8'), digestmod='sha256')
    m.update(bytes(get_setting('server.secret_key'), encoding='utf-8'))
    return m.hexdigest()


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

    If counter with valkey key ``SearXNG_counter_<name>`` does not exists it is
    created with initial value 1 returned.  The replacement ``<name>`` is a
    *secret hash* of the value from argument ``name`` (see
    :py:func:`secret_hash`).

    The implementation of the valkey counter is the lua script from string
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

    .. _EXPIRE: https://valkey.io/commands/expire/
    .. _INCR: https://valkey.io/commands/incr/

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
    name = "SearXNG_counter_" + secret_hash(name)
    c = script(args=[limit, expire], keys=[name])
    return c


def drop_counter(client, name):
    """Drop counter with valkey key ``SearXNG_counter_<name>``

    The replacement ``<name>`` is a *secret hash* of the value from argument
    ``name`` (see :py:func:`incr_counter` and :py:func:`incr_sliding_window`).
    """
    name = "SearXNG_counter_" + secret_hash(name)
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

    If counter with valkey key ``SearXNG_counter_<name>`` does not exists it is
    created with initial value 1 returned.  The replacement ``<name>`` is a
    *secret hash* of the value from argument ``name`` (see
    :py:func:`secret_hash`).

    :param name: name of the counter
    :type name: str

    :param duration: live-time of the sliding window in seconds
    :typeduration: int

    :return: value of the incremented counter
    :type return: int

    The implementation of the valkey counter is the lua script from string
    :py:obj:`INCR_SLIDING_WINDOW`.  The lua script uses `sorted sets in Valkey`_
    to implement a sliding window for the valkey key ``SearXNG_counter_<name>``
    (ZADD_).  The current TIME_ is used to score the items in the sorted set and
    the time window is moved by removing items with a score lower current time
    minus *duration* time (ZREMRANGEBYSCORE_).

    The EXPIRE_ time (the duration of the sliding window) is refreshed on each
    call (increment) and if there is no call in this duration, the sorted
    set expires from the valkey DB.

    The return value is the amount of items in the sorted set (ZCOUNT_), what
    means the number of calls in the sliding window.

    .. _Sorted sets in Valkey:
       https://valkey.com/ebook/part-1-getting-started/chapter-1-getting-to-know-valkey/1-2-what-valkey-data-structures-look-like/1-2-5-sorted-sets-in-valkey/
    .. _TIME: https://valkey.io/commands/time/
    .. _ZADD: https://valkey.io/commands/zadd/
    .. _EXPIRE: https://valkey.io/commands/expire/
    .. _ZREMRANGEBYSCORE: https://valkey.io/commands/zremrangebyscore/
    .. _ZCOUNT: https://valkey.io/commands/zcount/

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
    name = "SearXNG_counter_" + secret_hash(name)
    c = script(args=[duration], keys=[name])
    return c
