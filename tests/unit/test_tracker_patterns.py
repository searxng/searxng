# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name,consider-using-with

import tempfile
from unittest.mock import patch

from searx.cache import ExpireCacheCfg, ExpireCacheSQLite
from searx.data import tracker_patterns as tracker_patterns_mod
from searx.data.tracker_patterns import TrackerPatternsDB
from tests import SearxTestCase


class TestTrackerPatternsDB(SearxTestCase):

    def setUp(self):
        super().setUp()
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        cache = ExpireCacheSQLite.build_cache(
            ExpireCacheCfg(name="test_tracker_patterns", db_url=f"{tmpdir.name}/tracker.db")
        )
        patcher = patch.object(tracker_patterns_mod, "get_cache", return_value=cache)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.cache = cache
        self.db = TrackerPatternsDB()

    def test_set_if_absent_is_atomic(self):
        self.assertTrue(self.cache.properties.set_if_absent("key", "first"))
        self.assertFalse(self.cache.properties.set_if_absent("key", "second"))
        self.assertEqual(self.cache.properties("key"), "first")

    def test_init_loads_once(self):
        with patch.object(self.db, "load") as load:
            self.db.init()
            self.db.init()
        load.assert_called_once()

    def test_init_retries_after_failure(self):
        with patch.object(self.db, "load", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                self.db.init()
        self.assertIsNone(self.cache.properties("tracker_patterns loaded"))

        with patch.object(self.db, "load") as load:
            self.db.init()
        load.assert_called_once()
