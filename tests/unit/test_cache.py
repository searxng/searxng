# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

import os
import pickle
import sqlite3
import tempfile
import unittest

from searx.cache import ExpireCacheCfg, ExpireCacheSQLite

# Records that a pickle payload has been executed.  A tampered cache value must
# never reach pickle.loads(), so this list has to stay empty.
_EXECUTED: list[str] = []


def _record_execution(payload_id: str) -> None:  # pragma: no cover
    _EXECUTED.append(payload_id)


class _EvilValue:  # pylint: disable=too-few-public-methods
    """Stand-in for an attacker supplied pickle payload."""

    def __init__(self, payload_id: str):
        self.payload_id = payload_id

    def __reduce__(self):
        return (_record_execution, (self.payload_id,))


class TestExpireCacheValueIntegrity(unittest.TestCase):
    """The cache DB is a plain file in a world writable directory and its name
    is predictable, so it must not deserialize a value that it did not write
    itself."""

    def setUp(self):
        _EXECUTED.clear()
        fd, self.db_url = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.unlink(self.db_url)

        self.cache = ExpireCacheSQLite.build_cache(
            ExpireCacheCfg(
                name="TEST_INTEGRITY",
                db_url=self.db_url,
                password=b"test-password",
            )
        )
        # create the table and one entry
        self.cache.set(key="key", value=("legit", ["a"]), expire=None, ctx="t")

    def tearDown(self):
        try:
            os.unlink(self.db_url)
        except OSError:
            pass

    def _tamper(self, payload: bytes):
        with sqlite3.connect(self.db_url) as conn:
            conn.execute("UPDATE t SET value = ? WHERE key = 'key'", (payload,))

    def test_roundtrip_preserves_value_and_type(self):
        # legitimate control: values are returned unchanged, incl. tuple types
        value = self.cache.get(key="key", ctx="t")
        self.assertEqual(value, ("legit", ["a"]))
        self.assertIsInstance(value, tuple)

    def test_tampered_value_is_not_deserialized(self):
        self._tamper(pickle.dumps(_EvilValue("tampered")))

        value = self.cache.get(key="key", default="DEFAULT", ctx="t")

        self.assertEqual(_EXECUTED, [], "tampered cache value was deserialized")
        self.assertEqual(value, "DEFAULT", "a value without a valid integrity check must be a cache miss")

    def test_expired_value_is_not_deserialized(self):
        self._tamper(pickle.dumps(_EvilValue("expired")))

        with sqlite3.connect(self.db_url) as conn:
            conn.execute("UPDATE t SET expire = 0 WHERE key = 'key'")

        value = self.cache.get(key="key", default="DEFAULT", ctx="t")

        self.assertEqual(_EXECUTED, [], "expired cache value was deserialized")
        self.assertEqual(value, "DEFAULT")
