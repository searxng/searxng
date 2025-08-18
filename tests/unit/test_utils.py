# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

import random
import string
import lxml.etree
from lxml import html
from parameterized.parameterized import parameterized

from searx.exceptions import SearxXPathSyntaxException, SearxEngineXPathException
from searx import utils
from tests import SearxTestCase


def random_string(length, choices=string.ascii_letters):
    return ''.join(random.choice(choices) for _ in range(length))


class TestUtils(SearxTestCase):

    def test_gen_useragent(self):
        self.assertIsInstance(utils.gen_useragent(), str)
        self.assertIsNotNone(utils.gen_useragent())
        self.assertTrue(utils.gen_useragent().startswith('Mozilla'))

    def test_searxng_useragent(self):
        self.assertIsInstance(utils.searxng_useragent(), str)
        self.assertIsNotNone(utils.searxng_useragent())
        self.assertTrue(utils.searxng_useragent().startswith('SearXNG'))

    def test_extract_text(self):
        html_str = """
        <a href="/testlink" class="link_access_account">
            <span class="toto">
                <span>
                    <img src="test.jpg" />
                </span>
            </span>
            <span class="titi">
                            Test text
            </span>
        </a>
        """
        dom = html.fromstring(html_str)
        self.assertEqual(utils.extract_text(dom), 'Test text')
        self.assertEqual(utils.extract_text(dom.xpath('//span')), 'Test text')
        self.assertEqual(utils.extract_text(dom.xpath('//span/text()')), 'Test text')
        self.assertEqual(utils.extract_text(dom.xpath('count(//span)')), '3.0')
        self.assertEqual(utils.extract_text(dom.xpath('boolean(//span)')), 'True')
        self.assertEqual(utils.extract_text(dom.xpath('//img/@src')), 'test.jpg')
        self.assertEqual(utils.extract_text(dom.xpath('//unexistingtag')), '')

    def test_extract_text_allow_none(self):
        self.assertEqual(utils.extract_text(None, allow_none=True), None)

    def test_extract_text_error_none(self):
        with self.assertRaises(ValueError):
            utils.extract_text(None)

    def test_extract_text_error_empty(self):
        with self.assertRaises(ValueError):
            utils.extract_text({})

    def test_extract_url(self):
        def f(html_str, search_url):
            return utils.extract_url(html.fromstring(html_str), search_url)

        self.assertEqual(f('<span id="42">https://example.com</span>', 'http://example.com/'), 'https://example.com/')
        self.assertEqual(f('https://example.com', 'http://example.com/'), 'https://example.com/')
        self.assertEqual(f('//example.com', 'http://example.com/'), 'http://example.com/')
        self.assertEqual(f('//example.com', 'https://example.com/'), 'https://example.com/')
        self.assertEqual(f('/path?a=1', 'https://example.com'), 'https://example.com/path?a=1')
        with self.assertRaises(lxml.etree.ParserError):
            f('', 'https://example.com')
        with self.assertRaises(Exception):
            utils.extract_url([], 'https://example.com')

    def test_ecma_unscape(self):
        self.assertEqual(utils.ecma_unescape('text%20with%20space'), 'text with space')
        self.assertEqual(utils.ecma_unescape('text using %xx: %F3'), 'text using %xx: ó')
        self.assertEqual(utils.ecma_unescape('text using %u: %u5409, %u4E16%u754c'), 'text using %u: 吉, 世界')

    @parameterized.expand(
        [
            ('Example <span id="42">#2</span>', 'Example #2'),
            ('<style>.span { color: red; }</style><span>Example</span>', 'Example'),
            (r'regexp: (?&lt;![a-zA-Z]', r'regexp: (?<![a-zA-Z]'),
            (r'<p><b>Lorem ipsum </i>dolor sit amet</p>', 'Lorem ipsum </i>dolor sit amet</p>'),
            (r'&#x3e &#x3c &#97', '> < a'),
        ]
    )
    def test_html_to_text(self, html_str: str, text_str: str):
        self.assertEqual(utils.html_to_text(html_str), text_str)

    def test_html_to_text_with_a_style_span(self):
        html_str = """
        <a href="/testlink" class="link_access_account">
            <style>
                .toto {
                    color: red;
                }
            </style>
            <span class="toto">
                <span>
                    <img src="test.jpg" />
                </span>
            </span>
            <span class="titi">
                            Test text
            </span>
            <script>value='dummy';</script>
        </a>
        """
        self.assertIsInstance(utils.html_to_text(html_str), str)
        self.assertEqual(utils.html_to_text(html_str), "Test text")


class TestXPathUtils(SearxTestCase):  # pylint: disable=missing-class-docstring

    TEST_DOC = """<ul>
        <li>Text in <b>bold</b> and <i>italic</i> </li>
        <li>Another <b>text</b> <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="></li>
        </ul>"""

    def test_get_xpath_cache(self):
        xp1 = utils.get_xpath('//a')
        xp2 = utils.get_xpath('//div')
        xp3 = utils.get_xpath('//a')

        self.assertEqual(id(xp1), id(xp3))
        self.assertNotEqual(id(xp1), id(xp2))

    def test_get_xpath_type(self):
        utils.get_xpath(lxml.etree.XPath('//a'))

        with self.assertRaises(TypeError):
            utils.get_xpath([])

    def test_get_xpath_invalid(self):
        invalid_xpath = '//a[0].text'
        with self.assertRaises(SearxXPathSyntaxException) as context:
            utils.get_xpath(invalid_xpath)

        self.assertEqual(context.exception.message, 'Invalid expression')
        self.assertEqual(context.exception.xpath_str, invalid_xpath)

    def test_eval_xpath_unregistered_function(self):
        doc = html.fromstring(TestXPathUtils.TEST_DOC)

        invalid_function_xpath = 'int(//a)'
        with self.assertRaises(SearxEngineXPathException) as context:
            utils.eval_xpath(doc, invalid_function_xpath)

        self.assertEqual(context.exception.message, 'Unregistered function')
        self.assertEqual(context.exception.xpath_str, invalid_function_xpath)

    def test_eval_xpath(self):
        doc = html.fromstring(TestXPathUtils.TEST_DOC)

        self.assertEqual(utils.eval_xpath(doc, '//p'), [])
        self.assertEqual(utils.eval_xpath(doc, '//i/text()'), ['italic'])
        self.assertEqual(utils.eval_xpath(doc, 'count(//i)'), 1.0)

    def test_eval_xpath_list(self):
        doc = html.fromstring(TestXPathUtils.TEST_DOC)

        # check a not empty list
        self.assertEqual(utils.eval_xpath_list(doc, '//i/text()'), ['italic'])

        # check min_len parameter
        with self.assertRaises(SearxEngineXPathException) as context:
            utils.eval_xpath_list(doc, '//p', min_len=1)
        self.assertEqual(context.exception.message, 'len(xpath_str) < 1')
        self.assertEqual(context.exception.xpath_str, '//p')

    def test_eval_xpath_getindex(self):
        doc = html.fromstring(TestXPathUtils.TEST_DOC)

        # check index 0
        self.assertEqual(utils.eval_xpath_getindex(doc, '//i/text()', 0), 'italic')

        # default is 'something'
        self.assertEqual(utils.eval_xpath_getindex(doc, '//i/text()', 1, default='something'), 'something')

        # default is None
        self.assertIsNone(utils.eval_xpath_getindex(doc, '//i/text()', 1, default=None))

        # index not found
        with self.assertRaises(SearxEngineXPathException) as context:
            utils.eval_xpath_getindex(doc, '//i/text()', 1)
        self.assertEqual(context.exception.message, 'index 1 not found')

        # not a list
        with self.assertRaises(SearxEngineXPathException) as context:
            utils.eval_xpath_getindex(doc, 'count(//i)', 1)
        self.assertEqual(context.exception.message, 'the result is not a list')

    def test_detect_language(self):
        # make sure new line are not an issue
        # fasttext.predict('') does not accept new line.
        l = utils.detect_language('The quick brown fox jumps over\nthe lazy dog')
        self.assertEqual(l, 'en')

        l = utils.detect_language(
            'いろはにほへと ちりぬるを わかよたれそ つねならむ うゐのおくやま けふこえて あさきゆめみし ゑひもせす'
        )
        self.assertEqual(l, 'ja')

        l = utils.detect_language('Pijamalı hasta yağız şoföre çabucak güvendi.')
        self.assertEqual(l, 'tr')

        l = utils.detect_language('')
        self.assertIsNone(l)

        # mix languages --> None
        l = utils.detect_language('The いろはにほへと Pijamalı')
        self.assertIsNone(l)

        with self.assertRaises(ValueError):
            utils.detect_language(None)  # type: ignore
