# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

import json
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import mock

from searx.engines import eporner
from tests import SearxTestCase


class TestEpornerEngine(SearxTestCase):  # pylint: disable=missing-class-docstring

    def test_categories(self):
        # the engine belongs to the dedicated "adult" tab, not to "videos"
        self.assertEqual(eporner.categories, ["adult"])

    def test_request(self):
        params = eporner.request("test query", {"pageno": 2, "searxng_locale": "en"})

        query = parse_qs(urlparse(params["url"]).query)
        self.assertEqual(query["query"][0], "test query")
        self.assertEqual(query["page"][0], "2")
        self.assertEqual(query["format"][0], "json")
        self.assertEqual(query["thumbsize"][0], "big")
        self.assertIn("https://www.eporner.com/api/v2/video/search/", params["url"])

    def test_response(self):
        sample = json.dumps(
            {
                "count": 2,
                "page": 1,
                "total_count": 100,
                "total_pages": 5,
                "videos": [
                    {
                        "id": "IsabYDAiqXa",
                        "title": "Sample Video One",
                        "keywords": "tag1, tag2, <b>tag3</b>",
                        "views": 260221,
                        "rate": "4.13",
                        "url": "https://www.eporner.com/hd-porn/IsabYDAiqXa/sample-video-one/",
                        "added": "2019-11-21 11:42:47",
                        "length_sec": 2539,
                        "length_min": "42:19",
                        "embed": "https://www.eporner.com/embed/IsabYDAiqXa/",
                        "default_thumb": {
                            "size": "big",
                            "width": 640,
                            "height": 360,
                            "src": "https://static.eporner.com/thumbs/5_360.jpg",
                        },
                    },
                    {
                        "id": "sTlL3Cc3Dps",
                        "title": "Sample Video Two",
                        "keywords": None,
                        "views": 244545,
                        "rate": "3.78",
                        "url": "https://www.eporner.com/hd-porn/sTlL3Cc3Dps/sample-video-two/",
                        "added": "1970-01-01 01:00:00",
                        "length_sec": 201,
                        "length_min": "3:21",
                        "embed": "https://www.eporner.com/embed/sTlL3Cc3Dps/",
                        "default_thumb": {"src": "https://static.eporner.com/thumbs/14_360.jpg"},
                    },
                ],
            }
        )

        resp = mock.Mock(text=sample)
        resp.json.return_value = json.loads(sample)
        results = eporner.response(resp)

        self.assertEqual(len(results), 2)

        first = results[0]
        self.assertEqual(first["url"], "https://www.eporner.com/hd-porn/IsabYDAiqXa/sample-video-one/")
        self.assertEqual(first["title"], "Sample Video One")
        self.assertEqual(first["content"], "tag1, tag2, tag3")  # HTML tags stripped
        self.assertEqual(first["thumbnail"], "https://static.eporner.com/thumbs/5_360.jpg")
        self.assertEqual(first["iframe_src"], "https://www.eporner.com/embed/IsabYDAiqXa/")
        self.assertEqual(first["length"], "42:19")
        self.assertEqual(first["views"], 260221)
        self.assertEqual(
            first["publishedDate"], datetime(2019, 11, 21, 11, 42, 47, tzinfo=timezone.utc)
        )

        # epoch dates reported by the API count as "no date"
        second = results[1]
        self.assertIsNone(second["publishedDate"])
        self.assertEqual(second["content"], "")

    def test_response_no_videos(self):
        resp = mock.Mock(text=json.dumps({"count": 0, "videos": []}))
        resp.json.return_value = {"count": 0, "videos": []}
        results = eporner.response(resp)
        self.assertEqual(results, [])
