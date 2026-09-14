# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from json import loads
import mock

from searx.engines import yandex
from tests import SearxTestCase


class TestYandexEngine(SearxTestCase):
    def setUp(self):
        super().setUp()
        self.search_type = yandex.search_type
        yandex.search_type = 'images'

    def tearDown(self):
        yandex.search_type = self.search_type
        super().tearDown()

    def test_extract_json_object_returns_complete_object(self):
        payload = (
            '{"location":"/images/search/test",'
            '"nested":{"value":false,"items":[{"text":"false}}}"}]},'
            '"escaped":"quote: \\\" and slash: \\\\",'
            '"final":false}'
        )

        result = yandex.extract_json_object(
            f'<script>{payload}</script>',
            '{"location":"/images/search/',
        )

        self.assertEqual(result, payload)
        self.assertEqual(loads(result)['nested']['items'][0]['text'], 'false}}}')
        self.assertEqual(loads(result)['escaped'], 'quote: " and slash: \\')

    def test_extract_json_object_uses_matching_braces(self):
        payload = (
            '{"location":"/images/search/test",'
            '"first":{"second":{"third":true}},'
            '"list":[{"a":1},{"b":2}],'
            '"final":false}'
        )

        result = yandex.extract_json_object(
            f'prefix {payload} suffix {"location":"/images/search/"}',
            '{"location":"/images/search/',
        )

        self.assertEqual(loads(result), loads(payload))

    def test_extract_json_object_ignores_braces_inside_strings(self):
        payload = (
            '{"location":"/images/search/test",'
            '"text":"opening { brace and closing } brace",'
            '"marker":"false}}}",'
            '"ok":true}'
        )

        result = yandex.extract_json_object(
            payload,
            '{"location":"/images/search/',
        )

        self.assertEqual(result, payload)

    def test_extract_json_object_handles_escaped_quotes(self):
        payload = (
            '{"location":"/images/search/test",'
            '"text":"quote \\\" and brace }",'
            '"ok":true}'
        )

        result = yandex.extract_json_object(
            payload,
            '{"location":"/images/search/',
        )

        self.assertEqual(loads(result), loads(payload))

    def test_extract_json_object_rejects_missing_marker(self):
        with self.assertRaises(ValueError):
            yandex.extract_json_object(
                '{"location":"/images/other/test"}',
                '{"location":"/images/search/',
            )

    def test_extract_json_object_rejects_incomplete_object(self):
        with self.assertRaises(ValueError):
            yandex.extract_json_object(
                '{"location":"/images/search/test","nested":{"ok":true}',
                '{"location":"/images/search/',
            )

    def test_response_parses_complete_image_payload(self):
        payload = {
            "location": "/images/search/test",
            "initialState": {
                "serpList": {
                    "items": {
                        "entities": {
                            "1": {
                                "snippet": {
                                    "title": "A test image",
                                    "url": "https://example.org/source",
                                },
                                "viewerData": {
                                    "thumb": {
                                        "url": "https://example.org/thumb.jpg",
                                        "w": 100,
                                        "h": 100,
                                    },
                                    "dups": [
                                        {
                                            "url": "https://example.org/large.jpg",
                                            "w": 640,
                                            "h": 480,
                                            "fileSizeInBytes": 2048,
                                        }
                                    ],
                                    "preview": [
                                        {
                                            "url": "https://example.org/preview.jpg",
                                            "w": 320,
                                            "h": 240,
                                            "fileSizeInBytes": 1024,
                                        }
                                    ],
                                },
                                "image": "https://example.org/thumb-small.jpg",
                            }
                        }
                    }
                }
            },
            "extra": {
                "description": "contains false}}} and must not stop parsing"
            },
            "done": False,
        }

        import json

        response = mock.Mock(
            text=f'<html><body><script>{json.dumps(payload)}</script></body></html>',
            status_code=200,
            headers={},
        )

        results = yandex.response(response)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'A test image')
        self.assertEqual(results[0]['url'], 'https://example.org/source')
        self.assertEqual(results[0]['img_src'], 'https://example.org/large.jpg')
        self.assertEqual(results[0]['thumbnail_src'], 'https://example.org/thumb-small.jpg')
        self.assertEqual(results[0]['resolution'], '640 x 480')
        self.assertEqual(results[0]['filesize'], '2.0 KB')

    def test_response_returns_empty_for_unknown_search_type(self):
        yandex.search_type = 'videos'

        response = mock.Mock(text='<html></html>', status_code=200, headers={})

        self.assertEqual(yandex.response(response), [])

    def test_response_keeps_web_path_unchanged(self):
        yandex.search_type = 'web'

        body = """
        <ul>
            <li class="serp-item">
                <a class="b-serp-item__title-link" href="https://example.org">Title</a>
            </li>
        </ul>
        """

        response = mock.Mock(text=body, status_code=200, headers={})
        results = yandex.response(response)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['url'], 'https://example.org')
        self.assertEqual(results[0]['title'], 'Title')
        self.assertEqual(results[0]['content'], '')
