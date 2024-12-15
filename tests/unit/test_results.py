# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name


from searx.result_types import LegacyResult
from searx.results import ResultContainer
from tests import SearxTestCase


class ResultContainerTestCase(SearxTestCase):
    # pylint: disable=use-dict-literal

    TEST_SETTINGS = "test_result_container.yml"

    def test_empty(self):
        container = ResultContainer()
        self.assertEqual(container.get_ordered_results(), [])

    def test_one_result(self):
        result = dict(url="https://example.org", title="title ..", content="Lorem ..")

        container = ResultContainer()
        container.extend("google", [result])
        container.close()

        self.assertEqual(container.results_length(), 1)
        self.assertIn(LegacyResult(result), container.get_ordered_results())

    def test_one_suggestion(self):
        result = dict(suggestion="lorem ipsum ..")

        container = ResultContainer()
        container.extend("duckduckgo", [result])
        container.close()

        self.assertEqual(container.results_length(), 0)
        self.assertEqual(len(container.suggestions), 1)
        self.assertIn(result["suggestion"], container.suggestions)

    def test_merge_url_result(self):
        # from the merge of eng1 and eng2 we expect this result
        result = LegacyResult(
            url="https://example.org", title="very long title, lorem ipsum", content="Lorem ipsum dolor sit amet .."
        )
        eng1 = dict(url=result.url, title="short title", content=result.content, engine="google")
        eng2 = dict(url="http://example.org", title=result.title, content="lorem ipsum", engine="duckduckgo")

        container = ResultContainer()
        container.extend(None, [eng1, eng2])
        container.close()

        result_list = container.get_ordered_results()
        self.assertEqual(container.results_length(), 1)
        self.assertIn(result, result_list)
        self.assertEqual(result_list[0].title, result.title)
        self.assertEqual(result_list[0].content, result.content)
