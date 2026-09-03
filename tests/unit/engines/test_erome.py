# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from urllib.parse import parse_qs, urlparse

import mock

from searx.engines import erome
from tests import SearxTestCase

HTML = """
<html><body>
<div id="albums">
  <div class="album">
    <a href="/a/NBkd0ih0">
      <img class="lazyload" data-src="https://s77.erome.com/7453/NBkd0ih0/thumbs/i5OwkmJB.jpg?v=1772176993">
      <img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=">
      1841,2K
    </a>
    <a href="/a/NBkd0ih0">Bonnie Blue Album Title</a>
  </div>
  <div class="album">
    <a href="https://www.erome.com/a/4AsbLGVl">
      <img src="https://s44.erome.com/4758/4AsbLGVl/thumbs/uyczxdh8.jpeg?v=1770187564">
      11131K
    </a>
    <a href="https://www.erome.com/a/4AsbLGVl">Second Album</a>
  </div>
  <div class="album">
    <a href="/a/small3"><img src="https://s1.erome.com/x/thumbs/small3.jpg">3</a>
    <a href="/a/small3">Three Views Album</a>
  </div>
  <div class="album">
    <a href="/a/NoThumb">no preview image here</a>
    <a href="/a/NoThumb">Skipped Album</a>
  </div>
</div>
</body></html>
"""


class TestEromeEngine(SearxTestCase):  # pylint: disable=missing-class-docstring

    def test_categories(self):
        # the engine belongs to the dedicated "adult" tab, not to "videos"
        self.assertEqual(erome.categories, ["adult"])

    def test_request(self):
        params = erome.request("test query", {"pageno": 1, "searxng_locale": "en"})
        query = parse_qs(urlparse(params["url"]).query)
        self.assertEqual(query["q"][0], "test query")
        self.assertNotIn("page", query)
        self.assertIn("https://www.erome.com/search", params["url"])

        params = erome.request("test query", {"pageno": 2, "searxng_locale": "en"})
        query = parse_qs(urlparse(params["url"]).query)
        self.assertEqual(query["page"][0], "2")

    def test_response(self):
        resp = mock.Mock(text=HTML)
        results = erome.response(resp)

        # the album without preview image is skipped, no duplicates
        self.assertEqual(len(results), 3)

        first = results[0]
        self.assertEqual(first["url"], "https://www.erome.com/a/NBkd0ih0")
        self.assertEqual(first["title"], "Bonnie Blue Album Title")
        # data-src (lazyload) wins over the data: URI placeholder
        self.assertEqual(first["thumbnail"], "https://s77.erome.com/7453/NBkd0ih0/thumbs/i5OwkmJB.jpg?v=1772176993")
        self.assertEqual(first["views"], 1841200)

        second = results[1]
        self.assertEqual(second["url"], "https://www.erome.com/a/4AsbLGVl")
        self.assertEqual(second["views"], 11131000)

        third = results[2]
        self.assertEqual(third["views"], 3)

    def test_response_no_results(self):
        resp = mock.Mock(text="<html><body><p>nothing here</p></body></html>")
        results = erome.response(resp)
        self.assertEqual(results, [])
