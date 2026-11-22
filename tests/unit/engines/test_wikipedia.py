# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name

from unittest.mock import patch

from searx.engines import wikipedia
from searx.enginelib.traits import EngineTraitsMap
from tests import SearxTestCase


class TestWikipedia(SearxTestCase):

    def setUp(self):
        super().setUp()
        self.traits = EngineTraitsMap.from_data().get("wikipedia")

    def test_en_sg_uses_english(self):
        tag, netloc = wikipedia.get_wiki_params("en-SG", self.traits)
        self.assertEqual(tag, "en")
        self.assertEqual(netloc, "en.wikipedia.org")

    def test_zh_sg_uses_chinese(self):
        tag, netloc = wikipedia.get_wiki_params("zh-SG", self.traits)
        self.assertEqual(tag, "zh")
        self.assertEqual(netloc, "zh.wikipedia.org")

    def test_plain_language(self):
        tag, netloc = wikipedia.get_wiki_params("de", self.traits)
        self.assertEqual(tag, "de")
        self.assertEqual(netloc, "de.wikipedia.org")

    def test_request_capitalizes_only_first_letter(self):
        params = {"searxng_locale": "en", "headers": {}}
        with (
            patch.object(wikipedia, "traits", self.traits, create=True),
            patch.object(wikipedia, "_contact", return_value="test@example.org"),
        ):
            wikipedia.request("mixed raster content", params)
        self.assertIn("Mixed%20raster%20content", params["url"])
