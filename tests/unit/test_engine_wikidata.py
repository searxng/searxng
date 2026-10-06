# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring

from unittest.mock import patch

from searx.engines import wikidata
from searx.wikidata_properties import get_attributes
from tests import SearxTestCase


class WikidataGetResultsTests(SearxTestCase):

    ITEM = "http://www.wikidata.org/entity/Q1"

    def test_no_desc_list(self):
        # an entity without "itemDescription" must not leak a list into "content"
        attribute_result = {"item": self.ITEM, "itemLabel": "Label"}
        with patch.object(wikidata, "display_type", ["list"]):
            results = wikidata.get_results(attribute_result, get_attributes("en"), "en")
        self.assertEqual(results, [{"url": self.ITEM, "title": "Label", "content": ""}])

    def test_no_desc_infobox(self):
        attribute_result = {"item": self.ITEM, "itemLabel": "Label"}
        with patch.object(wikidata, "display_type", ["infobox"]):
            results = wikidata.get_results(attribute_result, get_attributes("en"), "en")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], "")
