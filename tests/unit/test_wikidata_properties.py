# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name

import json
from unittest.mock import patch

from searx import wikidata_properties
from searx.data import data_dir
from searx.wikidata_properties import WDImageAttribute, get_attributes
from tests import SearxTestCase


class TestWikidataProperties(SearxTestCase):

    def test_image_attributes_have_labels(self):
        with open(data_dir / "wikidata_properties.json", encoding="utf-8") as f:
            props = json.load(f)

        image_attrs = [attr for attr in get_attributes("en") if isinstance(attr, WDImageAttribute)]
        self.assertTrue(image_attrs)
        for attr in image_attrs:
            self.assertIn(attr.name, props, f"missing label for image property {attr.name}")
            self.assertIn("en", props[attr.name])

    def test_fetch_properties_requests_image_labels(self):
        captured = {}

        def fake_query(query, **kwargs):  # pylint: disable=unused-argument
            captured["query"] = query
            return {"results": {"bindings": []}}

        with (
            patch.object(wikidata_properties, "_WIKIDATA_PROPERTIES_OVERRIDE", {}),
            patch.object(wikidata_properties, "send_wikidata_query", side_effect=fake_query),
        ):
            wikidata_properties.fetch_properties({})

        self.assertIn("wd:P154", captured["query"])
