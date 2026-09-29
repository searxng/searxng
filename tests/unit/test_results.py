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

        self.assertEqual(len(container.get_ordered_results()), 1)

        res = LegacyResult(result)
        res.normalize_result_fields()
        self.assertIn(res, container.get_ordered_results())

    def test_one_suggestion(self):
        result = dict(suggestion="lorem ipsum ..")

        container = ResultContainer()
        container.extend("duckduckgo", [result])
        container.close()

        self.assertEqual(len(container.get_ordered_results()), 0)
        self.assertEqual(len(container.suggestions), 1)
        self.assertIn(result["suggestion"], container.suggestions)

    def test_merge_url_result(self):
        # from the merge of eng1 and eng2 we expect this result
        result = LegacyResult(
            url="https://example.org", title="very long title, lorem ipsum", content="Lorem ipsum dolor sit amet .."
        )
        result.normalize_result_fields()
        eng1 = dict(url=result.url, title="short title", content=result.content, engine="google")
        eng2 = dict(url="http://example.org", title=result.title, content="lorem ipsum", engine="duckduckgo")

        container = ResultContainer()
        container.extend(None, [eng1, eng2])
        container.close()

        result_list = container.get_ordered_results()
        self.assertEqual(len(container.get_ordered_results()), 1)
        self.assertIn(result, result_list)
        self.assertEqual(result_list[0].title, result.title)
        self.assertEqual(result_list[0].content, result.content)


class ResultOrderingTestCase(SearxTestCase):
    # pylint: disable=use-dict-literal,missing-class-docstring

    TEST_SETTINGS = "test_result_order.yml"

    def assert_scores_descending(self, container: ResultContainer, msg: str = ""):
        ordered = container.get_ordered_results()
        scores = [res.score for res in ordered]
        for i in range(1, len(scores)):
            self.assertLessEqual(
                scores[i],
                scores[i - 1],
                f"{msg}score ordering is not descending: {scores}; result {i} has score {scores[i]} "
                f"after result {i - 1} with score {scores[i - 1]}",
            )

    def test_results_ordered_by_score_descending(self):
        """Result ordering must be descending by score.
        """
        container = ResultContainer()

        container.extend(
            "general engine",
            [
                dict(url="https://general1.example.org", title="General 1", content="x", engine="general engine"),
                dict(url="https://general2.example.org", title="General 2", content="x", engine="general engine"),
                dict(url="https://general3.example.org", title="General 3", content="x", engine="general engine"),
                dict(url="https://general4.example.org", title="General 4", content="x", engine="general engine"),
            ],
        )
        container.extend(
            "news engine",
            [dict(url="https://news1.example.org", title="News 1", content="x", engine="news engine")],
        )
        container.close()
        self.assert_scores_descending(container)

    def test_results_ordered_by_score_same_category(self):
        """Same-category results must also be ordered by score.
        """
        container = ResultContainer()

        container.extend(
            "alpha engine",
            [
                dict(url="https://alpha1.example.org", title="Alpha 1", content="x", engine="alpha engine"),
                dict(url="https://alpha2.example.org", title="Alpha 2", content="x", engine="alpha engine"),
            ],
        )
        container.extend(
            "beta engine",
            [
                dict(url="https://beta1.example.org", title="Beta 1", content="x", engine="beta engine"),
                dict(url="https://beta2.example.org", title="Beta 2", content="x", engine="beta engine"),
            ],
        )
        container.extend(
            "alpha engine",
            [dict(url="https://alpha3.example.org", title="Alpha 3", content="x", engine="alpha engine")],
        )
        container.extend(
            "beta engine",
            [dict(url="https://beta3.example.org", title="Beta 3", content="x", engine="beta engine")],
        )
        container.close()
        self.assert_scores_descending(container, "same-category engines: ")


