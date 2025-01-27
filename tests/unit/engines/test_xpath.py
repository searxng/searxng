# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

from collections import defaultdict
import mock

from searx.engines import xpath
from searx import logger

from tests import SearxTestCase

logger = logger.getChild('engines')


class TestXpathEngine(SearxTestCase):
    html = """
    <div>
        <div class="search_result">
            <a class="result" href="https://result1.com">Result 1</a>
            <p class="content">Content 1</p>
            <a class="cached" href="https://cachedresult1.com">Cache</a>
        </div>
        <div class="search_result">
            <a class="result" href="https://result2.com">Result 2</a>
            <p class="content">Content 2</p>
            <a class="cached" href="https://cachedresult2.com">Cache</a>
        </div>
    </div>
    """

    def setUp(self):
        super().setUp()
        xpath.logger = logger.getChild('test_xpath')

    def test_request(self):
        xpath.search_url = 'https://url.com/{query}'
        xpath.categories = []
        xpath.paging = False
        query = 'test_query'
        dicto = defaultdict(dict)
        dicto['language'] = 'all'
        dicto['pageno'] = 1
        params = xpath.request(query, dicto)
        self.assertIn('url', params)
        self.assertEqual('https://url.com/test_query', params['url'])

        xpath.search_url = 'https://url.com/q={query}&p={pageno}'
        xpath.paging = True
        query = 'test_query'
        dicto = defaultdict(dict)
        dicto['language'] = 'all'
        dicto['pageno'] = 1
        params = xpath.request(query, dicto)
        self.assertIn('url', params)
        self.assertEqual('https://url.com/q=test_query&p=1', params['url'])

    def test_response(self):
        # without results_xpath
        xpath.url_xpath = '//div[@class="search_result"]//a[@class="result"]/@href'
        xpath.title_xpath = '//div[@class="search_result"]//a[@class="result"]'
        xpath.content_xpath = '//div[@class="search_result"]//p[@class="content"]'

        self.assertRaises(AttributeError, xpath.response, None)
        self.assertRaises(AttributeError, xpath.response, [])
        self.assertRaises(AttributeError, xpath.response, '')
        self.assertRaises(AttributeError, xpath.response, '[]')

        response = mock.Mock(text='<html></html>', status_code=200)
        self.assertEqual(xpath.response(response), [])

        response = mock.Mock(text=self.html, status_code=200)
        results = xpath.response(response)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['title'], 'Result 1')
        self.assertEqual(results[0]['url'], 'https://result1.com/')
        self.assertEqual(results[0]['content'], 'Content 1')
        self.assertEqual(results[1]['title'], 'Result 2')
        self.assertEqual(results[1]['url'], 'https://result2.com/')
        self.assertEqual(results[1]['content'], 'Content 2')

        # with cached urls, without results_xpath
        xpath.cached_xpath = '//div[@class="search_result"]//a[@class="cached"]/@href'
        results = xpath.response(response)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['cached_url'], 'https://cachedresult1.com')
        self.assertEqual(results[1]['cached_url'], 'https://cachedresult2.com')
        self.assertFalse(results[0].get('is_onion', False))

        # results are onion urls (no results_xpath)
        xpath.categories = ['onions']
        results = xpath.response(response)
        self.assertTrue(results[0]['is_onion'])

    def test_response_results_xpath(self):
        # with results_xpath
        xpath.results_xpath = '//div[@class="search_result"]'
        xpath.url_xpath = './/a[@class="result"]/@href'
        xpath.title_xpath = './/a[@class="result"]'
        xpath.content_xpath = './/p[@class="content"]'
        xpath.cached_xpath = None
        xpath.categories = []

        self.assertRaises(AttributeError, xpath.response, None)
        self.assertRaises(AttributeError, xpath.response, [])
        self.assertRaises(AttributeError, xpath.response, '')
        self.assertRaises(AttributeError, xpath.response, '[]')

        response = mock.Mock(text='<html></html>', status_code=200)
        self.assertEqual(xpath.response(response), [])

        response = mock.Mock(text=self.html, status_code=200)
        results = xpath.response(response)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['title'], 'Result 1')
        self.assertEqual(results[0]['url'], 'https://result1.com/')
        self.assertEqual(results[0]['content'], 'Content 1')
        self.assertEqual(results[1]['title'], 'Result 2')
        self.assertEqual(results[1]['url'], 'https://result2.com/')
        self.assertEqual(results[1]['content'], 'Content 2')

        # with cached urls, with results_xpath
        xpath.cached_xpath = './/a[@class="cached"]/@href'
        results = xpath.response(response)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['cached_url'], 'https://cachedresult1.com')
        self.assertEqual(results[1]['cached_url'], 'https://cachedresult2.com')
        self.assertFalse(results[0].get('is_onion', False))

        # results are onion urls (with results_xpath)
        xpath.categories = ['onions']
        results = xpath.response(response)
        self.assertTrue(results[0]['is_onion'])
