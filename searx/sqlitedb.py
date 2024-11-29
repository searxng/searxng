# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implementations to make access to SQLite databases a little more convenient.

:py:obj:`SQLiteAppl`
  Abstract class with which DB applications can be implemented.

:py:obj:`SQLiteProperties`:
  Class to manage properties stored in a database.

----

"""
from __future__ import annotations

import sys
import re
import sqlite3
import threading
import abc

from searx import logger

logger = logger.getChild('sqlitedb')


class SQLiteAppl(abc.ABC):
    """Abstract base class for implementing convenient DB access in SQLite
    applications.  In the constructor, a :py:obj:`SQLiteProperties` instance is
    already aggregated under ``self.properties``."""

    DDL_CREATE_TABLES: dict[str, str] = {}

    DB_SCHEMA: int = 1
    """As soon as changes are made to the DB schema, the version number must be
    increased.  Changes to the version number require the DB to be recreated (or
    migrated / if an migration path exists and is implemented)."""

    SQLITE_THREADING_MODE = {
        0: "single-thread",
        1: "multi-thread",
        3: "serialized"}[sqlite3.threadsafety]  # fmt:skip
    """Threading mode of the SQLite library.  Depends on the options used at
    compile time and is different for different distributions and architectures.

    Possible values are 0:``single-thread``, 1:``multi-thread``,
    3:``serialized`` (see :py:obj:`sqlite3.threadsafety`).  Pre- Python 3.11
    this value was hard coded to 1.

    Depending on this value, optimizations are made, e.g. in “serialized” mode
    it is not necessary to create a separate DB connector for each thread.
    """

    SQLITE_JOURNAL_MODE = "WAL"
    SQLITE_CONNECT_ARGS = {
        # "timeout": 5.0,
        # "detect_types": 0,
        "check_same_thread": bool(SQLITE_THREADING_MODE != "serialized"),
        "cached_statements": 0,  # https://github.com/python/cpython/issues/118172
        # "uri": False,
        "autocommit": False,
    }  # fmt:skip
    """Connection arguments (:py:obj:`sqlite3.connect`)

    ``check_same_thread``:
      Is disabled by default when :py:obj:`SQLITE_THREADING_MODE` is
      ``serialized``.  The check is more of a hindrance in this case because it
      would prevent a DB connector from being used in multiple threads.

    ``autocommit``:
      Is disabled by default.  Note: autocommit option has been added in Python
      3.12.

    ``cached_statements``:
      Is set to ``0`` by default.  Note: Python 3.12+ fetch result are not
      consistent in multi-threading application and causing an API misuse error.

      The multithreading use in SQLiteAppl is intended and supported if
      threadsafety is set to 3 (aka "serialized"). CPython supports “serialized”
      from version 3.12 on, but unfortunately only with errors:

      - https://github.com/python/cpython/issues/118172
      - https://github.com/python/cpython/issues/123873

      The workaround for SQLite3 multithreading cache inconsistency ist to set
      option ``cached_statements`` to ``0`` by default.
    """

    def __init__(self, db_url):

        self.db_url = db_url
        self.properties = SQLiteProperties(db_url)
        self.thread_local = threading.local()
        self._init_done = False
        self._compatibility()

    def _compatibility(self):

        if self.SQLITE_THREADING_MODE == "serialized":
            self._DB = None
        else:
            msg = (
                f"SQLite library is compiled with {self.SQLITE_THREADING_MODE} mode,"
                " read https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety"
            )
            if threading.active_count() > 1:
                logger.error(msg)
            else:
                logger.warning(msg)

        if sqlite3.sqlite_version_info <= (3, 35):
            # See "Generalize UPSERT:" in https://sqlite.org/releaselog/3_35_0.html
            logger.critical(
                "SQLite runtime library version %s is not supported (require >= 3.35)", sqlite3.sqlite_version
            )

    def connect(self) -> sqlite3.Connection:
        """Creates a new DB connection (:py:obj:`SQLITE_CONNECT_ARGS`).  If not
        already done, the DB schema is set up
        """
        if sys.version_info < (3, 12):
            # Prior Python 3.12 there is no "autocommit" option
            self.SQLITE_CONNECT_ARGS.pop("autocommit", None)

        self.init()
        logger.debug("%s: connect to DB: %s // %s", self.__class__.__name__, self.db_url, self.SQLITE_CONNECT_ARGS)
        conn = sqlite3.Connection(self.db_url, **self.SQLITE_CONNECT_ARGS)  # type: ignore
        conn.execute(f"PRAGMA journal_mode={self.SQLITE_JOURNAL_MODE}")
        self.register_functions(conn)
        return conn

    def register_functions(self, conn):
        """Create user-defined_ SQL functions.

        ``REGEXP(<pattern>, <field>)`` : 0 | 1
           `re.search`_ returns (int) 1 for a match and 0 for none match of
           ``<pattern>`` in ``<field>``.

           .. code:: sql

              SELECT '12' AS field WHERE REGEXP('^[0-9][0-9]$', field)
              -- 12

              SELECT REGEXP('[0-9][0-9]', 'X12Y')
              -- 1
              SELECT REGEXP('[0-9][0-9]', 'X1Y')
              -- 0

        .. _user-defined: https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.create_function
        .. _deterministic: https://sqlite.org/deterministic.html
        .. _re.search: https://docs.python.org/3/library/re.html#re.search
        """

        conn.create_function('regexp', 2, lambda x, y: 1 if re.search(x, y) else 0, deterministic=True)

    @property
    def DB(self) -> sqlite3.Connection:
        """Provides a DB connection.  The connection is a *singleton* and
        therefore well suited for read access.  If
        :py:obj:`SQLITE_THREADING_MODE` is ``serialized`` only one DB connection
        is created for all threads.

        .. note::

           For dedicated `transaction control`_, it is recommended to create a
           new connection (:py:obj:`SQLiteAppl.connect`).

        .. _transaction control:
            https://docs.python.org/3/library/sqlite3.html#sqlite3-controlling-transactions
        """

        if getattr(self.thread_local, 'DB', None) is None:
            self.thread_local.DB = self.connect()

        # Theoretically it is possible to reuse the DB cursor across threads as
        # of Python 3.12, in practice the threading of the cursor seems to me to
        # be so faulty that I prefer to establish one connection per thread

        self.thread_local.DB.commit()
        return self.thread_local.DB

        # In "serialized" mode, SQLite can be safely used by multiple threads
        # with no restriction.
        #
        # if self.SQLITE_THREADING_MODE != "serialized":
        #     if getattr(self.thread_local, 'DB', None) is None:
        #         self.thread_local.DB = self.connect()
        #     return self.thread_local.DB
        #
        # if self._DB is None:
        #     self._DB = self.connect()  # pylint: disable=attribute-defined-outside-init
        # return self._DB

    def init(self):
        """Initializes the DB schema and properties, is only executed once even
        if called several times."""

        if self._init_done:
            return
        self._init_done = True

        logger.debug("init DB: %s", self.db_url)
        self.properties.init()
        ver = self.properties("DB_SCHEMA")
        if ver is None:
            with self.properties.DB:
                self.create_schema(self.properties.DB)
        else:
            ver = int(ver)
            if ver != self.DB_SCHEMA:
                raise sqlite3.DatabaseError("Expected DB schema v%s, DB schema is v%s" % (self.DB_SCHEMA, ver))
            logger.debug("DB_SCHEMA = %s", ver)

    def create_schema(self, conn):

        logger.debug("create schema ..")
        with conn:
            for table_name, sql in self.DDL_CREATE_TABLES.items():
                conn.execute(sql)
                self.properties.set(f"Table {table_name} created", table_name)
                self.properties.set("DB_SCHEMA", self.DB_SCHEMA)
                self.properties.set("LAST_MAINTENANCE", "")


class SQLiteProperties(SQLiteAppl):
    """Simple class to manage properties of a DB application in the DB.  The
    object has its own DB connection and transaction area.

    .. code:: sql

       CREATE TABLE IF NOT EXISTS properties (
         name       TEXT,
         value      TEXT,
         m_time     INTEGER DEFAULT (strftime('%s', 'now')),
         PRIMARY KEY (name))

    """

    SQLITE_JOURNAL_MODE = "WAL"

    DDL_PROPERTIES = """\
CREATE TABLE IF NOT EXISTS properties (
  name       TEXT,
  value      TEXT,
  m_time     INTEGER DEFAULT (strftime('%s', 'now')),  -- last modified (unix epoch) time in sec.
  PRIMARY KEY (name))"""

    """Table to store properties of the DB application"""

    SQL_GET = "SELECT value FROM properties WHERE name = ?"
    SQL_M_TIME = "SELECT m_time FROM properties WHERE name = ?"
    SQL_SET = (
        "INSERT INTO properties (name, value) VALUES (?, ?)"
        "    ON CONFLICT(name) DO UPDATE"
        "   SET value=excluded.value, m_time=strftime('%s', 'now')"
    )
    SQL_TABLE_EXISTS = (
        "SELECT name FROM sqlite_master"
        " WHERE type='table' AND name='properties'"
    )  # fmt:skip
    SQLITE_CONNECT_ARGS = dict(SQLiteAppl.SQLITE_CONNECT_ARGS)
    SQLITE_CONNECT_ARGS["autocommit"] = True  # This option has no effect before Python 3.12

    def __init__(self, db_url: str):  # pylint: disable=super-init-not-called

        self.db_url = db_url
        self.thread_local = threading.local()
        self._init_done = False
        self._compatibility()

    def init(self):
        """Initializes DB schema of the properties in the DB."""

        if self._init_done:
            return
        self._init_done = True
        logger.debug("init properties of DB: %s", self.db_url)
        with self.DB as conn:
            res = conn.execute(self.SQL_TABLE_EXISTS)
            if res.fetchone() is None:  # DB schema needs to be be created
                self.create_schema(conn)

    def __call__(self, name, default=None):
        """Returns the value of the property ``name`` or ``default`` if property
        not exists in DB."""

        res = self.DB.execute(self.SQL_GET, (name,)).fetchone()
        if res is None:
            return default
        return res[0]

    def set(self, name, value):
        """Set ``value`` of property ``name`` in DB.  If property already
        exists, update the ``m_time`` (and the value)."""

        self.DB.execute(self.SQL_SET, (name, value))

        if sys.version_info <= (3, 12):
            # Prior Python 3.12 there is no "autocommit" option / lets commit
            # explicitely.
            self.DB.commit()

    def row(self, name, default=None):
        """Returns the DB row of property ``name`` or ``default`` if property
        not exists in DB."""

        cur = self.DB.cursor()
        cur.execute("SELECT * FROM properties WHERE name = ?", (name,))
        res = cur.fetchone()
        if res is None:
            return default
        col_names = [column[0] for column in cur.description]
        return dict(zip(col_names, res))

    def m_time(self, name, default: int = 0) -> int:
        """Last modification time of this property."""
        res = self.DB.execute(self.SQL_M_TIME, (name,)).fetchone()
        if res is None:
            return default
        return int(res[0])

    def create_schema(self, conn):
        with conn:
            conn.execute(self.DDL_PROPERTIES)
