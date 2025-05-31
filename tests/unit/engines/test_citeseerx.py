# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name,no-self-use

import unittest
from collections import defaultdict
from unittest import mock

from searx.engines import citeseerx # Corrected import
from searx.testing import SearxTestCase


class TestCiteseerx(SearxTestCase): # Corrected class name

    def test_metadata(self):
        self.assertIn('website', citeseerx.about)
        self.assertIn('categories', citeseerx)
        self.assertGreater(len(citeseerx.categories), 0)
        self.assertTrue(any(cat in citeseerx.categories for cat in ['science', 'computer science']))
        self.assertTrue(citeseerx.paging)

    def test_request(self):
        query = 'test_query'
        params_dict = defaultdict(dict)
        params_dict['pageno'] = 2
        request_params = citeseerx.request(query, params_dict)

        expected_offset = (params_dict['pageno'] - 1) * citeseerx.number_of_results
        self.assertIn('url', request_params)
        self.assertIn(query, request_params['url'])
        self.assertIn(f"q={query}", request_params['url'])
        self.assertIn(f"start={expected_offset}", request_params['url']) # 'start' is used in base_url
        self.assertIn(f"rpp={citeseerx.number_of_results}", request_params['url']) # 'rpp' is used
        self.assertIn("format=xml", request_params['url'])

    def test_response_empty(self):
        response_mock = mock.Mock(content=b'', status_code=200)
        results = citeseerx.response(response_mock)
        self.assertEqual(results, [])

        response_mock_malformed = mock.Mock(content=b'<malformed>', status_code=200)
        results_malformed = citeseerx.response(response_mock_malformed)
        self.assertEqual(results_malformed, [])

    def test_response_parsing(self):
        # This mock XML is based on the highly speculative XPaths in citeseerx.py
        # It does not use namespaces for simplicity.
        mock_xml_content = b"""
        <results>
            <result>
                <doc>
                    <title>Test CiteSeerX Paper 1</title>
                    <url>http://citeseerx.example.com/viewdoc/summary/doi/10.1.1.test1</url>
                    <abstract>Abstract for paper one.</abstract>
                    <authors><author>Author X</author><author>Author Y</author></authors>
                    <doi>10.1.1.test1</doi>
                    <download href="http://citeseerx.example.com/download/10.1.1.test1.pdf">PDF Link Text</download>
                    <year>2021</year>
                    <venue>Conference of Testing</venue>
                    <keywords><keyword>kw1</keyword><keyword>kw2</keyword></keywords>
                    <citations>123</citations>
                </doc>
            </result>
            <result>
                <doc>
                    <title>Second Test Paper</title>
                    <url>http://citeseerx.example.com/viewdoc/summary/doi/10.1.1.test2</url>
                    <abstract>Summary of the second one.</abstract>
                    <authors><author>Author Z</author></authors>
                    <doi>10.1.1.test2</doi>
                    <year>2020</year>
                    <citations>0</citations>
                </doc>
            </result>
        </results>
        """
        response_mock = mock.Mock(content=mock_xml_content, status_code=200)
        results = citeseerx.response(response_mock)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)

        # Test first result
        res1 = results[0]
        self.assertEqual(res1['title'], 'Test CiteSeerX Paper 1')
        self.assertEqual(res1['url'], 'http://citeseerx.example.com/viewdoc/summary/doi/10.1.1.test1')
        self.assertEqual(res1['content'], 'Abstract for paper one.')
        self.assertEqual(res1['authors'], ['Author X', 'Author Y'])
        self.assertEqual(res1['doi'], '10.1.1.test1')
        # The PDF URL extraction was: pdf_element.attrib.get('href', pdf_element.text)
        self.assertEqual(res1['pdf_url'], 'http://citeseerx.example.com/download/10.1.1.test1.pdf')
        self.assertEqual(res1['venue'], 'Conference of Testing') # 'venue' is used for journal
        self.assertEqual(res1['tags'], ['kw1', 'kw2'])
        self.assertEqual(res1['citations'], 123)
        self.assertIsNotNone(res1['publishedDate'])
        if res1['publishedDate']:
            self.assertEqual(res1['publishedDate'].year, 2021)
            self.assertEqual(res1['publishedDate'].month, 1) # Defaults to Jan 1st

        # Test second result (no PDF, no keywords, 0 citations)
        res2 = results[1]
        self.assertEqual(res2['title'], 'Second Test Paper')
        self.assertIsNone(res2['pdf_url'])
        self.assertEqual(res2['tags'], [])
        self.assertEqual(res2['citations'], 0)
        self.assertIsNotNone(res2['publishedDate'])
        if res2['publishedDate']:
            self.assertEqual(res2['publishedDate'].year, 2020)

    def test_response_with_problematic_year(self):
        mock_xml_content_bad_date = b"""
        <results><result><doc>
            <title>Year Test</title>
            <year>NotAYear</year>
        </doc></result></results>
        """
        response_mock = mock.Mock(content=mock_xml_content_bad_date, status_code=200)
        results = citeseerx.response(response_mock)
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0]['publishedDate'])

if __name__ == '__main__':
    unittest.main()
