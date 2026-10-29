# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name

from unittest.mock import Mock

from searx.engines import openalex
from tests import SearxTestCase


class OpenAlexEngineTests(SearxTestCase):

    def setUp(self):
        super().setUp()
        self.orig_has_api_key = hasattr(openalex, "api_key")
        self.orig_api_key = getattr(openalex, "api_key", "")
        self.orig_mailto = getattr(openalex, "mailto", "")
        if self.orig_has_api_key:
            openalex.api_key = ""
        openalex.mailto = ""

    def tearDown(self):
        if self.orig_has_api_key:
            openalex.api_key = self.orig_api_key
        elif hasattr(openalex, "api_key"):
            delattr(openalex, "api_key")
        openalex.mailto = self.orig_mailto
        super().tearDown()

    def test_module_attributes(self):
        self.assertTrue(self.orig_has_api_key)
        self.assertEqual(self.orig_api_key, "")
        self.assertTrue(hasattr(openalex, "mailto"))
        self.assertEqual(self.orig_mailto, "")

    def test_request_unauthenticated(self):
        for empty_key in ("", None, "   "):
            with self.subTest(api_key=empty_key):
                openalex.api_key = empty_key  # type: ignore[assignment]
                openalex.mailto = ""
                params = {"pageno": 1, "headers": {}}
                openalex.request("quantum", params)
                self.assertIn("search=quantum", params["url"])
                self.assertIn("per-page=10", params["url"])
                self.assertNotIn("Authorization", params.get("headers", {}))
                self.assertNotIn("mailto", params["url"])
                self.assertNotIn("api_key", params["url"])

    def test_request_authenticated(self):
        openalex.api_key = "test_key_123"
        params = {"pageno": 1, "headers": {"User-Agent": "test-agent", "Accept": "application/json"}}
        openalex.request("quantum", params)
        self.assertIn("headers", params)
        self.assertEqual(params["headers"].get("Authorization"), "Bearer test_key_123")
        self.assertEqual(params["headers"].get("User-Agent"), "test-agent")
        self.assertEqual(params["headers"].get("Accept"), "application/json")
        self.assertNotIn("api_key", params["url"])
        self.assertNotIn("mailto", params["url"])

    def test_request_api_key_normalization(self):
        cases = [
            ("  Bearer my_secret_token  ", "Bearer my_secret_token"),
            ("bearer: xyz", "Bearer xyz"),
            ("  my_secret_token  ", "Bearer my_secret_token"),
            ("BEARER my_secret_token", "Bearer my_secret_token"),
            ("Bearer: my_secret_token", "Bearer my_secret_token"),
        ]
        for raw_key, expected_header in cases:
            with self.subTest(raw_key=raw_key):
                openalex.api_key = raw_key
                params = {"pageno": 1, "headers": {}}
                openalex.request("quantum", params)
                self.assertIn("headers", params)
                self.assertEqual(params["headers"].get("Authorization"), expected_header)

    def test_request_missing_headers_key(self):
        openalex.api_key = "test_key_123"
        params = {"pageno": 1}
        openalex.request("quantum", params)
        self.assertIn("headers", params)
        self.assertEqual(params["headers"].get("Authorization"), "Bearer test_key_123")

    def test_request_deprecated_mailto_ignored(self):
        openalex.mailto = "[email protected]"
        params = {"pageno": 1, "headers": {}}
        openalex.request("test", params)
        self.assertNotIn("mailto", params["url"])

    def test_response_parsing(self):
        fake_resp = Mock()
        fake_resp.json.return_value = {
            "results": [
                {
                    "id": "https://openalex.org/W123456",
                    "title": "Quantum Supremacy",
                    "publication_date": "2023-01-15",
                    "doi": "https://doi.org/10.1234/test.doi",
                    "abstract_inverted_index": {
                        "Quantum": [0],
                        "computing": [1],
                        "advancement.": [2],
                    },
                    "authorships": [
                        {"author": {"display_name": "Alice Smith"}},
                        {"author": {"display_name": "Bob Jones"}},
                    ],
                    "host_venue": {
                        "display_name": "Nature Physics",
                        "publisher": "Springer Nature",
                    },
                    "biblio": {"volume": "19", "issue": "1", "first_page": "10", "last_page": "20"},
                    "primary_location": {
                        "landing_page_url": "https://doi.org/10.1234/test.doi",
                        "pdf_url": "https://example.com/paper.pdf",
                    },
                    "concepts": [{"display_name": "Physics"}],
                    "cited_by_count": 42,
                    "type": "article",
                }
            ]
        }
        results = openalex.response(fake_resp)
        self.assertEqual(len(results), 1)
        paper = results[0]
        self.assertEqual(paper["title"], "Quantum Supremacy")
        self.assertEqual(paper["doi"], "10.1234/test.doi")
        self.assertEqual(paper["content"], "Quantum computing advancement.")
        self.assertEqual(paper["authors"], ["Alice Smith", "Bob Jones"])
        self.assertEqual(paper["journal"], "Nature Physics")
        self.assertEqual(paper["publisher"], "Springer Nature")
        self.assertEqual(paper["url"], "https://doi.org/10.1234/test.doi")
