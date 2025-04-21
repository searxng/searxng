"""Implementation of caching solutions.

- :py:obj:`searx.cache.ExpireCache` and its :py:obj:`searx.cache.ExpireCacheCfg`

----
"""

from __future__ import annotations

__all__ = ["ExpireCacheCfg", "ExpireCacheStats", "ExpireCache", "ExpireCacheSQLite"]

import abc
import dataclasses
import datetime
import hashlib
import hmac
import os
import pickle
import secrets
import sqlite3
import string
import tempfile
import time
import typing

from base64 import urlsafe_b64encode, urlsafe_b64decode

import msgspec

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from searx import sqlitedb
from searx import logger
from searx import get_setting

log = logger.getChild("cache")


class ExpireCacheCfg(msgspec.Struct):  # pylint: disable=too-few-public-methods
    """Configuration of a :py:obj:`ExpireCache` cache."""

    name: str
    """Name of the cache."""

    db_url: str = ""
    """URL of the SQLite DB, the path to the database file.  If unset a default
    DB will be created in `/tmp/sxng_cache_{self.name}.db`"""

    MAX_VALUE_LEN: int = 1024 * 10
    """Max lenght of a *serialized* value."""

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

    # encryption of the values stored in the DB

    password: bytes = get_setting("server.secret_key").encode()  # type: ignore
    """Password used in case of :py:obj:`ExpireCacheCfg.ENCRYPT_VALUE` is
    ``True``.

    The default password is taken from :ref:`secret_key <server.secret_key>`.
    When the password is changed, the values in the cache can no longer be
    decrypted, which is why all values in the cache are deleted when the
    password is changed.
    """

    ENCRYPT_VALUE: bool = True
    """Encrypting the values before they are written to the DB (see:
    :py:obj:`ExpireCacheCfg.password`)."""

    def __post_init__(self):
        # if db_url is unset, use a default DB in /tmp/sxng_cache_{name}.db
        if not self.db_url:
            self.db_url = tempfile.gettempdir() + os.sep + f"sxng_cache_{ExpireCache.normalize_name(self.name)}.db"


@dataclasses.dataclass
class ExpireCacheStats:
    """Dataclass wich provides information on the status of the cache."""

    cached_items: dict[str, list[tuple[str, typing.Any, int]]]
    """Values in the cache mapped by table name.

    .. code: python

       {
           "table name": [
               ("foo key": "foo value", <expire>),
               ("bar key": "bar value", <expire>),
               # ...
           ],
           # ...
       }
    """

    def report(self):
        c_tables = 0
        c_kv = 0
        lines = []

        for table_name, kv_list in self.cached_items.items():
            c_tables += 1
            if not kv_list:
                lines.append(f"[{table_name:20s}] empty")
                continue

            for key, value, expire in kv_list:
                valid_until = datetime.datetime.fromtimestamp(expire).strftime("%Y-%m-%d %H:%M:%S")
                c_kv += 1
                lines.append(f"[{table_name:20s}] {valid_until} {key:12}" f" --> ({type(value).__name__}) {value} ")

        lines.append(f"number of tables: {c_tables}")
        lines.append(f"number of key/value pairs: {c_kv}")
        return "\n".join(lines)


class ExpireCache(abc.ABC):
    """Abstract base class for the implementation of a key/value cache
    with expire date."""

    cfg: ExpireCacheCfg

    hmac_iterations: int = 10_000
    crypt_hash_property = "crypt_hash"

    @abc.abstractmethod
    def set(self, key: str, value: typing.Any, expire: int | None) -> bool:
        """Set *key* to *value*.  To set a timeout on key use argument
        ``expire`` (in sec.).  If expire is unset the default is taken from
        :py:obj:`ExpireCacheCfg.MAXHOLD_TIME`.  After the timeout has expired,
        the key will automatically be deleted.
        """

    @abc.abstractmethod
    def get(self, key: str, default=None) -> typing.Any:
        """Return *value* of *key*.  If key is unset, ``None`` is returned."""

    @abc.abstractmethod
    def maintenance(self, force: bool = False, drop_crypted: bool = False) -> bool:
        """Performs maintenance on the cache.

        ``force``:
          Maintenance should be carried out even if the maintenance interval has
          not yet been reached.

        ``drop_crypted``:
           The encrypted values can no longer be decrypted (if the password is
           changed), they must be removed from the cache.
        """

    @abc.abstractmethod
    def state(self) -> ExpireCacheStats:
        """Returns a :py:obj:`ExpireCacheStats`, which provides information
        about the status of the cache."""

    @staticmethod
    def build_cache(cfg: ExpireCacheCfg) -> ExpireCache:
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
        table name."""

        _valid = "-_." + string.ascii_letters + string.digits
        return "".join([c for c in name if c in _valid])

    def derive_key(self, password: bytes, salt: bytes, iterations: int) -> bytes:
        """Derive a secret-key from a given password and salt."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
        )
        return urlsafe_b64encode(kdf.derive(password))

    def serialize(self, value: typing.Any) -> bytes:
        dump: bytes = pickle.dumps(value)
        if self.cfg.ENCRYPT_VALUE:
            dump = self.encrypt(dump)
        return dump

    def deserialize(self, value: bytes) -> typing.Any:
        if self.cfg.ENCRYPT_VALUE:
            value = self.decrypt(value)
        obj = pickle.loads(value)
        return obj

    def encrypt(self, message: bytes) -> bytes:
        """Encode and decode values by a method using `Fernet with password`_ where
        the key is derived from the password (PBKDF2HMAC_).  The *password* for
        encryption is taken from the :ref:`server.secret_key`

        .. _Fernet with password:  https://stackoverflow.com/a/55147077
        .. _PBKDF2HMAC: https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/#pbkdf2
        """

        # Including the salt in the output makes it possible to use a random
        # salt value, which in turn ensures the encrypted output is guaranteed
        # to be fully random regardless of password reuse or message
        # repetition.
        salt = secrets.token_bytes(16)  # randomly generated salt

        # Including the iteration count ensures that you can adjust
        # for CPU performance increases over time without losing the ability to
        # decrypt older messages.
        iterations = int(self.hmac_iterations)

        key = self.derive_key(self.cfg.password, salt, iterations)
        crypted_msg = Fernet(key).encrypt(message)

        # Put salt and iteration count on the beginning of the binary
        token = b"%b%b%b" % (salt, iterations.to_bytes(4, "big"), urlsafe_b64encode(crypted_msg))
        return urlsafe_b64encode(token)

    def decrypt(self, token: bytes) -> bytes:
        token = urlsafe_b64decode(token)

        # Strip salt and iteration count from the beginning of the binary
        salt = token[:16]
        iterations = int.from_bytes(token[16:20], "big")

        key = self.derive_key(self.cfg.password, salt, iterations)
        crypted_msg = urlsafe_b64decode(token[20:])

        message = Fernet(key).decrypt(crypted_msg)
        return message

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
    - :py:obj:`ExpireCacheCfg.ENCRYPT_VALUE`
    """

    DB_SCHEMA = 1

    # The key/value tables will be created on demand by self.create_table
    DDL_CREATE_TABLES = {}

    CACHE_TABLE_PREFIX = "CACHE-TABLE-"

    def __init__(self, cfg: ExpireCacheCfg):
        """An instance of the SQLite expire cache is build up from a
        :py:obj:`config <ExpireCacheCfg>`."""

        self.cfg = cfg
        if cfg.db_url == ":memory:":
            log.critical("don't use SQLite DB in :memory: in production!!")
        super().__init__(cfg.db_url)

    def init(self, conn: sqlite3.Connection) -> bool:
        ret_val = super().init(conn)
        if not ret_val:
            return False

        if self.cfg.ENCRYPT_VALUE:
            new = hashlib.sha256(self.cfg.password).hexdigest()
            old = self.properties(self.crypt_hash_property)
            if old != new:
                if old is not None:
                    log.warning("[%s] crypt token changed: drop all cache tables", self.cfg.name)
                self.maintenance(force=True, drop_crypted=True)
                self.properties.set(self.crypt_hash_property, new)

        return True

    def maintenance(self, force: bool = False, drop_crypted: bool = False) -> bool:

        if not force and int(time.time()) < self.next_maintenance_time:
            # log.debug("no maintenance required yet, next maintenance interval is in the future")
            return False

        # Prevent parallel DB maintenance cycles from other DB connections
        # (e.g. in multi thread or process environments).
        self.properties.set("LAST_MAINTENANCE", "")  # hint: this (also) sets the m_time of the property!

        if drop_crypted:
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

    def set(self, key: str, value: typing.Any, expire: int | None, table: str | None = None) -> bool:
        """Set key/value in ``table``.  If expire is unset the default is taken
        from :py:obj:`ExpireCacheCfg.MAXHOLD_TIME`.  If ``table`` argument is
        ``None`` (the default), a table name is generated from the
        :py:obj:`ExpireCacheCfg.name`.  If DB ``table`` does not exists, it will be
        created (on demand) by :py:obj:`self.create_table
        <ExpireCacheSQLite.create_table>`.
        """
        self.maintenance()

        value = self.serialize(value=value)
        if len(value) > self.cfg.MAX_VALUE_LEN:
            log.warning("ExpireCache.set(): %s.key='%s' - value too big to cache (len: %s)  ", table, value, len(value))
            return False

        if not expire:
            expire = self.cfg.MAXHOLD_TIME
        expire = int(time.time()) + expire

        table_name = table
        if not table_name:
            table_name = self.normalize_name(self.cfg.name)
        self.create_table(table_name)

        sql = (
            f"INSERT INTO {table_name} (key, value, expire) VALUES (?, ?, ?)"
            f"    ON CONFLICT DO "
            f"UPDATE SET value=?, expire=?"
        )

        if table:
            with self.DB:
                self.DB.execute(sql, (key, value, expire, value, expire))
        else:
            with self.connect() as conn:
                conn.execute(sql, (key, value, expire, value, expire))
            conn.close()

        return True

    def get(self, key: str, default=None, table: str | None = None) -> typing.Any:
        """Get value of ``key`` from ``table``.  If ``table`` argument is
        ``None`` (the default), a table name is generated from the
        :py:obj:`ExpireCacheCfg.name`.  If ``key`` not exists (in table), the
        ``default`` value is returned.
        """
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

    def state(self) -> ExpireCacheStats:
        cached_items = {}
        for table in self.table_names:
            cached_items[table] = []
            for row in self.DB.execute(f"SELECT key, value, expire FROM {table}"):
                cached_items[table].append((row[0], self.deserialize(row[1]), row[2]))
        return ExpireCacheStats(cached_items=cached_items)
