# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

import mock
from lxml import html
from urllib.parse import parse_qs

from searx.engines import kagi
from searx.exceptions import SearxEngineAPIException
from tests import SearxTestCase


class TestKagiEngine(SearxTestCase):

    def setUp(self):
        self.test_html = """
        <div class="_0_main-search-results">
            <div class="_0_SRI search-result">
                <div class="_0_TITLE __sri-title">
                    <h3 class="__sri-title-box">
                        <a class="__sri_title_link _ext_t" href="https://example1.com">Result 1</a>
                    </h3>
                </div>
                <div class="__sri-url-box">
                    <span class="host">example1.com</span>
                </div>
                <div class="__sri-body">
                    <div class="__sri-desc">Content 1</div>
                </div>
            </div>
            <div class="_0_SRI search-result">
                <div class="_0_TITLE __sri-title">
                    <h3 class="__sri-title-box">
                        <a class="__sri_title_link _ext_t" href="https://example2.com">Result 2</a>
                    </h3>
                </div>
                <div class="__sri-url-box">
                    <span class="host">example2.com</span>
                </div>
                <div class="__sri-body">
                    <div class="__sri-desc">Content 2</div>
                </div>
            </div>
        </div>
        """

    def test_request(self):
        # Test with missing API token
        kagi.token = None
        params = {'pageno': 1, 'headers': {}}
        self.assertRaises(SearxEngineAPIException, kagi.request, 'test query', params)

        # Test with valid API token but no cookie
        kagi.token = 'test_token'
        params = {'pageno': 1, 'headers': {}, 'cookies': {}}
        query = 'test query'
        request_params = kagi.request(query, params)

        self.assertIn('url', request_params)
        self.assertIn('token=test_token', request_params['url'])
        self.assertIn('q=test+query', request_params['url'])
        self.assertEqual(request_params['max_redirects'], 1)
        self.assertTrue(request_params['allow_redirects'])

        # Test with both required cookies
        params['cookies']['kagi_session'] = 'test_session'
        params['cookies']['_kagi_search_'] = 'test_search'
        request_params = kagi.request(query, params)
        self.assertNotIn('token=', request_params['url'])
        self.assertIn('q=test+query', request_params['url'])
        self.assertEqual(request_params['max_redirects'], 1)
        self.assertTrue(request_params['allow_redirects'])

        # Test with missing search cookie
        params['cookies'] = {'kagi_session': 'test_session'}
        request_params = kagi.request(query, params)
        self.assertIn('token=', request_params['url'])

        # Test with missing session cookie
        params['cookies'] = {'_kagi_search_': 'test_search'}
        request_params = kagi.request(query, params)
        self.assertIn('token=', request_params['url'])

        # Test pagination
        params['pageno'] = 2
        request_params = kagi.request(query, params)
        self.assertIn('batch=2', request_params['url'])
        self.assertEqual(request_params['max_redirects'], 1)

    def test_response(self):
        def verify_cookie_capture(cookie_headers, expected_session, expected_search):
            mock_headers = mock.Mock()
            mock_headers.get_list = mock.Mock(return_value=cookie_headers)
            mock_headers.__contains__ = mock.Mock(return_value=True)

            response = mock.Mock(
                text=self.test_html, status_code=200, headers=mock_headers, search_params={'cookies': {}}
            )
            results = kagi.response(response)

            self.assertEqual(response.search_params['cookies'].get('kagi_session'), expected_session)
            self.assertEqual(response.search_params['cookies'].get('_kagi_search_'), expected_search)
            return results

        # Test cookie capture with standard attributes
        results = verify_cookie_capture(
            ['kagi_session=test_session; Path=/; HttpOnly', '_kagi_search_=test_search; Path=/; HttpOnly'],
            'test_session',
            'test_search',
        )

        # Test cookie capture with additional attributes
        results = verify_cookie_capture(
            [
                'kagi_session=test_session2; Path=/; HttpOnly; SameSite=Lax',
                '_kagi_search_=test_search2; Domain=.kagi.com; Path=/; SameSite=Lax',
            ],
            'test_session2',
            'test_search2',
        )

        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 2)  # 2 search results

        # Check first result
        self.assertEqual(results[0]['title'], 'Result 1')
        self.assertEqual(results[0]['url'], 'https://example1.com')
        self.assertEqual(results[0]['content'], 'Content 1')
        self.assertEqual(results[0]['domain'], 'example1.com')

        # Check second result
        self.assertEqual(results[1]['title'], 'Result 2')
        self.assertEqual(results[1]['url'], 'https://example2.com')
        self.assertEqual(results[1]['content'], 'Content 2')
        self.assertEqual(results[1]['domain'], 'example2.com')

    def test_response_error_handling(self):
        # Test invalid token/cookie response
        response = mock.Mock(
            text='', status_code=401, search_params={'cookies': {'kagi_session': 'invalid_session'}}, headers={}
        )
        self.assertRaises(SearxEngineAPIException, kagi.response, response)
        # Verify invalid cookie was cleared
        self.assertNotIn('kagi_session', response.search_params['cookies'])

        # Test rate limit response
        response = mock.Mock(text='', status_code=429, search_params={'cookies': {}}, headers={})
        self.assertRaises(SearxEngineAPIException, kagi.response, response)

        # Test other error response
        response = mock.Mock(text='', status_code=500, search_params={'cookies': {}}, headers={})
        self.assertRaises(SearxEngineAPIException, kagi.response, response)
