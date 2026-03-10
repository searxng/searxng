# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring

import logging
import threading
from collections import defaultdict
from unittest.mock import Mock

from tests import SearxTestCase


class FakeCache:

    def __init__(self):
        self.store: dict[str, str] = {}
        self._lock = threading.Lock()

    def get(self, key, default=None, **kwargs):
        with self._lock:
            return self.store.get(key, default)

    def set(self, key, value, expire=None, **kwargs):
        with self._lock:
            self.store[key] = value

    def secret_hash(self, value):
        return str(value)


class FakeTraits:

    all_locale = "wt-wt"

    def __init__(self):
        self.custom = {"lang_region": {}}

    def get_region(self, sxng_locale, default):
        if sxng_locale == "all":
            return default
        return "us-en"

    def get_language(self, sxng_locale, default):
        return "en_US"


class DuckDuckGoTests(SearxTestCase):

    def setUp(self):
        super().setUp()

        import searx.engines.duckduckgo as duckduckgo
        import searx.engines.duckduckgo_extra as duckduckgo_extra
        import searx.engines.duckduckgo_weather as duckduckgo_weather

        self.ddg = duckduckgo
        self.ddg_extra = duckduckgo_extra
        self.ddg_weather = duckduckgo_weather

        self.cache = FakeCache()
        self.traits = FakeTraits()
        self.logger = logging.getLogger("tests.ddg")

        self._set_module_attr(self.ddg, "logger", self.logger)
        self._set_module_attr(self.ddg_extra, "logger", self.logger)
        self._set_module_attr(self.ddg_weather, "logger", self.logger)

        self._set_module_attr(self.ddg, "traits", self.traits)
        self._set_module_attr(self.ddg_extra, "traits", self.traits)
        self._set_module_attr(self.ddg_weather, "traits", self.traits)

        self.setattr4test(self.ddg, "get_cache", lambda: self.cache)
        self.setattr4test(self.ddg, "_CACHE", None)
        self.setattr4test(self.ddg_extra, "ddg_category", "images")
        self._set_time_ms(0)

    def _set_module_attr(self, module, attr, value):
        if hasattr(module, attr):
            self.setattr4test(module, attr, value)
            return

        setattr(module, attr, value)

        def cleanup():
            delattr(module, attr)

        self.addCleanup(cleanup)

    def _set_time_ms(self, now_ms):
        self.setattr4test(self.ddg.time, "time", lambda: now_ms / 1000)

    def _make_params(self, **overrides):
        params = defaultdict(dict)
        params["headers"] = {}
        params["data"] = {}
        params["cookies"] = {}
        params["searxng_locale"] = "en-US"
        params["pageno"] = 1
        params["time_range"] = None
        params["safesearch"] = 0
        params.update(overrides)
        return params

    def test_web_request_rate_limits_with_exact_threshold(self):
        params = self._make_params()

        self.ddg.request("open source", params)

        self.assertEqual(self.ddg.ddg_url, params["url"])
        self.assertEqual("POST", params["method"])
        self.assertFalse(any(key.startswith("Sec-Fetch-") for key in params["headers"]))

        self._set_time_ms(2999)
        skipped_params = self._make_params()
        self.ddg.request("open source", skipped_params)
        self.assertIsNone(skipped_params["url"])

        self._set_time_ms(3000)
        resumed_params = self._make_params()
        self.ddg.request("open source", resumed_params)
        self.assertEqual(self.ddg.ddg_url, resumed_params["url"])
        self.assertEqual("POST", resumed_params["method"])

    def test_captcha_sets_global_cooldown_and_raises(self):
        self._set_time_ms(12_345)
        response = Mock()
        response.status_code = 200
        response.text = '<html><body><form id="challenge-form"></form></body></html>'
        response.search_params = {"data": {"kl": "us-en"}}

        with self.assertRaises(self.ddg.SearxEngineCaptchaException) as exc:
            self.ddg.response(response)

        self.assertGreater(exc.exception.suspended_time, 0)
        self.assertEqual(
            12_345 + self.ddg._DDG_CAPTCHA_COOLDOWN_MS,
            self.ddg.get_ddg_global_blocked_until_ms(),
        )

    def test_captcha_does_not_shorten_existing_cooldown(self):
        self._set_time_ms(12_345)
        self.ddg.set_ddg_global_blocked_until_ms(9_999_999)

        response = Mock()
        response.status_code = 200
        response.text = '<html><body><form id="challenge-form"></form></body></html>'
        response.search_params = {"data": {"kl": "us-en"}}

        with self.assertRaises(self.ddg.SearxEngineCaptchaException):
            self.ddg.response(response)

        self.assertEqual(9_999_999, self.ddg.get_ddg_global_blocked_until_ms())

    def test_web_request_skips_when_global_cooldown_is_active(self):
        self._set_time_ms(5_000)
        self.ddg.set_ddg_global_blocked_until_ms(8_000)

        params = self._make_params()
        self.ddg.request("blocked", params)

        self.assertIsNone(params["url"])

    def test_global_cooldown_has_priority_over_web_rate_limit_slot(self):
        self._set_time_ms(5_000)
        self.ddg.set_ddg_global_blocked_until_ms(8_000)
        self.cache.store[self.ddg._DDG_WEB_NEXT_ALLOWED_AT_KEY] = "0"

        params = self._make_params()
        self.ddg.request("blocked", params)

        self.assertIsNone(params["url"])
        self.assertEqual(
            0, self.ddg._get_cache_int(self.ddg._DDG_WEB_NEXT_ALLOWED_AT_KEY)
        )

    def test_extra_request_honors_global_cooldown_before_vqd_lookup(self):
        self._set_time_ms(5_000)
        self.ddg.set_ddg_global_blocked_until_ms(8_000)
        self.setattr4test(
            self.ddg_extra,
            "get_vqd",
            lambda **kwargs: self.fail("get_vqd should not run"),
        )
        self.setattr4test(
            self.ddg_extra,
            "fetch_vqd",
            lambda **kwargs: self.fail("fetch_vqd should not run"),
        )

        params = self._make_params()
        self.ddg_extra.request("cats", params)

        self.assertIsNone(params["url"])

    def test_fetch_vqd_honors_global_cooldown_before_network_get(self):
        self._set_time_ms(5_000)
        self.ddg.set_ddg_global_blocked_until_ms(8_000)
        self.setattr4test(
            self.ddg_extra,
            "get",
            lambda **kwargs: self.fail("network get should not run"),
        )

        params = self._make_params()

        self.assertEqual("", self.ddg_extra.fetch_vqd("cats", params))

    def test_extra_request_skips_when_vqd_is_unavailable(self):
        self._set_time_ms(9_000)
        self.ddg.set_ddg_global_blocked_until_ms(8_000)
        self.setattr4test(self.ddg_extra, "get_vqd", lambda **kwargs: "")
        self.setattr4test(self.ddg_extra, "fetch_vqd", lambda **kwargs: "")

        params = self._make_params()
        self.ddg_extra.request("cats", params)

        self.assertIsNone(params["url"])

    def test_extra_request_resumes_after_global_cooldown_expires(self):
        self._set_time_ms(9_000)
        self.ddg.set_ddg_global_blocked_until_ms(8_000)
        self.setattr4test(self.ddg_extra, "get_vqd", lambda **kwargs: "cached-vqd")

        params = self._make_params()
        self.ddg_extra.request("cats", params)

        self.assertIn("/i.js?", params["url"])
        self.assertIn("vqd=cached-vqd", params["url"])

    def test_weather_request_honors_global_cooldown(self):
        self._set_time_ms(5_000)
        self.ddg.set_ddg_global_blocked_until_ms(8_000)

        params = self._make_params()
        self.ddg_weather.request("Paris", params)

        self.assertIsNone(params["url"])
        self.assertEqual({}, params["cookies"])

    def test_weather_request_resumes_after_global_cooldown_expires(self):
        self._set_time_ms(9_000)
        self.ddg.set_ddg_global_blocked_until_ms(8_000)

        params = self._make_params()
        self.ddg_weather.request("Paris", params)

        self.assertIn("/js/spice/forecast/Paris/en", params["url"])
        self.assertEqual("en_US", params["cookies"]["ad"])
        self.assertEqual("us-en", params["cookies"]["ah"])
        self.assertEqual("us-en", params["cookies"]["l"])

    def test_vqd_missed_keeps_zero_suspension(self):
        params = self._make_params(pageno=2)

        with self.assertRaises(self.ddg.SearxEngineCaptchaException) as exc:
            self.ddg.request("next page", params)

        self.assertEqual(0, exc.exception.suspended_time)
        self.assertIn("VQD missed", exc.exception.message)
        self.assertEqual(0, self.ddg.get_ddg_global_blocked_until_ms())

    def test_long_query_skip_does_not_consume_rate_limit_slot(self):
        skipped_params = self._make_params()

        self.ddg.request("x" * 500, skipped_params)

        self.assertIsNone(skipped_params["url"])
        self.assertEqual(
            0, self.ddg._get_cache_int(self.ddg._DDG_WEB_NEXT_ALLOWED_AT_KEY)
        )

        allowed_params = self._make_params()
        self.ddg.request("short query", allowed_params)
        self.assertEqual(self.ddg.ddg_url, allowed_params["url"])

    def test_invalid_cached_state_is_ignored(self):
        self.cache.store[self.ddg._DDG_GLOBAL_BLOCKED_UNTIL_KEY] = "bad-value"
        self.cache.store[self.ddg._DDG_WEB_NEXT_ALLOWED_AT_KEY] = "also-bad"

        params = self._make_params()
        self.ddg.request("open source", params)

        self.assertEqual(self.ddg.ddg_url, params["url"])
        self.assertEqual(0, self.ddg.get_ddg_global_blocked_until_ms())

    def test_set_global_cooldown_is_monotonic(self):
        self.ddg.set_ddg_global_blocked_until_ms(9_000)
        self.ddg.set_ddg_global_blocked_until_ms(8_000)

        self.assertEqual(9_000, self.ddg.get_ddg_global_blocked_until_ms())

    def test_web_rate_limit_remains_active_after_global_cooldown_expires(self):
        self._set_time_ms(5_000)
        self.ddg.set_ddg_global_blocked_until_ms(8_000)

        skipped_params = self._make_params()
        self.ddg.request("blocked", skipped_params)
        self.assertIsNone(skipped_params["url"])

        self._set_time_ms(9_000)
        first_params = self._make_params()
        self.ddg.request("resumed", first_params)
        self.assertEqual(self.ddg.ddg_url, first_params["url"])

        self._set_time_ms(10_000)
        throttled_params = self._make_params()
        self.ddg.request("resumed", throttled_params)
        self.assertIsNone(throttled_params["url"])

    def test_extra_long_query_skips_without_vqd_lookup(self):
        self.setattr4test(
            self.ddg_extra,
            "get_vqd",
            lambda **kwargs: self.fail("get_vqd should not run"),
        )
        self.setattr4test(
            self.ddg_extra,
            "fetch_vqd",
            lambda **kwargs: self.fail("fetch_vqd should not run"),
        )

        params = self._make_params()
        self.ddg_extra.request("x" * 500, params)

        self.assertIsNone(params["url"])

    def test_page2_without_vqd_raises_captcha_zero_suspension(self):
        params_p1 = self._make_params(pageno=1)
        self.ddg.request("search query", params_p1)
        self.assertEqual(self.ddg.ddg_url, params_p1["url"])

        self._set_time_ms(5_000)
        params_p2 = self._make_params(pageno=2)
        with self.assertRaises(self.ddg.SearxEngineCaptchaException) as exc:
            self.ddg.request("search query", params_p2)

        self.assertEqual(0, exc.exception.suspended_time)
        self.assertIn("VQD missed", exc.exception.message)
        # Global cooldown must NOT be set for a VQD miss
        self.assertEqual(0, self.ddg.get_ddg_global_blocked_until_ms())

    def test_concurrent_web_requests_allow_only_one_slot(self):
        self._set_time_ms(10_000)
        params_list = [self._make_params() for _ in range(3)]
        errors = []

        def run_request(params):
            try:
                self.ddg.request("parallel", params)
            except Exception as exc:  # pragma: no cover
                errors.append(exc)

        threads = [
            threading.Thread(target=run_request, args=(params,))
            for params in params_list
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual([], errors)
        self.assertEqual(
            1, sum(1 for params in params_list if params["url"] == self.ddg.ddg_url)
        )
        self.assertEqual(2, sum(1 for params in params_list if params["url"] is None))
