# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from collections import defaultdict
import mock

from searx.engines import json_engine
from searx import logger

from tests import SearxTestCase

logger = logger.getChild('engines')


class TestJsonEngine(SearxTestCase):  # pylint: disable=missing-class-docstring
    json = """
    [
        {
            "title": "title0",
            "content": "content0",
            "url": "https://example.com/url0",
            "images": [
                {
                    "thumb": "https://example.com/thumb00"
                },
                {
                    "thumb": "https://example.com/thumb01"
                }
            ]
        },
        {
            "title": "<h1>title1</h1>",
            "content": "<h2>content1</h2>",
            "url": "https://example.com/url1",
            "images": [
                {
                    "thumb": "https://example.com/thumb10"
                },
                {
                    "thumb": "https://example.com/thumb11"
                }
            ]
        },
        {
            "title": "title2",
            "content": "content2",
            "url": 2,
            "images": [
                {
                    "thumb": "thumb20"
                },
                {
                    "thumb": 21
                }
            ]
        }
    ]
    """

    json_result_query = """
    {
        "data": {
            "results": [
                {
                    "title": "title0",
                    "content": "content0",
                    "url": "https://example.com/url0",
                    "images": [
                        {
                            "thumb": "https://example.com/thumb00"
                        },
                        {
                            "thumb": "https://example.com/thumb01"
                        }
                    ]
                },
                {
                    "title": "<h1>title1</h1>",
                    "content": "<h2>content1</h2>",
                    "url": "https://example.com/url1",
                    "images": [
                        {
                            "thumb": "https://example.com/thumb10"
                        },
                        {
                            "thumb": "https://example.com/thumb11"
                        }
                    ]
                },
                {
                    "title": "title2",
                    "content": "content2",
                    "url": 2,
                    "images": [
                        {
                            "thumb": "thumb20"
                        },
                        {
                            "thumb": 21
                        }
                    ]
                }
            ],
            "suggestions": [
                "suggestion0",
                "suggestion1"
            ]
        }
    }
    """

    def setUp(self):
        json_engine.logger = logger.getChild('test_json_engine')

    def test_request(self):
        json_engine.search_url = 'https://example.com/{query}'
        json_engine.categories = []
        json_engine.paging = False
        query = 'test_query'
        dicto = defaultdict(dict)
        dicto['language'] = 'all'
        dicto['pageno'] = 1
        params = json_engine.request(query, dicto)
        self.assertIn('url', params)
        self.assertEqual('https://example.com/test_query', params['url'])

        json_engine.search_url = 'https://example.com/q={query}&p={pageno}'
        json_engine.paging = True
        query = 'test_query'
        dicto = defaultdict(dict)
        dicto['language'] = 'all'
        dicto['pageno'] = 1
        params = json_engine.request(query, dicto)
        self.assertIn('url', params)
        self.assertEqual('https://example.com/q=test_query&p=1', params['url'])

        json_engine.search_url = 'https://example.com/'
        json_engine.paging = True
        json_engine.request_body = '{{"page": {pageno}, "query": "{query}"}}'
        query = 'test_query'
        dicto = defaultdict(dict)
        dicto['language'] = 'all'
        dicto['pageno'] = 1
        params = json_engine.request(query, dicto)
        self.assertIn('data', params)
        self.assertEqual('{"page": 1, "query": "test_query"}', params['data'])

    def test_response(self):
        # without results_query
        json_engine.results_query = ''
        json_engine.url_query = 'url'
        json_engine.url_prefix = ''
        json_engine.title_query = 'title'
        json_engine.content_query = 'content'
        json_engine.thumbnail_query = 'images/thumb'
        json_engine.thumbnail_prefix = ''
        json_engine.title_html_to_text = False
        json_engine.content_html_to_text = False
        json_engine.categories = []

        self.assertRaises(AttributeError, json_engine.response, None)
        self.assertRaises(AttributeError, json_engine.response, [])
        self.assertRaises(AttributeError, json_engine.response, '')
        self.assertRaises(AttributeError, json_engine.response, '[]')

        response = mock.Mock(text='{}', status_code=200)
        self.assertEqual(json_engine.response(response), [])

        response = mock.Mock(text=self.json, status_code=200)
        results = json_engine.response(response)
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['title'], 'title0')
        self.assertEqual(results[0]['url'], 'https://example.com/url0')
        self.assertEqual(results[0]['content'], 'content0')
        self.assertEqual(results[0]['thumbnail'], 'https://example.com/thumb00')
        self.assertEqual(results[1]['title'], '<h1>title1</h1>')
        self.assertEqual(results[1]['url'], 'https://example.com/url1')
        self.assertEqual(results[1]['content'], '<h2>content1</h2>')
        self.assertEqual(results[1]['thumbnail'], 'https://example.com/thumb10')

        # with prefix and suggestions without results_query
        json_engine.url_prefix = 'https://example.com/url'
        json_engine.thumbnail_query = 'images/1/thumb'
        json_engine.thumbnail_prefix = 'https://example.com/thumb'

        results = json_engine.response(response)
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[2]['title'], 'title2')
        self.assertEqual(results[2]['url'], 'https://example.com/url2')
        self.assertEqual(results[2]['content'], 'content2')
        self.assertEqual(results[2]['thumbnail'], 'https://example.com/thumb21')
        self.assertFalse(results[0].get('is_onion', False))

        # results are onion urls without results_query
        json_engine.categories = ['onions']
        results = json_engine.response(response)
        self.assertTrue(results[0]['is_onion'])

    def test_response_results_json(self):
        # with results_query
        json_engine.results_query = 'data/results'
        json_engine.url_query = 'url'
        json_engine.url_prefix = ''
        json_engine.title_query = 'title'
        json_engine.content_query = 'content'
        json_engine.thumbnail_query = 'images/1/thumb'
        json_engine.thumbnail_prefix = ''
        json_engine.title_html_to_text = True
        json_engine.content_html_to_text = True
        json_engine.categories = []

        self.assertRaises(AttributeError, json_engine.response, None)
        self.assertRaises(AttributeError, json_engine.response, [])
        self.assertRaises(AttributeError, json_engine.response, '')
        self.assertRaises(AttributeError, json_engine.response, '[]')

        response = mock.Mock(text='{}', status_code=200)
        self.assertEqual(json_engine.response(response), [])

        response = mock.Mock(text=self.json_result_query, status_code=200)
        results = json_engine.response(response)
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['title'], 'title0')
        self.assertEqual(results[0]['url'], 'https://example.com/url0')
        self.assertEqual(results[0]['content'], 'content0')
        self.assertEqual(results[0]['thumbnail'], 'https://example.com/thumb01')
        self.assertEqual(results[1]['title'], 'title1')
        self.assertEqual(results[1]['url'], 'https://example.com/url1')
        self.assertEqual(results[1]['content'], 'content1')
        self.assertEqual(results[1]['thumbnail'], 'https://example.com/thumb11')

        # with prefix and suggestions with results_query
        json_engine.url_prefix = 'https://example.com/url'
        json_engine.thumbnail_query = 'images/1/thumb'
        json_engine.thumbnail_prefix = 'https://example.com/thumb'
        json_engine.suggestion_query = 'data/suggestions'

        results = json_engine.response(response)
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 4)
        self.assertEqual(results[2]['title'], 'title2')
        self.assertEqual(results[2]['url'], 'https://example.com/url2')
        self.assertEqual(results[2]['content'], 'content2')
        self.assertEqual(results[2]['thumbnail'], 'https://example.com/thumb21')
        self.assertEqual(results[3]['suggestion'], ['suggestion0', 'suggestion1'])
        self.assertFalse(results[0].get('is_onion', False))

        # results are onion urls with results_query
        json_engine.categories = ['onions']
        results = json_engine.response(response)
        self.assertTrue(results[0]['is_onion'])
