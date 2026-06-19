# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring

import logging
from unittest.mock import Mock

import searx.engines
from tests import SearxTestCase


class KagiTests(SearxTestCase):

    TEST_SETTINGS = "test_kagi.yml"

    def setUp(self):
        super().setUp()
        self.kagi = searx.engines.engines['kagi']
        self.kagi.logger.setLevel(logging.INFO)

    def tearDown(self):
        searx.search.load_engines([])

    def _response(self, json_data, categ="search"):
        """Build a mocked ``SXNG_Response`` and call ``kagi.response``.

        The kagi engine reads the module-level ``kagi_categ`` global to decide
        which branch of the response parser runs.  The loaded engine object
        (``searx.engines.engines['kagi']``) is the module the parser reads from,
        so the category has to be set on that object, not on the
        ``searx.engines.kagi`` import path.  ``setattr4test`` resets the value
        to its previous state during cleanup, so each test can pick the category
        it exercises without leaking into the next one.
        """
        self.setattr4test(self.kagi, "kagi_categ", categ)
        response = Mock()
        response.json.return_value = json_data
        response.status_code = 200
        return self.kagi.response(response)

    # --- search / news branch ---------------------------------------------

    def test_search_result_with_title_and_snippet(self):
        results = self._response(
            {
                "data": {
                    "search": [
                        {
                            "url": "https://example.com/foo",
                            "title": "Foo &amp; Bar",
                            "snippet": "A &lt;snippet&gt; about foo",
                            "image": {"url": "https://example.com/thumb.png"},
                        }
                    ],
                }
            },
            categ="search",
        )
        self.assertEqual(1, len(results))
        result = results[0]
        self.assertEqual("https://example.com/foo", result.url)
        self.assertEqual("Foo & Bar", result.title)
        self.assertEqual("A <snippet> about foo", result.content)
        self.assertEqual("https://example.com/thumb.png", result.thumbnail)

    def test_search_result_without_snippet(self):
        # Kagi can omit ``snippet`` on some results; the parser must not raise
        # (observed in production as ``KeyError: 'snippet'`` /
        # ``unresponsive_engines: [['kagi', 'parsing error']]``).
        results = self._response(
            {
                "data": {
                    "search": [
                        {
                            "url": "https://example.com/no-snippet",
                            "title": "No snippet here",
                        }
                    ],
                }
            },
            categ="search",
        )
        self.assertEqual(1, len(results))
        self.assertEqual("", results[0].content)

    def test_search_result_without_title(self):
        results = self._response(
            {
                "data": {
                    "search": [
                        {
                            "url": "https://example.com/no-title",
                            "snippet": "only a snippet",
                        }
                    ],
                }
            },
            categ="search",
        )
        self.assertEqual(1, len(results))
        self.assertEqual("", results[0].title)
        self.assertEqual("only a snippet", results[0].content)

    def test_news_result_without_snippet(self):
        # the ``news`` branch shares the search/news code path
        results = self._response(
            {
                "data": {
                    "news": [
                        {
                            "url": "https://example.com/news",
                            "title": "A headline",
                        }
                    ],
                }
            },
            categ="news",
        )
        self.assertEqual(1, len(results))
        self.assertEqual("", results[0].content)

    # --- videos branch ----------------------------------------------------

    def test_videos_result_without_snippet(self):
        results = self._response(
            {
                "data": {
                    "video": [
                        {
                            "url": "https://example.com/video",
                            "title": "A video",
                            "props": {"duration": "3m12s", "creator_name": "alice"},
                        }
                    ],
                }
            },
            categ="videos",
        )
        self.assertEqual(1, len(results))
        result = results[0]
        self.assertEqual("", result["content"])
        self.assertEqual("A video", result["title"])
        self.assertEqual("alice", result["author"])

    def test_videos_result_without_title(self):
        results = self._response(
            {
                "data": {
                    "video": [
                        {
                            "url": "https://example.com/video2",
                            "snippet": "a snippet",
                            "props": {},
                        }
                    ],
                }
            },
            categ="videos",
        )
        self.assertEqual(1, len(results))
        self.assertEqual("", results[0]["title"])

    def test_videos_result_without_props(self):
        # ``props`` is used unguarded at the top of the videos branch; a result
        # that omits it entirely must not raise.
        results = self._response(
            {
                "data": {
                    "video": [
                        {
                            "url": "https://example.com/video3",
                            "title": "A video",
                            "snippet": "a snippet",
                        }
                    ],
                }
            },
            categ="videos",
        )
        self.assertEqual(1, len(results))
        self.assertIsNone(results[0]["length"])
        self.assertIsNone(results[0]["author"])

    # --- images branch ----------------------------------------------------

    def test_images_result_with_image_dims(self):
        results = self._response(
            {
                "data": {
                    "image": [
                        {
                            "url": "https://example.com/img.html",
                            "title": "An image",
                            "image": {
                                "url": "https://example.com/img.png",
                                "width": 1920,
                                "height": 1080,
                            },
                            "props": {
                                "thumbnail": {"url": "https://example.com/thumb.png"},
                            },
                        }
                    ],
                }
            },
            categ="images",
        )
        self.assertEqual(1, len(results))
        result = results[0]
        self.assertEqual("1920x1080", result.resolution)
        self.assertEqual("https://example.com/img.png", result.img_src)
        self.assertEqual("https://example.com/thumb.png", result.thumbnail_src)

    def test_images_result_without_image(self):
        # the original code did ``result['image']['width']`` chained; a result
        # without ``image`` raised ``KeyError: 'image'``.  The fix degrades
        # ``resolution`` to an empty string instead.
        results = self._response(
            {
                "data": {
                    "image": [
                        {
                            "url": "https://example.com/no-dims.html",
                            "title": "No dims",
                        }
                    ],
                }
            },
            categ="images",
        )
        self.assertEqual(1, len(results))
        self.assertEqual("", results[0].resolution)

    def test_images_result_with_image_but_no_dims(self):
        results = self._response(
            {
                "data": {
                    "image": [
                        {
                            "url": "https://example.com/no-dims2.html",
                            "title": "Image without dims",
                            "image": {"url": "https://example.com/img2.png"},
                        }
                    ],
                }
            },
            categ="images",
        )
        self.assertEqual(1, len(results))
        self.assertEqual("", results[0].resolution)
        self.assertEqual("https://example.com/img2.png", results[0].img_src)

    # --- related_search ---------------------------------------------------

    def test_related_search_are_collected(self):
        results = self._response(
            {
                "data": {
                    "search": [
                        {"url": "https://example.com/r", "title": "t", "snippet": "s"},
                    ],
                    "related_search": [{"title": "kagi alternative"}],
                }
            },
            categ="search",
        )
        # one search result + one suggestion
        self.assertEqual(2, len(results))
        self.assertEqual("kagi alternative", results[1]["suggestion"])
