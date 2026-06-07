# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implementations to make access to SQLite databases a little more convenient.

:py:obj:`SQLiteAppl`
  Abstract class with which DB applications can be implemented.

:py:obj:`SQLiteProperties`:
  Class to manage properties stored in a database.

Examplarical implementations based on :py:obj:`SQLiteAppl`:

:py:obj:`searx.cache.ExpireCacheSQLite` :
  Cache that manages key/value pairs in a SQLite DB, in which the key/value
  pairs are deleted after an "expire" time.  This type of cache is used, for
  example, for the engines, see :py:obj:`searx.enginelib.EngineCache`.

:py:obj:`searx.favicons.cache.FaviconCacheSQLite` :
  Favicon cache that manages the favicon BLOBs in a SQLite DB.

----
"""

import typing as t
import abc
import datetime
import re
import sqlite3
import sys
import threading
import uuid

from searx import logger

logger = logger.getChild("sqlitedb")

THREAD_LOCAL = threading.local()


class DBSession:
    """A *thead-local* DB session"""

    @classmethod
    def get_connect(cls, app: "SQLiteAppl") -> sqlite3.Connection:
        """Returns a thread local DB connection.  The connection is only
        established once per thread.
        """
        if getattr(THREAD_LOCAL, "DBSession_map", None) is None:
            url_to_session: dict[str, DBSession] = {}
            THREAD_LOCAL.DBSession_map = url_to_session

        session: DBSession | None = THREAD_LOCAL.DBSession_map.get(app.db_url)
        if session is None:
            session = cls(app)
        return session.conn

    def __init__(self, app: "SQLiteAppl"):
        self.uuid: uuid.UUID = uuid.uuid4()
        self.app: SQLiteAppl = app
        self._conn: sqlite3.Connection | None = None
        # self.__del__ will be called, when thread ends
        if getattr(THREAD_LOCAL, "DBSession_map", None) is None:
            url_to_session: dict[str, DBSession] = {}
            THREAD_LOCAL.DBSession_map = url_to_session
        THREAD_LOCAL.DBSession_map[self.app.db_url] = self

    @property
    def conn(self) -> sqlite3.Connection:
        msg = f"[{threading.current_thread().ident}] DBSession: " f"{self.app.__class__.__name__}({self.app.db_url})"
        if self._conn is None:
            self._conn = self.app.connect()
            logger.debug("%s --> created new connection", msg)
        # else:
        #     logger.debug("%s --> already connected", msg)

        return self._conn

    def __del__(self):
        try:
            if self._conn is not None:
                # HINT: Don't use Python's logging facility in a destructor, it
                # will produce error reports when python aborts the process or
                # thread, because at this point objects that the logging module
                # needs, do not exist anymore.
                # msg = f"DBSession: close [{self.uuid}] {self.app.__class__.__name__}({self.app.db_url})"
                # logger.debug(msg)
                self._conn.close()
        except Exception:  # pylint: disable=broad-exception-caught
            pass


class SQLiteAppl(abc.ABC):
    """Abstract base class for implementing convenient DB access in SQLite
    applications.  In the constructor, a :py:obj:`SQLiteProperties` instance is
    already aggregated under ``self.properties``."""

    DDL_CREATE_TABLES: dict[str, str] = {}

    DB_SCHEMA: int = 1
    """As soon as changes are made to the DB schema, the version number must be
    increased.  Changes to the version number require the DB to be recreated (or
    migrated / if an migration path exists and is implemented)."""

    SQLITE_THREADING_MODE: str = {
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

    SQLITE_JOURNAL_MODE: str = "WAL"
    """``SQLiteAppl`` applications are optimized for WAL_ mode, its not recommend
    to change the journal mode (see :py:obj:`SQLiteAppl.tear_down`).

    .. _WAL: https://sqlite.org/wal.html
    """
    SQLITE_CONNECT_ARGS: dict[str,str|int|bool|None] = {
        # "timeout": 5.0,
        # "detect_types": 0,
        "check_same_thread": bool(SQLITE_THREADING_MODE != "serialized"),
        "cached_statements": 0,  # https://github.com/python/cpython/issues/118172
        # "uri": False,
        # "isolation_level": "",
        # "autocommit": sqlite3.LEGACY_TRANSACTION_CONTROL,
    }  # fmt:skip
    """Connection arguments (:py:obj:`sqlite3.connect`)

    ``check_same_thread``: *bool*
      Is disabled by default when :py:obj:`SQLITE_THREADING_MODE` is
      `serialized`.  The check is more of a hindrance when threadsafety_ is
      `serialized` because it would prevent a DB connector from being used in
      multiple threads.

      Is enabled when threadsafety_ is ``single-thread`` or ``multi-thread``
      (when threads cannot share a connection PEP-0249_).

    ``cached_statements``:
      Is set to ``0`` by default.  Note: Python 3.12+ fetch result are not
      consistent in multi-threading application and causing an API misuse error.

      The multithreading use in SQLiteAppl is intended and supported if
      threadsafety is set to 3 (aka "serialized"). CPython supports “serialized”
      from version 3.12 on, but unfortunately only with errors:

      - https://github.com/python/cpython/issues/118172
      - https://github.com/python/cpython/issues/123873

      The workaround for SQLite3 multithreading cache inconsistency is to set
      option ``cached_statements`` to ``0`` by default.

    ``isolation_level``: *unset*
      If the connection attribute isolation_level_ is **not** ``None``, new
      transactions are implicitly opened before ``execute()`` and
      ``executemany()`` executes SQL- INSERT, UPDATE, DELETE, or REPLACE
      statements `[1]`_.

      By default, the value is not set, which means the default from Python is
      used: Python's default is ``""``, which is an alias for ``"DEFERRED"``.

    ``autocommit``: *unset*
      Starting with Python 3.12 the DB connection has a ``autocommit`` attribute
      and the recommended way of controlling transaction behaviour is through
      this attribute `[2]`_.

      By default, the value is not set, which means the default from Python is
      used: Python's default is the constant LEGACY_TRANSACTION_CONTROL_:
      Pre-Python 3.12 (non-PEP 249-compliant) transaction control, see
      ``isolation_level`` above for more details.

    .. _PEP-0249:
        https://peps.python.org/pep-0249/#threadsafety
    .. _threadsafety:
        https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety
    .. _isolation_level:
        https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.isolation_level
    .. _[1]:
        https://docs.python.org/3/library/sqlite3.html#sqlite3-transaction-control-isolation-level
    .. _autocommit:
        https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.autocommit
    .. _[2]:
        https://docs.python.org/3/library/sqlite3.html#transaction-control-via-the-autocommit-attribute
    .. _LEGACY_TRANSACTION_CONTROL:
        https://docs.python.org/3/library/sqlite3.html#sqlite3.LEGACY_TRANSACTION_CONTROL
    """

    def __init__(self, db_url: str):

        self.db_url: str = db_url
        self.properties: SQLiteProperties = SQLiteProperties(db_url)
        self._init_done: bool = False
        self._compatibility()
        # atexit.register(self.tear_down)

    # def tear_down(self):
    #     """:ref:`Vacuuming the WALs` upon normal interpreter termination
    #     (:py:obj:`atexit.register`).

    #     .. _SQLite: Vacuuming the WALs: https://www.theunterminatedstring.com/sqlite-vacuuming/
    #     """
    #     self.DB.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def _compatibility(self):

        if self.SQLITE_THREADING_MODE == "serialized":
            self._DB: sqlite3.Connection | None = None
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

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.Connection(self.db_url, **self.SQLITE_CONNECT_ARGS)  # type: ignore
        conn.execute(f"PRAGMA journal_mode={self.SQLITE_JOURNAL_MODE}")
        self.register_functions(conn)
        return conn

    def connect(self) -> sqlite3.Connection:
        """Creates a new DB connection (:py:obj:`SQLITE_CONNECT_ARGS`).  If not
        already done, the DB schema is set up.  The caller must take care of
        closing the resource.  Alternatively, :py:obj:`SQLiteAppl.DB` can also
        be used (the resource behind `self.DB` is automatically closed when the
        process or thread is terminated).
        """
        if sys.version_info < (3, 12):
            # Prior Python 3.12 there is no "autocommit" option
            self.SQLITE_CONNECT_ARGS.pop("autocommit", None)  # pyright: ignore[reportUnreachable]

        msg = (
            f"[{threading.current_thread().ident}] {self.__class__.__name__}({self.db_url})"
            f" {self.SQLITE_CONNECT_ARGS} // {self.SQLITE_JOURNAL_MODE}"
        )
        logger.debug(msg)

        with self._connect() as conn:
            self.init(conn)
        return conn

    def register_functions(self, conn: sqlite3.Connection):
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

        conn.create_function("regexp", 2, lambda x, y: 1 if re.search(x, y) else 0, deterministic=True)  # type: ignore

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

        conn: sqlite3.Connection

        if self.SQLITE_THREADING_MODE == "serialized":
            # Theoretically it is possible to reuse the DB cursor across threads
            # as of Python 3.12, in practice the threading of the cursor seems
            # to me a little faulty that I prefer to establish one connection
            # per thread.
            #
            # may we can activate this code one day ..
            # if self._DB is None:
            #     self._DB = self.connect()
            # conn = self._DB
            conn = DBSession.get_connect(self)
        else:
            conn = DBSession.get_connect(self)

        # Since more than one instance of SQLiteAppl share the same DB
        # connection, we need to make sure that each SQLiteAppl instance has run
        # its init method at least once.
        self.init(conn)

        return conn

    def init(self, conn: sqlite3.Connection) -> bool:
        """Initializes the DB schema and properties, is only executed once even
        if called several times.

        If the initialization has not yet taken place, it is carried out and a
        `True` is returned to the caller at the end.  If the initialization has
        already been carried out in the past, `False` is returned.
        """

        if self._init_done:
            return False
        self._init_done = True

        logger.debug("init DB: %s", self.db_url)
        self.properties.init(conn)

        ver = self.properties("DB_SCHEMA")
        if ver is None:
            with conn:
                self.create_schema(conn)
        else:
            ver = int(ver)
            if ver != self.DB_SCHEMA:
                raise sqlite3.DatabaseError("Expected DB schema v%s, DB schema is v%s" % (self.DB_SCHEMA, ver))
            logger.debug("DB_SCHEMA = %s", ver)

        return True

    def create_schema(self, conn: sqlite3.Connection):

        logger.debug("create schema ..")
        self.properties.set("DB_SCHEMA", self.DB_SCHEMA)
        self.properties.set("LAST_MAINTENANCE", "")
        with conn:
            for table_name, sql in self.DDL_CREATE_TABLES.items():
                conn.execute(sql)
                self.properties.set(f"Table {table_name} created", table_name)


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

    SQLITE_JOURNAL_MODE: str = "WAL"

    DDL_PROPERTIES: str = """\
CREATE TABLE IF NOT EXISTS properties (
  name       TEXT,
  value      TEXT,
  m_time     INTEGER DEFAULT (strftime('%s', 'now')),  -- last modified (unix epoch) time in sec.
  PRIMARY KEY (name))"""

    """Table to store properties of the DB application"""

    SQL_GET: str = "SELECT value FROM properties WHERE name = ?"
    SQL_M_TIME: str = "SELECT m_time FROM properties WHERE name = ?"
    SQL_SET: str = (
        "INSERT INTO properties (name, value) VALUES (?, ?)"
        "    ON CONFLICT(name) DO UPDATE"
        "   SET value=excluded.value, m_time=strftime('%s', 'now')"
    )
    SQL_DELETE: str = "DELETE FROM properties WHERE name = ?"
    SQL_TABLE_EXISTS: str = (
        "SELECT name FROM sqlite_master"
        " WHERE type='table' AND name='properties'"
    )  # fmt:skip
    SQLITE_CONNECT_ARGS: dict[str, str | int | bool | None] = dict(SQLiteAppl.SQLITE_CONNECT_ARGS)

    # pylint: disable=super-init-not-called
    def __init__(self, db_url: str):  # pyright: ignore[reportMissingSuperCall]

        self.db_url: str = db_url
        self._init_done: bool = False
        self._compatibility()

    def init(self, conn: sqlite3.Connection) -> bool:
        """Initializes DB schema of the properties in the DB."""

        if self._init_done:
            return False
        self._init_done = True
        logger.debug("init properties of DB: %s", self.db_url)
        res = conn.execute(self.SQL_TABLE_EXISTS)
        if res.fetchone() is None:  # DB schema needs to be be created
            self.create_schema(conn)
        return True

    def __call__(self, name: str, default: t.Any = None) -> t.Any:
        """Returns the value of the property ``name`` or ``default`` if property
        not exists in DB."""

        res = self.DB.execute(self.SQL_GET, (name,)).fetchone()
        if res is None:
            return default
        return res[0]

    def set(self, name: str, value: str | int):
        """Set ``value`` of property ``name`` in DB.  If property already
        exists, update the ``m_time`` (and the value)."""

        with self.DB:
            self.DB.execute(self.SQL_SET, (name, value))

    def delete(self, name: str) -> int:
        """Delete of property ``name`` from DB."""
        with self.DB:
            cur = self.DB.execute(self.SQL_DELETE, (name,))
        return cur.rowcount

    def row(self, name: str, default: t.Any = None):
        """Returns the DB row of property ``name`` or ``default`` if property
        not exists in DB."""

        res = self.DB.execute("SELECT * FROM properties WHERE name = ?", (name,))
        row = res.fetchone()
        if row is None:
            return default

        col_names = [column[0] for column in row.description]
        return dict(zip(col_names, row))

    def m_time(self, name: str, default: int = 0) -> int:
        """Last modification time of this property."""
        res = self.DB.execute(self.SQL_M_TIME, (name,))
        row = res.fetchone()
        if row is None:
            return default
        return int(row[0])

    def create_schema(self, conn: sqlite3.Connection):
        with conn:
            conn.execute(self.DDL_PROPERTIES)

    def __str__(self) -> str:
        lines: list[str] = []
        for row in self.DB.execute("SELECT name, value, m_time FROM properties"):
            name, value, m_time = row
            m_time = datetime.datetime.fromtimestamp(m_time).strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"[last modified: {m_time}] {name:20s}: {value}")
        return "\n".join(lines)
