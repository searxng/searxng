# SPDX-License-Identifier: AGPL-3.0-or-later
"""A collection of convenient functions and redis/lua scripts.

This code was partial inspired by the `Bullet-Proofing Lua Scripts in RedisPy`_
article.

.. _Bullet-Proofing Lua Scripts in RedisPy:
   https://redis.com/blog/bullet-proofing-lua-scripts-in-redispy/

"""
from __future__ import annotations
from typing import Tuple, List, Iterable

from ipaddress import IPv4Network, IPv6Network
import hmac
import redis

from searx import get_setting

LUA_SCRIPT_STORAGE = {}
"""A global dictionary to cache client's ``Script`` objects, used by
:py:obj:`lua_script_storage`"""


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

    .. _EXPIRE: https://redis.io/commands/expire/
    .. _DEL: https://redis.io/commands/del/

    """
    script = lua_script_storage(client, PURGE_BY_PREFIX)
    script(args=[prefix])


def secret_hash(name: str):
    """Creates a hash of the ``name``.

    Combines argument ``name`` with the ``secret_key`` from :ref:`settings
    server`.  This function can be used to get a more anonymized name of a Redis
    KEY.

    :param name: the name to create a secret hash for
    :type name: str
    """
    m = hmac.new(bytes(name, encoding='utf-8'), digestmod='sha256')
    m.update(bytes(get_setting('server.secret_key'), encoding='utf-8'))  # type: ignore
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

    If counter with redis key ``SearXNG_counter_<name>`` does not exists it is
    created with initial value 1 returned.  The replacement ``<name>`` is a
    *secret hash* of the value from argument ``name`` (see
    :py:func:`secret_hash`).

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
    name = "SearXNG_counter_" + secret_hash(name)
    c = script(args=[limit, expire], keys=[name])
    return c


def drop_counter(client, name):
    """Drop counter with redis key ``SearXNG_counter_<name>``

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

    If counter with redis key ``SearXNG_counter_<name>`` does not exists it is
    created with initial value 1 returned.  The replacement ``<name>`` is a
    *secret hash* of the value from argument ``name`` (see
    :py:func:`secret_hash`).

    :param name: name of the counter
    :type name: str

    :param duration: live-time of the sliding window in seconds
    :typeduration: int

    :return: value of the incremented counter
    :type return: int

    The implementation of the redis counter is the lua script from string
    :py:obj:`INCR_SLIDING_WINDOW`.  The lua script uses `sorted sets in Redis`_
    to implement a sliding window for the redis key ``SearXNG_counter_<name>``
    (ZADD_).  The current TIME_ is used to score the items in the sorted set and
    the time window is moved by removing items with a score lower current time
    minus *duration* time (ZREMRANGEBYSCORE_).

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
    name = "SearXNG_counter_" + secret_hash(name)
    c = script(args=[duration], keys=[name])
    return c


class RangeReader:
    """Base class of readers passed to :py:obj:`RangeTable.init_table`."""

    # pylint: disable=too-few-public-methods

    def __init__(self, table: List[Tuple[(int, int)]]):
        self._table = table

    @property
    def table(self) -> List[Tuple[(int, int)]]:
        """Returns a table by a list of tuples (table's rows) with a *start*
        value of the range and a *end* value.  The values of *start* and *end*
        column are integers."""
        return self._table


class IPNetworkReader(RangeReader):
    """A reader for :py:obj:`RangeTable` that is build up from a list of
    :py:obj:`IPv4Network` and :py:obj:`IPv6Network` items.

    .. code:: python

       >>> from ipaddress import IPv4Network, ip_address
       >>> from searx import redislib
       >>> reader = redislib.IPNetworkReader([
               IPv4Network('192.169.0.42/32'),
               IPv4Network('192.169.1.0/24'),
       ])
       >>> ipv4_ranges = redislib.RangeTable('ipv4_ranges', client)
       >>> ipv4_ranges.init_table(reader)

    A IP lookup can be done by :py:obj`RangeTable.in_range`:

    .. code:: python

       >>> ipv4_ranges.in_range(int(ip_address('192.169.0.42')))
       True
       >>> ipv4_ranges.in_range(int(ip_address('192.169.0.41')))
       False
       >>> ipv4_ranges.in_range(int(ip_address('192.169.0.43')))
       False
       >>> ipv4_ranges.in_range(int(ip_address('192.169.1.43')))
       True

    """

    # pylint: disable=too-few-public-methods, super-init-not-called

    def __init__(self, table: List[IPv4Network | IPv6Network]):
        self._table = table

    @property
    def table(self) -> Iterable[Tuple[(int, int)]]:
        """Yields rows of a table where the *start* value of the range is the
        integer of the ``net.network_address`` and the *end* value is the
        integer of the ``net.broadcast_address``.
        """

        for net in self._table:
            yield (int(net.network_address), int(net.broadcast_address))


class RangeTable:
    """.. sidebar: info

       - ZRANGEBYSCORE_
       - client.zrangebyscore_

    A table of ranges.  A range is a tuple with a *start* value of the range
    and a *end* value.  The values of *start* and *end* column are integers.  By
    example, the tuple ``(0, 10)`` is a range that includes 11 integers from 0
    to 10 (includes 0 and 10).

    The table of ranges is stored in the redis DB by a set with scores (aka
    `sorted set`).  For ultrafast lookups if a score is in a range
    ZRANGEBYSCORE_ is used (client.zrangebyscore_).

    A table is loaded into the redis DB by :py:obj:`RangeTable.init_table`
    (client.zadd_).

    .. tabs::

       .. group-tab:: redis-py

          .. code:: python

             >>> from searx import redisdb
             >>> from searx import redislib
             >>> redisdb.initialize()
             True
             >>> client = redisdb.client()

          .. code:: python

             >>> table_0_100 = [
             ...     (0, 10),    # range starts by 0 and ends in 10
             ...     (10, 19),   # range starts by 10 and ends in 19
             ...     (20, 97),   # range starts by 20 and ends in 97
             ... ]
             >>> my_table = redislib.RangeTable('mytable', client)
             >>> reader = redislib.RangeReader(table_0_100)
             >>> my_table.init_table(reader)

       .. group-tab:: REDIS

          The analogous redis command would be:

          .. code::

              ZADD SearXNG_range_table_my_table 10 "0-10" 19 "10-19"  97 "20-97"

    In the example above, a value of 10 is in two ranges: ``(0, 10)`` and ``(10,
    19)``.  Only the first range that matches ``(0, 10)`` will be returned by
    :py:obj:`RangeTable.get_range_of` (the second range 10 is in, is
    ``(10, 19)`` but is not returned).


    .. tabs::

       .. group-tab:: redis-py

          .. code:: python

             >>> my_table.get_range_of(5)
             (0, 10)
             >>> my_table.get_range_of(10)
             (0, 10)

          .. code:: python

             >>> my_table.in_range(5)
             True
             >>> my_table.in_range(10)
             True

       .. group-tab:: REDIS

          .. code::

             ZRANGEBYSCORE SearXNG_range_table_my_table 5 +inf LIMIT 0 1
               --> '0-10'
             ZRANGEBYSCORE SearXNG_range_table_my_table 10 +inf LIMIT 0 1
               --> '0-10'

    The value 19 is only in one range: ``(10, 19)``:

    .. tabs::

       .. group-tab:: redis-py

          .. code:: python

             >>> my_table.get_range_of(19)
             (10, 19)

       .. group-tab:: REDIS

          .. code::

             ZRANGEBYSCORE SearXNG_range_table_my_table 19 +inf LIMIT 0 1
               --> '10-19'


    A value of ``>97`` is not in any range:

    .. tabs::

       .. group-tab:: redis-py

          .. code:: python

             >>> my_table.get_range_of(97)
             (20, 97)
             >>> my_table.get_range_of(98) is None
             True

       .. group-tab:: REDIS

          .. code::

             ZRANGEBYSCORE SearXNG_range_table_my_table 19 +inf LIMIT 0 1
               --> '20-97'
             ZRANGEBYSCORE SearXNG_range_table_my_table 98 +inf LIMIT 0 1
               --> (empty array)



    .. _Checking if IP falls within a range with Redis:
       https://stackoverflow.com/questions/33015904/checking-if-ip-falls-within-a-range-with-redis/33020687#33020687
    .. _sorted set:
       https://redis.io/docs/data-types/sorted-sets/
    .. _ZRANGEBYSCORE:
       https://redis.io/commands/zrangebyscore/
    .. _client.zrangebyscore:
       https://redis-py-doc.readthedocs.io/en/master/#redis.Redis.zrangebyscore
    .. _client.zadd:
       https://redis-py-doc.readthedocs.io/en/master/#redis.Redis.zadd

    """

    def __init__(self, table_name: str, client: redis.Redis):
        self.table_name = f"SearXNG_range_table_{table_name}"
        self.client = client

    def get_range_of(self, score: int) -> Tuple[int, int] | None:
        """Find and return a range in this table where score is in.  Only the
        first range that matches will be returned (by example ``(0, 10)``).  If
        score is not in any of the ranges, ``None`` is returned.
        """
        member = self.client.zrangebyscore(
            name=self.table_name,
            max='+inf',
            min=score,
            start=0,
            num=1,
        )

        if not member:
            return None
        start, end = [int(x) for x in member[0].decode('utf-8').split('-')]
        if score >= start:
            # score is in range ..
            return (start, end)
        return None

    def in_range(self, score: int) -> bool:
        """Returns ``True`` when score is in one ore more *start*, *end* ranges.
        If not, ``False`` is returned.
        """
        return bool(self.get_range_of(score))

    def init_table(self, reader: RangeReader):
        """Init table by a list of tuples (table's rows) with a *start* value of
        the range and a *end* value.
        """
        mapping = {}
        for start, end in reader.table:
            mapping[f"{start}-{end}"] = end
        self.client.zadd(self.table_name, mapping=mapping)
