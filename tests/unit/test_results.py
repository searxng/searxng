# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from searx.results import ResultContainer
import searx.search
from tests import SearxTestCase


def make_test_engine_dict(**kwargs) -> dict:
    test_engine = {
        # fmt: off
        'name': None,
        'engine': None,
        'categories': 'general',
        'shortcut': 'dummy',
        'timeout': 3.0,
        'tokens': [],
        # fmt: on
    }

    test_engine.update(**kwargs)
    return test_engine


def fake_result(url='https://aa.bb/cc?dd=ee#ff', title='aaa', content='bbb', engine='wikipedia', **kwargs):
    result = {
        # fmt: off
        'url': url,
        'title': title,
        'content': content,
        'engine': engine,
        # fmt: on
    }
    result.update(kwargs)
    return result


class ResultContainerTestCase(SearxTestCase):  # pylint: disable=missing-class-docstring

    def setUp(self) -> None:
        stract_engine = make_test_engine_dict(name="stract", engine="stract", shortcut="stra")
        duckduckgo_engine = make_test_engine_dict(name="duckduckgo", engine="duckduckgo", shortcut="ddg")
        mojeek_engine = make_test_engine_dict(name="mojeek", engine="mojeek", shortcut="mjk")
        searx.search.initialize([stract_engine, duckduckgo_engine, mojeek_engine])
        self.container = ResultContainer()

    def tearDown(self):
        searx.search.load_engines([])

    def test_empty(self):
        self.assertEqual(self.container.get_ordered_results(), [])

    def test_one_result(self):
        self.container.extend('wikipedia', [fake_result()])

        self.assertEqual(self.container.results_length(), 1)

    def test_one_suggestion(self):
        self.container.extend('wikipedia', [fake_result(suggestion=True)])

        self.assertEqual(len(self.container.suggestions), 1)
        self.assertEqual(self.container.results_length(), 0)

    def test_result_merge(self):
        self.container.extend('wikipedia', [fake_result()])
        self.container.extend('wikidata', [fake_result(), fake_result(url='https://example.com/')])

        self.assertEqual(self.container.results_length(), 2)

    def test_result_merge_by_title(self):
        self.container.extend('stract', [fake_result(engine='stract', title='short title')])
        self.container.extend('duckduckgo', [fake_result(engine='duckduckgo', title='normal title')])
        self.container.extend('mojeek', [fake_result(engine='mojeek', title='this long long title')])

        self.assertEqual(self.container.get_ordered_results()[0].get('title', ''), 'this long long title')
