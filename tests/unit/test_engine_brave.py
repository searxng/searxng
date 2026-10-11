# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,line-too-long

import json

from parameterized import parameterized

from searx.engines import brave
from tests import SearxTestCase


class BraveEngineTests(SearxTestCase):
    '''Unit tests specific to the Brave engine'''

    # extract_iife_object
    @parameterized.expand(
        [
            (
                """(function (a, b, c){ return {"a": a, "b": b, "c": c };})("first", 2, {"third": 3})""",  # basic shape, numeric, nested object
                {"a": "first", "b": 2, "c": {"third": 3}},
            ),
            (
                '(function ($,aa,a,a1){return {"first": $, "second": true, "third": [aa,a,a1]};})("actual","x","y","z")',  # non-alpha param, literal, and array
                {"first": "actual", "second": True, "third": ["x", "y", "z"]},
            ),
        ]
    )
    def test_javascript_iife_parser(self, js_code, expected_output):
        iife_match = brave.IIFE_RE.match(js_code)
        self.assertIsNotNone(iife_match)

        iife_object, _ = brave.extract_iife_object(js_code, iife_match)  # pyright: ignore[reportArgumentType]
        parsed = json.loads(iife_object)
        self.assertEqual(parsed, expected_output)
