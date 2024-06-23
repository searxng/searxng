# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from searx.search import SearchQuery, EngineRef
from searx.search.processors import online
from searx.engines import load_engines
from searx import engines

from tests import SearxTestCase

TEST_ENGINE_NAME = 'dummy engine'
TEST_ENGINE = {
    'name': TEST_ENGINE_NAME,
    'engine': 'dummy',
    'categories': 'general',
    'shortcut': 'du',
    'timeout': 3.0,
    'tokens': [],
}


class TestOnlineProcessor(SearxTestCase):  # pylint: disable=missing-class-docstring

    def setUp(self):
        load_engines([TEST_ENGINE])

    def tearDown(self):
        load_engines([])

    def _get_params(self, online_processor, search_query, engine_category):
        params = online_processor.get_params(search_query, engine_category)
        self.assertIsNotNone(params)
        assert params is not None
        return params

    def test_get_params_default_params(self):
        engine = engines.engines[TEST_ENGINE_NAME]
        online_processor = online.OnlineProcessor(engine, TEST_ENGINE_NAME)
        search_query = SearchQuery('test', [EngineRef(TEST_ENGINE_NAME, 'general')], 'all', 0, 1, None, None, None)
        params = self._get_params(online_processor, search_query, 'general')
        self.assertIn('method', params)
        self.assertIn('headers', params)
        self.assertIn('data', params)
        self.assertIn('url', params)
        self.assertIn('cookies', params)
        self.assertIn('auth', params)

    def test_get_params_useragent(self):
        engine = engines.engines[TEST_ENGINE_NAME]
        online_processor = online.OnlineProcessor(engine, TEST_ENGINE_NAME)
        search_query = SearchQuery('test', [EngineRef(TEST_ENGINE_NAME, 'general')], 'all', 0, 1, None, None, None)
        params = self._get_params(online_processor, search_query, 'general')
        self.assertIn('User-Agent', params['headers'])
