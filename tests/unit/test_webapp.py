# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

import json
import babel
from mock import Mock

import searx.webapp
import searx.search
import searx.search.processors
from searx.result_types._base import MainResult

from searx.results import Timing
from searx.preferences import Preferences
from tests import SearxTestCase


class ViewsTestCase(SearxTestCase):  # pylint: disable=too-many-public-methods

    def setUp(self):
        super().setUp()

        # skip init function (no external HTTP request)
        def dummy(*args, **kwargs):  # pylint: disable=unused-argument
            pass

        self.setattr4test(searx.search.processors.PROCESSORS, 'init', dummy)

        # set some defaults
        test_results = [
            MainResult(
                title="First Test",
                url="http://first.test.xyz",
                content="first test content",
                engine="startpage",
            ),
            MainResult(
                title="Second Test",
                url="http://second.test.xyz",
                content="second test content",
                engine="youtube",
            ),
        ]
        for r in test_results:
            r.normalize_result_fields()
        timings = [
            Timing(engine='startpage', total=0.8, load=0.7),
            Timing(engine='youtube', total=0.9, load=0.6),
        ]

        def search_mock(search_self, *args):  # pylint: disable=unused-argument
            search_self.result_container = Mock(
                get_ordered_results=lambda: test_results,
                answers={},
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
            search_self.search_query.locale = babel.Locale.parse("en-US", sep='-')

        self.setattr4test(searx.search.Search, 'search', search_mock)

        original_preferences_get_value = Preferences.get_value

        def preferences_get_value(preferences_self, user_setting_name: str):
            if user_setting_name == 'theme':
                return 'simple'
            return original_preferences_get_value(preferences_self, user_setting_name)

        self.setattr4test(Preferences, 'get_value', preferences_get_value)

        # to see full diffs
        self.maxDiff = None  # pylint: disable=invalid-name

    def test_index_empty(self):
        result = self.client.post('/')
        self.assertEqual(result.status_code, 200)
        self.assertIn(
            b'<div class="title"><h1>SearXNG</h1></div>',
            result.data,
        )

    def test_index_html_post(self):
        result = self.client.post('/', data={'q': 'test'})
        self.assertEqual(result.status_code, 308)
        self.assertEqual(result.location, '/search')

    def test_index_html_get(self):
        result = self.client.post('/?q=test')
        self.assertEqual(result.status_code, 308)
        self.assertEqual(result.location, '/search?q=test')

    def test_search_empty_html(self):
        result = self.client.post('/search', data={'q': ''})
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'<div class="title"><h1>SearXNG</h1></div>', result.data)

    def test_search_empty_json(self):
        result = self.client.post('/search', data={'q': '', 'format': 'json'})
        self.assertEqual(result.status_code, 400)

    def test_search_empty_csv(self):
        result = self.client.post('/search', data={'q': '', 'format': 'csv'})
        self.assertEqual(result.status_code, 400)

    def test_search_empty_rss(self):
        result = self.client.post('/search', data={'q': '', 'format': 'rss'})
        self.assertEqual(result.status_code, 400)

    def test_search_html(self):
        result = self.client.post('/search', data={'q': 'test'})

        self.assertIn(
            b'<span class="url_o1"><span class="url_i1">http://second.test.xyz</span></span>',
            result.data,
        )
        self.assertIn(
            b'<p class="content">\n    second <span class="highlight">test</span> ',
            result.data,
        )

    def test_index_json(self):
        result = self.client.post('/', data={'q': 'test', 'format': 'json'})
        self.assertEqual(result.status_code, 308)

    def test_search_json(self):
        result = self.client.post('/search', data={'q': 'test', 'format': 'json'})
        result_dict = json.loads(result.data.decode())

        self.assertEqual('test', result_dict['query'])
        self.assertEqual(len(result_dict['results']), 2)
        self.assertEqual(result_dict['results'][0]['content'], 'first test content')
        self.assertEqual(result_dict['results'][0]['url'], 'http://first.test.xyz')

    def test_index_csv(self):
        result = self.client.post('/', data={'q': 'test', 'format': 'csv'})
        self.assertEqual(result.status_code, 308)

    def test_search_csv(self):
        result = self.client.post('/search', data={'q': 'test', 'format': 'csv'})
        self.assertEqual(
            b'title,url,content,host,engine,score,type\r\n'
            + b'First Test,http://first.test.xyz,first test content,first.test.xyz,startpage,0,result\r\n'
            + b'Second Test,http://second.test.xyz,second test content,second.test.xyz,youtube,0,result\r\n',
            result.data,
        )

    def test_index_rss(self):
        result = self.client.post('/', data={'q': 'test', 'format': 'rss'})
        self.assertEqual(result.status_code, 308)

    def test_search_rss(self):
        result = self.client.post('/search', data={'q': 'test', 'format': 'rss'})

        self.assertIn(b'<description>Search results for "test" - SearXNG</description>', result.data)

        self.assertIn(b'<opensearch:totalResults>3</opensearch:totalResults>', result.data)

        self.assertIn(b'<title>First Test</title>', result.data)

        self.assertIn(b'<link>http://first.test.xyz</link>', result.data)

        self.assertIn(b'<description>first test content</description>', result.data)

    def test_redirect_about(self):
        result = self.client.get('/about')
        self.assertEqual(result.status_code, 302)

    def test_info_page(self):
        result = self.client.get('/info/en/search-syntax')
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'<h1>Search syntax</h1>', result.data)

    def test_health(self):
        result = self.client.get('/healthz')
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'OK', result.data)

    def test_preferences(self):
        result = self.client.get('/preferences')
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'<form id="search_form" method="post" action="/preferences"', result.data)
        self.assertIn(b'<div id="categories_container">', result.data)
        self.assertIn(b'<legend id="pref_ui_locale">Interface language</legend>', result.data)

    def test_browser_locale(self):
        result = self.client.get('/preferences', headers={'Accept-Language': 'zh-tw;q=0.8'})
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

    def test_browser_empty_locale(self):
        result = self.client.get('/preferences', headers={'Accept-Language': ''})
        self.assertEqual(result.status_code, 200)
        self.assertIn(
            b'<option value="en" selected="selected">', result.data, 'Interface locale ignored browser preference.'
        )

    def test_locale_occitan(self):
        result = self.client.get('/preferences?locale=oc')
        self.assertEqual(result.status_code, 200)
        self.assertIn(
            b'<option value="oc" selected="selected">', result.data, 'Interface locale ignored browser preference.'
        )

    def test_stats(self):
        result = self.client.get('/stats')
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'<h1>Engine stats</h1>', result.data)

    def test_robots_txt(self):
        result = self.client.get('/robots.txt')
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'Allow: /', result.data)

    def test_opensearch_xml(self):
        result = self.client.get('/opensearch.xml')
        self.assertEqual(result.status_code, 200)
        self.assertIn(
            b'<Description>SearXNG is a metasearch engine that respects your privacy.</Description>', result.data
        )

    def test_favicon(self):
        result = self.client.get('/favicon.ico')
        result.close()
        self.assertEqual(result.status_code, 200)

    def test_config(self):
        result = self.client.get('/config')
        self.assertEqual(result.status_code, 200)
        json_result = result.get_json()
        self.assertTrue(json_result)
