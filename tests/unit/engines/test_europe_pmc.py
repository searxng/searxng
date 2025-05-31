# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name,no-self-use

import unittest
from collections import defaultdict
from unittest import mock

from searx.engines import europe_pmc
from searx.testing import SearxTestCase


class TestEuropePmc(SearxTestCase):

    def test_metadata(self):
        self.assertIn('website', europe_pmc.about)
        self.assertIn('categories', europe_pmc)
        self.assertGreater(len(europe_pmc.categories), 0)
        self.assertIn('science', europe_pmc.categories)
        self.assertTrue(europe_pmc.paging)

    def test_request(self):
        query = 'test_query'
        params_dict = defaultdict(dict)
        params_dict['pageno'] = 1
        request_params = europe_pmc.request(query, params_dict)
        self.assertIn('url', request_params)
        self.assertIn(query, request_params['url'])
        self.assertIn(f"page={params_dict['pageno']}", request_params['url'])
        self.assertIn(f"pageSize={europe_pmc.number_of_results}", request_params['url'])

    def test_response_empty(self):
        # Test with an empty or malformed response
        response_mock = mock.Mock(content=b'', status_code=200)
        results = europe_pmc.response(response_mock)
        self.assertEqual(results, [])

        response_mock_malformed = mock.Mock(content=b'<malformed>', status_code=200)
        results_malformed = europe_pmc.response(response_mock_malformed)
        self.assertEqual(results_malformed, [])

    def test_response_parsing(self):
        # Based on the guessed XPaths in europe_pmc.py
        # Namespace might be an issue if not correctly guessed or used in mock XML.
        # For simplicity, this mock XML does not use namespaces. If the engine's XPaths
        # require namespaces, this test would need adjustment or the XPaths made namespace-agnostic.
        mock_xml_content = b"""
        <responseWrapper>
            <resultList>
                <result>
                    <id>PUB12345</id>
                    <title>Test Paper Title 1</title>
                    <abstractText>This is a summary of the test paper 1.</abstractText>
                    <authorString>Author A, Author B</authorString>
                    <doi>10.1000/testdoi1</doi>
                    <firstPublicationDate>2023-01-15</firstPublicationDate>
                    <journalTitle>Journal of Tests</journalTitle>
                    <keywordList><keyword>cat1</keyword><keyword>cat2</keyword></keywordList>
                    <fullTextUrlList>
                        <fullTextUrl>
                            <url>http://example.com/pdf1.pdf</url>
                            <urlType>pdf</urlType>
                        </fullTextUrl>
                    </fullTextUrlList>
                </result>
                <result>
                    <id>PUB67890</id>
                    <title>Another Test Paper</title>
                    <abstractText>Abstract for second paper.</abstractText>
                    <authorString>Author C</authorString>
                    <doi>10.1000/testdoi2</doi>
                    <firstPublicationDate>2022-11-20</firstPublicationDate>
                    <journalTitle>Annals of Testing</journalTitle>
                    <keywordList><keyword>cat3</keyword></keywordList>
                    <url>https://europepmc.org/articles/PUB67890</url> {/* Direct URL example */}
                </result>
            </resultList>
        </responseWrapper>
        """
        response_mock = mock.Mock(content=mock_xml_content, status_code=200)
        results = europe_pmc.response(response_mock)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)

        # Test first result
        res1 = results[0]
        self.assertEqual(res1['title'], 'Test Paper Title 1')
        self.assertEqual(res1['content'], 'This is a summary of the test paper 1.')
        # The default URL construction is "https://europepmc.org/abstract/MED/{id}"
        self.assertEqual(res1['url'], 'https://europepmc.org/abstract/MED/PUB12345')
        self.assertEqual(res1['doi'], '10.1000/testdoi1')
        self.assertEqual(res1['authors'], ['Author A', 'Author B'])
        self.assertEqual(res1['journal'], 'Journal of Tests')
        self.assertEqual(res1['pdf_url'], 'http://example.com/pdf1.pdf') # Relies on specific xpath for pdf
        self.assertEqual(res1['tags'], ['cat1', 'cat2'])
        self.assertIsNotNone(res1['publishedDate'])
        if res1['publishedDate']: # Guard against None if parsing failed
            self.assertEqual(res1['publishedDate'].year, 2023)
            self.assertEqual(res1['publishedDate'].month, 1)
            self.assertEqual(res1['publishedDate'].day, 15)

        # Test second result (with direct url and no PDF)
        res2 = results[1]
        self.assertEqual(res2['title'], 'Another Test Paper')
        self.assertEqual(res2['url'], 'https://europepmc.org/articles/PUB67890') # Direct URL used
        self.assertIsNone(res2['pdf_url']) # No PDF
        self.assertEqual(res2['tags'], ['cat3'])

    def test_response_with_problematic_date(self):
        mock_xml_content_bad_date = b"""
        <responseWrapper><resultList><result>
            <title>Date Test</title>
            <firstPublicationDate>Invalid Date String</firstPublicationDate>
        </result></resultList></responseWrapper>
        """
        response_mock = mock.Mock(content=mock_xml_content_bad_date, status_code=200)
        results = europe_pmc.response(response_mock)
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0]['publishedDate'])

if __name__ == '__main__':
    unittest.main()
