# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

import tempfile
from unittest import mock

from searx.cache import ExpireCacheCfg, ExpireCacheSQLite
from searx.data.tracker_patterns import TrackerPatternsDB

from tests import SearxTestCase


class TrackerPatternsTest(SearxTestCase):

    def setUp(self):
        super().setUp()
        # An isolated, file-backed cache (not the process-wide DATA_CACHE) so the
        # test is hermetic and does not depend on previously cached rules.
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db")  # pylint: disable=consider-using-with
        self.addCleanup(self._tmp.close)

        self.db = TrackerPatternsDB()
        self.db.cache = ExpireCacheSQLite(ExpireCacheCfg(name="TEST_TRACKER", db_url=self._tmp.name))

        # Pretend the rule set is already loaded so init() never reaches the
        # network, then seed a single well-known rule.
        self.db.cache.properties.set("tracker_patterns loaded", "OK")
        self.db.add((r".*", [], [r"utm_.*"]))
        # add() invalidates the in-process copy; start each test from "not built"
        self.db._rules = None  # pylint: disable=protected-access

    def test_clean_url_strips_tracker_arg(self):
        cleaned = self.db.clean_url("http://example.com/?utm_source=spam&q=keep")
        self.assertEqual(cleaned, "http://example.com/?q=keep")

    def test_clean_url_keeps_untracked_url(self):
        # No tracker args -> rule makes no change -> returns True (use unchanged).
        self.assertTrue(self.db.clean_url("http://example.com/?q=keep"))

    def test_rule_set_read_from_db_once_across_many_calls(self):
        # Regression: clean_url() used to re-read and re-deserialize the whole
        # rule set from SQLite on *every* call.  It must now hit the DB at most
        # once and serve every later call from the in-process copy.
        with mock.patch.object(self.db.cache, "pairs", wraps=self.db.cache.pairs) as spy:
            for i in range(50):
                self.db.clean_url(f"http://example.com/?utm_source=spam&q={i}")
            self.assertEqual(spy.call_count, 1)

    def test_cache_write_invalidates_in_process_copy(self):
        # Build the in-process copy ...
        self.db.clean_url("http://example.com/?utm_source=spam")
        self.assertIsNotNone(self.db._rules)  # pylint: disable=protected-access
        # ... a write to the cache must drop it so the new rule is picked up.
        self.db.add((r".*", [], [r"ref"]))
        self.assertIsNone(self.db._rules)  # pylint: disable=protected-access

        with mock.patch.object(self.db.cache, "pairs", wraps=self.db.cache.pairs) as spy:
            self.db.clean_url("http://example.com/?ref=spam&q=keep")
            self.assertEqual(spy.call_count, 1)
