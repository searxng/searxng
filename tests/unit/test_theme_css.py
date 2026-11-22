# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name

import pathlib

from tests import SearxTestCase

CSS_DIR = pathlib.Path(__file__).parents[2] / "searx" / "static" / "themes" / "simple"


class TestThemeCss(SearxTestCase):

    def test_rtl_query_keeps_auto_direction(self):
        # #q must keep dir="auto" so a leading bang stays at the start (#2699)
        css = (CSS_DIR / "sxng-rtl.min.css").read_text(encoding="utf-8")
        self.assertNotIn("#q,#sidebar .infobox dt bdi{direction:rtl}", css)
        self.assertIn("#sidebar .infobox dt bdi{direction:rtl}", css)

    def test_centered_answers_aligned_with_results(self):
        # the answer box must get the same offset as the result list (#4832)
        css = (CSS_DIR / "sxng-ltr.min.css").read_text(encoding="utf-8")
        self.assertIn("#main_results #answers{margin-left:3rem}", css)
