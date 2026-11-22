# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name,consider-using-with,protected-access

import tempfile
from unittest.mock import patch

from searx.cache import ExpireCacheCfg, ExpireCacheSQLite
from searx.data import currencies as currencies_mod
from searx.data.currencies import CurrenciesDB
from tests import SearxTestCase


class TestCurrenciesDB(SearxTestCase):

    def setUp(self):
        super().setUp()
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        cache = ExpireCacheSQLite.build_cache(
            ExpireCacheCfg(name="test_currencies", db_url=f"{tmpdir.name}/currencies.db")
        )
        patcher = patch.object(currencies_mod, "get_cache", return_value=cache)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.cache = cache
        self.db = CurrenciesDB()

    def test_init_loads_data(self):
        self.db.init()
        self.assertTrue(self.db.is_iso4217("USD"))
        self.assertEqual(self.db.name_to_iso4217("euro"), "EUR")

    def test_self_heals_when_marked_loaded_but_empty(self):
        # Broken state reported in #6500: property says loaded, cache is empty.
        self.cache.properties.set("currencies loaded", "OK")
        self.assertFalse(self.db._is_loaded())
        self.assertTrue(self.db.is_iso4217("USD"))
        self.assertTrue(self.db._is_loaded())

    def test_load_failure_does_not_mark_loaded(self):
        with patch.object(self.db, "load", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                self.db.init()
        self.assertNotEqual(self.cache.properties("currencies loaded"), "OK")
