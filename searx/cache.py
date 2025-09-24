"""Implementation of caching solutions.

- :py:obj:`searx.cache.ExpireCache` and its :py:obj:`searx.cache.ExpireCacheCfg`

----
"""

__all__ = ["ExpireCacheCfg", "ExpireCacheStats", "ExpireCache", "ExpireCacheSQLite"]

import abc
from collections.abc import Iterator
import dataclasses
import datetime
import hashlib
import hmac
import os
import pickle
import sqlite3
import string
import tempfile
import time
import typing

import msgspec

from searx import sqlitedb
from searx import logger
from searx import get_setting

log = logger.getChild("cache")

CacheRowType: typing.TypeAlias = tuple[str, typing.Any, int | None]


class ExpireCacheCfg(msgspec.Struct):  # pylint: disable=too-few-public-methods
    """Configuration of a :py:obj:`ExpireCache` cache."""

    name: str
    """Name of the cache."""

    db_url: str = ""
    """URL of the SQLite DB, the path to the database file.  If unset a default
    DB will be created in `/tmp/sxng_cache_{self.name}.db`"""

    MAX_VALUE_LEN: int = 1024 * 10
    """Max length of a *serialized* value."""

    MAXHOLD_TIME: int = 60 * 60 * 24 * 7  # 7 days
    """Hold time (default in sec.), after which a value is removed from the cache."""

    MAINTENANCE_PERIOD: int = 60 * 60  # 2h
    """Maintenance period in seconds / when :py:obj:`MAINTENANCE_MODE` is set to
    ``auto``."""

    MAINTENANCE_MODE: typing.Literal["auto", "off"] = "auto"
    """Type of maintenance mode

    ``auto``:
      Maintenance is carried out automatically as part of the maintenance
      intervals (:py:obj:`MAINTENANCE_PERIOD`); no external process is required.

    ``off``:
      Maintenance is switched off and must be carried out by an external process
      if required.
    """

    password: bytes = get_setting("server.secret_key").encode()
    """Password used by :py:obj:`ExpireCache.secret_hash`.

    The default password is taken from :ref:`secret_key <server.secret_key>`.
    When the password is changed, the hashed keys in the cache can no longer be
    used, which is why all values in the cache are deleted when the password is
    changed.
    """

    def __post_init__(self):
        # if db_url is unset, use a default DB in /tmp/sxng_cache_{name}.db
        if not self.db_url:
            self.db_url = tempfile.gettempdir() + os.sep + f"sxng_cache_{ExpireCache.normalize_name(self.name)}.db"


@dataclasses.dataclass
class ExpireCacheStats:
    """Dataclass which provides information on the status of the cache."""

    cached_items: dict[str, list[CacheRowType]]
    """Values in the cache mapped by context name.

    .. code: python

       {
           "context name": [
               ("foo key": "foo value", <expire>),
               ("bar key": "bar value", <expire>),
               # ...
           ],
           # ...
       }
    """

    def report(self):
        c_ctx = 0
        c_kv = 0
        lines: list[str] = []

        for ctx_name, kv_list in self.cached_items.items():
            c_ctx += 1
            if not kv_list:
                lines.append(f"[{ctx_name:20s}] empty")
                continue

            for key, value, expire in kv_list:
                valid_until = ""
                if expire:
                    valid_until = datetime.datetime.fromtimestamp(expire).strftime("%Y-%m-%d %H:%M:%S")
                c_kv += 1
                lines.append(f"[{ctx_name:20s}] {valid_until} {key:12}" f" --> ({type(value).__name__}) {value} ")

        lines.append(f"Number of contexts: {c_ctx}")
        lines.append(f"number of key/value pairs: {c_kv}")
        return "\n".join(lines)


class ExpireCache(abc.ABC):
    """Abstract base class for the implementation of a key/value cache
    with expire date."""

    cfg: ExpireCacheCfg

    hash_token: str = "hash_token"

    @abc.abstractmethod
    def set(self, key: str, value: typing.Any, expire: int | None, ctx: str | None = None) -> bool:
        """Set *key* to *value*.  To set a timeout on key use argument
        ``expire`` (in sec.).  If expire is unset the default is taken from
        :py:obj:`ExpireCacheCfg.MAXHOLD_TIME`.  After the timeout has expired,
        the key will automatically be deleted.

        The ``ctx`` argument specifies the context of the ``key``.  A key is
        only unique in its context.

        The concrete implementations of this abstraction determine how the
        context is mapped in the connected database.  In SQL databases, for
        example, the context is a DB table or in a Key/Value DB it could be
        a prefix for the key.

        If the context is not specified (the default is ``None``) then a
        default context should be used, e.g. a default table for SQL databases
        or a default prefix in a Key/Value DB.
        """

    @abc.abstractmethod
    def get(self, key: str, default: typing.Any = None, ctx: str | None = None) -> typing.Any:
        """Return *value* of *key*.  If key is unset, ``None`` is returned."""

    @abc.abstractmethod
    def maintenance(self, force: bool = False, truncate: bool = False) -> bool:
        """Performs maintenance on the cache.

        ``force``:
          Maintenance should be carried out even if the maintenance interval has
          not yet been reached.

        ``truncate``:
          Truncate the entire cache, which is necessary, for example, if the
          password has changed.
        """

    @abc.abstractmethod
    def state(self) -> ExpireCacheStats:
        """Returns a :py:obj:`ExpireCacheStats`, which provides information
        about the status of the cache."""

    @staticmethod
    def build_cache(cfg: ExpireCacheCfg) -> "ExpireCacheSQLite":
        """Factory to build a caching instance.

        .. note::

           Currently, only the SQLite adapter is available, but other database
           types could be implemented in the future, e.g. a Valkey (Redis)
           adapter.
        """
        return ExpireCacheSQLite(cfg)

    @staticmethod
    def normalize_name(name: str) -> str:
        """Returns a normalized name that can be used as a file name or as a SQL
        table name (is used, for example, to normalize the context name)."""

        _valid = "-_." + string.ascii_letters + string.digits
        return "".join([c for c in name if c in _valid])

    def serialize(self, value: typing.Any) -> bytes:
        dump: bytes = pickle.dumps(value)
        return dump

    def deserialize(self, value: bytes) -> typing.Any:
        obj = pickle.loads(value)
        return obj

    def secret_hash(self, name: str | bytes) -> str:
        """Creates a hash of the argument ``name``.  The hash value is formed
        from the ``name`` combined with the :py:obj:`password
        <ExpireCacheCfg.password>`.  Can be used, for example, to make the
        ``key`` stored in the DB unreadable for third parties."""

        if isinstance(name, str):
            name = bytes(name, encoding='utf-8')
        m = hmac.new(name + self.cfg.password, digestmod='sha256')
        return m.hexdigest()


class ExpireCacheSQLite(sqlitedb.SQLiteAppl, ExpireCache):
    """Cache that manages key/value pairs in a SQLite DB.  The DB model in the
    SQLite DB is implemented in abstract class :py:obj:`SQLiteAppl
    <searx.sqlitedb.SQLiteAppl>`.

    The following configurations are required / supported:

    - :py:obj:`ExpireCacheCfg.db_url`
    - :py:obj:`ExpireCacheCfg.MAXHOLD_TIME`
    - :py:obj:`ExpireCacheCfg.MAINTENANCE_PERIOD`
    - :py:obj:`ExpireCacheCfg.MAINTENANCE_MODE`
    """

    DB_SCHEMA: int = 1

    # The key/value tables will be created on demand by self.create_table
    DDL_CREATE_TABLES: dict[str, str] = {}

    CACHE_TABLE_PREFIX: str = "CACHE-TABLE"

    def __init__(self, cfg: ExpireCacheCfg):
        """An instance of the SQLite expire cache is build up from a
        :py:obj:`config <ExpireCacheCfg>`."""

        self.cfg: ExpireCacheCfg = cfg
        if cfg.db_url == ":memory:":
            log.critical("don't use SQLite DB in :memory: in production!!")
        super().__init__(cfg.db_url)

    def init(self, conn: sqlite3.Connection) -> bool:
        ret_val = super().init(conn)
        if not ret_val:
            return False

        new = hashlib.sha256(self.cfg.password).hexdigest()
        old = self.properties(self.hash_token)
        if old != new:
            if old is not None:
                log.warning("[%s] hash token changed: truncate all cache tables", self.cfg.name)
            self.maintenance(force=True, truncate=True)
            self.properties.set(self.hash_token, new)

        return True

    def maintenance(self, force: bool = False, truncate: bool = False) -> bool:

        if not force and int(time.time()) < self.next_maintenance_time:
            # log.debug("no maintenance required yet, next maintenance interval is in the future")
            return False

        # Prevent parallel DB maintenance cycles from other DB connections
        # (e.g. in multi thread or process environments).
        self.properties.set("LAST_MAINTENANCE", "")  # hint: this (also) sets the m_time of the property!

        if truncate:
            self.truncate_tables(self.table_names)
            return True

        # drop items by expire time stamp ..
        expire = int(time.time())

        with self.connect() as conn:
            for table in self.table_names:
                res = conn.execute(f"DELETE FROM {table} WHERE expire < ?", (expire,))
                log.debug("deleted %s keys from table %s (expire date reached)", res.rowcount, table)

        # Vacuuming the WALs
        # https://www.theunterminatedstring.com/sqlite-vacuuming/

        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()

        return True

    def create_table(self, table: str) -> bool:
        """Create DB ``table`` if it has not yet been created, no recreates are
        initiated if the table already exists.
        """
        if table in self.table_names:
            # log.debug("key/value table %s exists in DB (no need to recreate)", table)
            return False

        log.info("key/value table '%s' NOT exists in DB -> create DB table ..", table)
        sql_table = "\n".join(
            [
                f"CREATE TABLE IF NOT EXISTS {table} (",
                "  key        TEXT,",
                "  value      BLOB,",
                f"  expire     INTEGER DEFAULT (strftime('%s', 'now') + {self.cfg.MAXHOLD_TIME}),",
                "PRIMARY KEY (key))",
            ]
        )
        sql_index = f"CREATE INDEX IF NOT EXISTS index_expire_{table} ON {table}(expire);"
        with self.connect() as conn:
            conn.execute(sql_table)
            conn.execute(sql_index)
        conn.close()

        self.properties.set(f"{self.CACHE_TABLE_PREFIX}-{table}", table)
        return True

    @property
    def table_names(self) -> list[str]:
        """List of key/value tables already created in the DB."""
        sql = f"SELECT value FROM properties WHERE name LIKE '{self.CACHE_TABLE_PREFIX}%%'"
        rows = self.DB.execute(sql).fetchall() or []
        return [r[0] for r in rows]

    def truncate_tables(self, table_names: list[str]):
        log.debug("truncate table: %s", ",".join(table_names))
        with self.connect() as conn:
            for table in table_names:
                conn.execute(f"DELETE FROM {table}")
        conn.close()
        return True

    @property
    def next_maintenance_time(self) -> int:
        """Returns (unix epoch) time of the next maintenance."""

        return self.cfg.MAINTENANCE_PERIOD + self.properties.m_time("LAST_MAINTENANCE", int(time.time()))

    # implement ABC methods of ExpireCache

    def set(self, key: str, value: typing.Any, expire: int | None, ctx: str | None = None) -> bool:
        """Set key/value in DB table given by argument ``ctx``.  If expire is
        unset the default is taken from :py:obj:`ExpireCacheCfg.MAXHOLD_TIME`.
        If ``ctx`` argument is ``None`` (the default), a table name is
        generated from the :py:obj:`ExpireCacheCfg.name`.  If DB table does not
        exists, it will be created (on demand) by :py:obj:`self.create_table
        <ExpireCacheSQLite.create_table>`.
        """
        c, err_msg_list = self._setmany([(key, value, expire)], ctx=ctx)
        if c:
            log.debug("%s -- %s: key '%s' updated or inserted (%s errors)", self.cfg.name, ctx, key, len(err_msg_list))
        else:
            for msg in err_msg_list:
                log.error("%s -- %s: %s", self.cfg.name, ctx, msg)
        return bool(c)

    def setmany(
        self,
        opt_list: list[CacheRowType],
        ctx: str | None = None,
    ) -> int:
        """Efficient bootload of the cache from a list of options.  The list
        contains tuples with the arguments described in
        :py:obj:`ExpireCacheSQLite.set`."""
        _start = time.time()
        c, err_msg_list = self._setmany(opt_list=opt_list, ctx=ctx)
        _end = time.time()
        for msg in err_msg_list:
            log.error("%s -- %s: %s", self.cfg.name, ctx, msg)

        log.debug(
            "%s -- %s: %s/%s key/value pairs updated or inserted in %s sec (%s errors)",
            self.cfg.name,
            ctx,
            c,
            len(opt_list),
            _end - _start,
            len(err_msg_list),
        )
        return c

    def _setmany(
        self,
        opt_list: list[CacheRowType],
        ctx: str | None = None,
    ) -> tuple[int, list[str]]:

        table = ctx
        self.maintenance()

        table_name = table
        if not table_name:
            table_name = self.normalize_name(self.cfg.name)
        self.create_table(table_name)

        sql_str = (
            f"INSERT INTO {table_name} (key, value, expire) VALUES (?, ?, ?)"
            f"    ON CONFLICT DO "
            f"UPDATE SET value=?, expire=?"
        )

        sql_rows: list[
            tuple[
                str,  # key
                typing.Any,  # value
                int | None,  # expire
                typing.Any,  # value
                int | None,  # expire
            ]
        ] = []

        err_msg_list: list[str] = []
        for key, _val, expire in opt_list:

            value: bytes = self.serialize(value=_val)
            if len(value) > self.cfg.MAX_VALUE_LEN:
                err_msg_list.append(f"{table}.key='{key}' - serialized value too big to cache (len: {len(value)}) ")
                continue

            if not expire:
                expire = self.cfg.MAXHOLD_TIME
            expire = int(time.time()) + expire

            # positional arguments of the INSERT INTO statement
            sql_args = (key, value, expire, value, expire)
            sql_rows.append(sql_args)

        if not sql_rows:
            return 0, err_msg_list

        if table:
            with self.DB:
                self.DB.executemany(sql_str, sql_rows)
        else:
            with self.connect() as conn:
                conn.executemany(sql_str, sql_rows)
            conn.close()

        return len(sql_rows), err_msg_list

    def get(self, key: str, default: typing.Any = None, ctx: str | None = None) -> typing.Any:
        """Get value of ``key`` from table given by argument ``ctx``.  If
        ``ctx`` argument is ``None`` (the default), a table name is generated
        from the :py:obj:`ExpireCacheCfg.name`.  If ``key`` not exists (in
        table), the ``default`` value is returned.

        """
        table = ctx
        self.maintenance()

        if not table:
            table = self.normalize_name(self.cfg.name)

        if table not in self.table_names:
            return default

        sql = f"SELECT value FROM {table} WHERE key = ?"
        row = self.DB.execute(sql, (key,)).fetchone()
        if row is None:
            return default

        return self.deserialize(row[0])

    def pairs(self, ctx: str) -> Iterator[tuple[str, typing.Any]]:
        """Iterate over key/value pairs from table given by argument ``ctx``.
        If ``ctx`` argument is ``None`` (the default), a table name is
        generated from the :py:obj:`ExpireCacheCfg.name`."""
        table = ctx
        self.maintenance()

        if not table:
            table = self.normalize_name(self.cfg.name)

        if table in self.table_names:
            for row in self.DB.execute(f"SELECT key, value FROM {table}"):
                yield row[0], self.deserialize(row[1])

    def state(self) -> ExpireCacheStats:
        cached_items: dict[str, list[CacheRowType]] = {}
        for table in self.table_names:
            cached_items[table] = []
            for row in self.DB.execute(f"SELECT key, value, expire FROM {table}"):
                cached_items[table].append((row[0], self.deserialize(row[1]), row[2]))
        return ExpireCacheStats(cached_items=cached_items)
