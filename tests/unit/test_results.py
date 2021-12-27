# -*- coding: utf-8 -*-

from searx.results import ResultContainer
from tests import SearxTestCase


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


#  TODO
class ResultContainerTestCase(SearxTestCase):
    def test_empty(self):
        c = ResultContainer()
        self.assertEqual(c.get_ordered_results(), [])

    def test_one_result(self):
        c = ResultContainer()
        c.extend('wikipedia', [fake_result()])
        self.assertEqual(c.results_length(), 1)

    def test_one_suggestion(self):
        c = ResultContainer()
        c.extend('wikipedia', [fake_result(suggestion=True)])
        self.assertEqual(len(c.suggestions), 1)
        self.assertEqual(c.results_length(), 0)

    def test_result_merge(self):
        c = ResultContainer()
        c.extend('wikipedia', [fake_result()])
        c.extend('wikidata', [fake_result(), fake_result(url='https://example.com/')])
        self.assertEqual(c.results_length(), 2)
