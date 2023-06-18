# -*- coding: utf-8 -*-

import json
from urllib.parse import ParseResult
from mock import Mock
from searx.results import Timing

import searx.search.processors
from searx.search import Search
from searx.preferences import Preferences
from tests import SearxTestCase


class ViewsTestCase(SearxTestCase):
    def setUp(self):
        # skip init function (no external HTTP request)
        def dummy(*args, **kwargs):
            pass

        self.setattr4test(searx.search.processors, 'initialize_processor', dummy)

        from searx import webapp  # pylint disable=import-outside-toplevel

        webapp.app.config['TESTING'] = True  # to get better error messages
        self.app = webapp.app.test_client()

        # remove sha for the static file
        # so the tests don't have to care about the changing URLs
        for k in webapp.static_files:
            webapp.static_files[k] = None

        # set some defaults
        test_results = [
            {
                'content': 'first test content',
                'title': 'First Test',
                'url': 'http://first.test.xyz',
                'engines': ['youtube', 'startpage'],
                'engine': 'startpage',
                'parsed_url': ParseResult(
                    scheme='http', netloc='first.test.xyz', path='/', params='', query='', fragment=''
                ),
                'template': 'default.html',
            },
            {
                'content': 'second test content',
                'title': 'Second Test',
                'url': 'http://second.test.xyz',
                'engines': ['youtube', 'startpage'],
                'engine': 'youtube',
                'parsed_url': ParseResult(
                    scheme='http', netloc='second.test.xyz', path='/', params='', query='', fragment=''
                ),
                'template': 'default.html',
            },
        ]

        timings = [
            Timing(engine='startpage', total=0.8, load=0.7),
            Timing(engine='youtube', total=0.9, load=0.6),
        ]

        def search_mock(search_self, *args):
            search_self.result_container = Mock(
                get_ordered_results=lambda: test_results,
                answers=dict(),
                corrections=set(),
                suggestions=set(),
                infoboxes=[],
                unresponsive_engines=set(),
                results=test_results,
                number_of_results=3,
                results_length=lambda: len(test_results),
                get_timings=lambda: timings,
                redirect_url=None,
                engine_data={},
            )

        self.setattr4test(Search, 'search', search_mock)

        original_preferences_get_value = Preferences.get_value

        def preferences_get_value(preferences_self, user_setting_name: str):
            if user_setting_name == 'theme':
                return 'simple'
            return original_preferences_get_value(preferences_self, user_setting_name)

        self.setattr4test(Preferences, 'get_value', preferences_get_value)

        self.maxDiff = None  # to see full diffs

    def test_index_empty(self):
        result = self.app.post('/')
        self.assertEqual(result.status_code, 200)
        self.assertIn(
            b'<div class="title"><h1>SearXNG</h1></div>',
            result.data,
        )

    def test_index_html_post(self):
        result = self.app.post('/', data={'q': 'test'})
        self.assertEqual(result.status_code, 308)
        self.assertEqual(result.location, '/search')

    def test_index_html_get(self):
        result = self.app.post('/?q=test')
        self.assertEqual(result.status_code, 308)
        self.assertEqual(result.location, '/search?q=test')

    def test_search_empty_html(self):
        result = self.app.post('/search', data={'q': ''})
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'<div class="title"><h1>SearXNG</h1></div>', result.data)

    def test_search_empty_json(self):
        result = self.app.post('/search', data={'q': '', 'format': 'json'})
        self.assertEqual(result.status_code, 400)

    def test_search_empty_csv(self):
        result = self.app.post('/search', data={'q': '', 'format': 'csv'})
        self.assertEqual(result.status_code, 400)

    def test_search_empty_rss(self):
        result = self.app.post('/search', data={'q': '', 'format': 'rss'})
        self.assertEqual(result.status_code, 400)

    def test_search_html(self):
        result = self.app.post('/search', data={'q': 'test'})

        self.assertIn(
            b'<span class="url_o1"><span class="url_i1">http://second.test.xyz</span></span>',
            result.data,
        )
        self.assertIn(
            b'<p class="content">\n    second <span class="highlight">test</span> ',
            result.data,
        )

    def test_index_json(self):
        result = self.app.post('/', data={'q': 'test', 'format': 'json'})
        self.assertEqual(result.status_code, 308)

    def test_search_json(self):
        result = self.app.post('/search', data={'q': 'test', 'format': 'json'})
        result_dict = json.loads(result.data.decode())

        self.assertEqual('test', result_dict['query'])
        self.assertEqual(len(result_dict['results']), 2)
        self.assertEqual(result_dict['results'][0]['content'], 'first test content')
        self.assertEqual(result_dict['results'][0]['url'], 'http://first.test.xyz')

    def test_index_csv(self):
        result = self.app.post('/', data={'q': 'test', 'format': 'csv'})
        self.assertEqual(result.status_code, 308)

    def test_search_csv(self):
        result = self.app.post('/search', data={'q': 'test', 'format': 'csv'})

        self.assertEqual(
            b'title,url,content,host,engine,score,type\r\n'
            b'First Test,http://first.test.xyz,first test content,first.test.xyz,startpage,,result\r\n'  # noqa
            b'Second Test,http://second.test.xyz,second test content,second.test.xyz,youtube,,result\r\n',  # noqa
            result.data,
        )

    def test_index_rss(self):
        result = self.app.post('/', data={'q': 'test', 'format': 'rss'})
        self.assertEqual(result.status_code, 308)

    def test_search_rss(self):
        result = self.app.post('/search', data={'q': 'test', 'format': 'rss'})

        self.assertIn(b'<description>Search results for "test" - searx</description>', result.data)

        self.assertIn(b'<opensearch:totalResults>3</opensearch:totalResults>', result.data)

        self.assertIn(b'<title>First Test</title>', result.data)

        self.assertIn(b'<link>http://first.test.xyz</link>', result.data)

        self.assertIn(b'<description>first test content</description>', result.data)

    def test_redirect_about(self):
        result = self.app.get('/about')
        self.assertEqual(result.status_code, 302)

    def test_info_page(self):
        result = self.app.get('/info/en/search-syntax')
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'<h1>Search syntax</h1>', result.data)

    def test_health(self):
        result = self.app.get('/healthz')
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'OK', result.data)

    def test_preferences(self):
        result = self.app.get('/preferences')
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'<form id="search_form" method="post" action="/preferences"', result.data)
        self.assertIn(
            b'<input type="checkbox" id="checkbox_general" name="category_general" checked="checked"/>', result.data
        )
        self.assertIn(b'<legend id="pref_ui_locale">Interface language</legend>', result.data)

    def test_browser_locale(self):
        result = self.app.get('/preferences', headers={'Accept-Language': 'zh-tw;q=0.8'})
        self.assertEqual(result.status_code, 200)
        self.assertIn(
            b'<option value="zh-Hant-TW" selected="selected">',
            result.data,
            'Interface locale ignored browser preference.',
        )
        self.assertIn(
            b'<option value="zh-Hant-TW" selected="selected">',
            result.data,
            'Search language ignored browser preference.',
        )

    def test_brower_empty_locale(self):
        result = self.app.get('/preferences', headers={'Accept-Language': ''})
        self.assertEqual(result.status_code, 200)
        self.assertIn(
            b'<option value="en" selected="selected">', result.data, 'Interface locale ignored browser preference.'
        )

    def test_locale_occitan(self):
        result = self.app.get('/preferences?locale=oc')
        self.assertEqual(result.status_code, 200)
        self.assertIn(
            b'<option value="oc" selected="selected">', result.data, 'Interface locale ignored browser preference.'
        )

    def test_stats(self):
        result = self.app.get('/stats')
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'<h1>Engine stats</h1>', result.data)

    def test_robots_txt(self):
        result = self.app.get('/robots.txt')
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'Allow: /', result.data)

    def test_opensearch_xml(self):
        result = self.app.get('/opensearch.xml')
        self.assertEqual(result.status_code, 200)
        self.assertIn(
            b'<Description>SearXNG is a metasearch engine that respects your privacy.</Description>', result.data
        )

    def test_favicon(self):
        result = self.app.get('/favicon.ico')
        self.assertEqual(result.status_code, 200)

    def test_config(self):
        result = self.app.get('/config')
        self.assertEqual(result.status_code, 200)
        json_result = result.get_json()
        self.assertTrue(json_result)
