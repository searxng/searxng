# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-class-docstring,invalid-name
"""Tests for :py:obj:`searx.data.currencies.CurrenciesDB`."""

import tempfile
import pathlib

from searx.cache import ExpireCacheCfg, ExpireCacheSQLite
from searx.data.currencies import CurrenciesDB

from tests import SearxTestCase


class TestCurrenciesDB(SearxTestCase):

    def setUp(self):
        super().setUp()
        self.tmp_dir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp_dir.cleanup)
        db_url = str(pathlib.Path(self.tmp_dir.name) / "test_currencies.db")
        self.cache = ExpireCacheSQLite.build_cache(ExpireCacheCfg(name="TEST_CURRENCIES", db_url=db_url))

        self.db = CurrenciesDB.__new__(CurrenciesDB)
        self.db.cache = self.cache

    def test_init_loads_currencies(self):
        self.db.init()
        self.assertEqual(self.cache.properties("currencies loaded"), "OK")
        self.assertTrue(self.db.is_iso4217("USD"))

    def test_failed_load_does_not_mark_cache_as_loaded(self):
        """A load() that raises must not leave the "loaded" flag set: the flag is
        set before the rows are written, so keeping it would make every later
        init() a no-op against an empty cache (issue #6500)."""

        def failing_load():
            raise OSError("cannot read currencies.json")

        self.db.load = failing_load  # pyright: ignore[reportAttributeAccessIssue]

        with self.assertRaises(OSError):
            self.db.init()

        self.assertNotEqual(self.cache.properties("currencies loaded"), "OK")
        self.assertFalse(self.db.is_iso4217("USD"))

        # a later init() must still be able to populate the cache
        del self.db.load
        self.db.init()
        self.assertTrue(self.db.is_iso4217("USD"))
