# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

import tempfile
from unittest import mock

from searx.cache import ExpireCacheCfg, ExpireCacheSQLite
from searx.data.currencies import CurrenciesDB
from searx.data.tracker_patterns import TrackerPatternsDB

from tests import SearxTestCase


class DataCacheTestCase(SearxTestCase):

    def setUp(self):
        super().setUp()
        self.tmp_dir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.cache = ExpireCacheSQLite.build_cache(
            ExpireCacheCfg(name="TEST_DATA_CACHE", db_url=f"{self.tmp_dir.name}/data_cache.db")
        )

    def tearDown(self):
        self.tmp_dir.cleanup()
        super().tearDown()

    def new_db(self, db_class):
        with (
            mock.patch("searx.data.currencies.get_cache", return_value=self.cache),
            mock.patch("searx.data.tracker_patterns.get_cache", return_value=self.cache),
        ):
            return db_class()


class TestCurrenciesDB(DataCacheTestCase):

    def test_is_iso4217_on_fresh_cache(self):
        currencies = self.new_db(CurrenciesDB)
        self.assertTrue(currencies.is_iso4217("USD"))

    def test_reload_after_truncate(self):
        # e.g. the server.secret_key has changed, all cache tables are truncated
        currencies = self.new_db(CurrenciesDB)
        self.assertEqual(currencies.name_to_iso4217("euro"), "EUR")
        self.cache.truncate_tables(self.cache.table_names)
        self.assertEqual(currencies.name_to_iso4217("euro"), "EUR")
        self.assertTrue(currencies.is_iso4217("USD"))

    def test_reload_after_expire(self):
        currencies = self.new_db(CurrenciesDB)
        self.assertTrue(currencies.is_iso4217("USD"))
        with mock.patch("time.time", return_value=9_999_999_999):
            self.assertTrue(currencies.is_iso4217("USD"))


class TestTrackerPatternsDB(DataCacheTestCase):

    rule = (r"^https?://example\.org", [], ["utm_source"])

    def test_reload_after_truncate(self):
        tracker_patterns = self.new_db(TrackerPatternsDB)
        with mock.patch.object(TrackerPatternsDB, "iter_clear_list", return_value=iter([self.rule])):
            self.assertEqual(list(tracker_patterns.rules()), [self.rule])
        self.cache.truncate_tables(self.cache.table_names)
        with mock.patch.object(TrackerPatternsDB, "iter_clear_list", return_value=iter([self.rule])):
            self.assertEqual(list(tracker_patterns.rules()), [self.rule])
