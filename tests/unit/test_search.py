# -*- coding: utf-8 -*-

from copy import copy

import searx.search
from searx.search import SearchQuery, EngineRef
from searx import settings
from tests import SearxTestCase


SAFESEARCH = 0
PAGENO = 1
PUBLIC_ENGINE_NAME = 'general dummy'
TEST_ENGINES = [
    {
        'name': PUBLIC_ENGINE_NAME,
        'engine': 'dummy',
        'categories': 'general',
        'shortcut': 'gd',
        'timeout': 3.0,
        'tokens': [],
    },
]


class SearchQueryTestCase(SearxTestCase):
    def test_repr(self):
        s = SearchQuery('test', [EngineRef('bing', 'general')], 'all', 0, 1, '1', 5.0, 'g')
        self.assertEqual(
            repr(s), "SearchQuery('test', [EngineRef('bing', 'general')], 'all', 0, 1, '1', 5.0, 'g')"
        )  # noqa

    def test_eq(self):
        s = SearchQuery('test', [EngineRef('bing', 'general')], 'all', 0, 1, None, None, None)
        t = SearchQuery('test', [EngineRef('google', 'general')], 'all', 0, 1, None, None, None)
        self.assertEqual(s, s)
        self.assertNotEqual(s, t)

    def test_copy(self):
        s = SearchQuery('test', [EngineRef('bing', 'general')], 'all', 0, 1, None, None, None)
        t = copy(s)
        self.assertEqual(s, t)


class SearchTestCase(SearxTestCase):
    @classmethod
    def setUpClass(cls):
        searx.search.initialize(TEST_ENGINES)

    def test_timeout_simple(self):
        settings['outgoing']['max_request_timeout'] = None
        search_query = SearchQuery(
            'test', [EngineRef(PUBLIC_ENGINE_NAME, 'general')], 'en-US', SAFESEARCH, PAGENO, None, None
        )
        search = searx.search.Search(search_query)
        search.search()
        self.assertEqual(search.actual_timeout, 3.0)

    def test_timeout_query_above_default_nomax(self):
        settings['outgoing']['max_request_timeout'] = None
        search_query = SearchQuery(
            'test', [EngineRef(PUBLIC_ENGINE_NAME, 'general')], 'en-US', SAFESEARCH, PAGENO, None, 5.0
        )
        search = searx.search.Search(search_query)
        search.search()
        self.assertEqual(search.actual_timeout, 3.0)

    def test_timeout_query_below_default_nomax(self):
        settings['outgoing']['max_request_timeout'] = None
        search_query = SearchQuery(
            'test', [EngineRef(PUBLIC_ENGINE_NAME, 'general')], 'en-US', SAFESEARCH, PAGENO, None, 1.0
        )
        search = searx.search.Search(search_query)
        search.search()
        self.assertEqual(search.actual_timeout, 1.0)

    def test_timeout_query_below_max(self):
        settings['outgoing']['max_request_timeout'] = 10.0
        search_query = SearchQuery(
            'test', [EngineRef(PUBLIC_ENGINE_NAME, 'general')], 'en-US', SAFESEARCH, PAGENO, None, 5.0
        )
        search = searx.search.Search(search_query)
        search.search()
        self.assertEqual(search.actual_timeout, 5.0)

    def test_timeout_query_above_max(self):
        settings['outgoing']['max_request_timeout'] = 10.0
        search_query = SearchQuery(
            'test', [EngineRef(PUBLIC_ENGINE_NAME, 'general')], 'en-US', SAFESEARCH, PAGENO, None, 15.0
        )
        search = searx.search.Search(search_query)
        search.search()
        self.assertEqual(search.actual_timeout, 10.0)

    def test_external_bang(self):
        search_query = SearchQuery(
            'yes yes',
            [EngineRef(PUBLIC_ENGINE_NAME, 'general')],
            'en-US',
            SAFESEARCH,
            PAGENO,
            None,
            None,
            external_bang="yt",
        )
        search = searx.search.Search(search_query)
        results = search.search()
        # For checking if the user redirected with the youtube external bang
        self.assertTrue(results.redirect_url is not None)

        search_query = SearchQuery(
            'youtube never gonna give you up',
            [EngineRef(PUBLIC_ENGINE_NAME, 'general')],
            'en-US',
            SAFESEARCH,
            PAGENO,
            None,
            None,
        )

        search = searx.search.Search(search_query)
        results = search.search()
        # This should not redirect
        self.assertTrue(results.redirect_url is None)
