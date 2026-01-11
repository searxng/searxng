# SPDX-License-Identifier: AGPL-3.0-or-later
"""Utility functions for the engines"""


import re
import importlib
import importlib.util
import json
import types

import typing as t
from collections.abc import MutableMapping, Callable

from numbers import Number
from os.path import splitext, join
from random import choice
from html.parser import HTMLParser
from html import escape
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from datetime import timedelta
from markdown_it import MarkdownIt

from lxml import html
from lxml.etree import XPath, XPathError, XPathSyntaxError
from lxml.etree import ElementBase, _Element  # pyright: ignore[reportPrivateUsage]

from searx import settings
from searx.data import USER_AGENTS, data_dir, gsa_useragents_loader
from searx.version import VERSION_TAG
from searx.sxng_locales import sxng_locales
from searx.exceptions import SearxXPathSyntaxException, SearxEngineXPathException
from searx import logger

if t.TYPE_CHECKING:
    import fasttext.FastText  # type: ignore


logger = logger.getChild('utils')

XPathSpecType: t.TypeAlias = str | XPath
"""Type alias used by :py:obj:`searx.utils.get_xpath`,
:py:obj:`searx.utils.eval_xpath` and other XPath selectors."""

ElementType: t.TypeAlias = ElementBase | _Element


_BLOCKED_TAGS = ('script', 'style')

_ECMA_UNESCAPE4_RE = re.compile(r'%u([0-9a-fA-F]{4})', re.UNICODE)
_ECMA_UNESCAPE2_RE = re.compile(r'%([0-9a-fA-F]{2})', re.UNICODE)

_JS_STRING_DELIMITERS = re.compile(r'(["\'`])')
_JS_QUOTE_KEYS_RE = re.compile(r'([\{\s,])([\$_\w][\$_\w0-9]*)(:)')
_JS_VOID_OR_UNDEFINED_RE = re.compile(r'void\s+[0-9]+|void\s*\([0-9]+\)|undefined')
_JS_DECIMAL_RE = re.compile(r"([\[\,:])\s*(\-?)\s*([0-9_]*)\.([0-9_]*)")
_JS_DECIMAL2_RE = re.compile(r"([\[\,:])\s*(\-?)\s*([0-9_]+)")
_JS_EXTRA_COMA_RE = re.compile(r"\s*,\s*([\]\}])")
_JS_STRING_ESCAPE_RE = re.compile(r'\\(.)')
_JSON_PASSTHROUGH_ESCAPES = R'"\bfnrtu'

_XPATH_CACHE: dict[str, XPath] = {}
_LANG_TO_LC_CACHE: dict[str, dict[str, str]] = {}

_FASTTEXT_MODEL: "fasttext.FastText._FastText | None" = None  # pyright: ignore[reportPrivateUsage]
"""fasttext model to predict language of a search term"""

SEARCH_LANGUAGE_CODES = frozenset([searxng_locale[0].split('-')[0] for searxng_locale in sxng_locales])
"""Languages supported by most searxng engines (:py:obj:`searx.sxng_locales.sxng_locales`)."""


class _NotSetClass:  # pylint: disable=too-few-public-methods
    """Internal class for this module, do not create instance of this class.
    Replace the None value, allow explicitly pass None as a function argument"""


_NOTSET = _NotSetClass()


def searxng_useragent() -> str:
    """Return the SearXNG User Agent"""
    return f"SearXNG/{VERSION_TAG} {settings['outgoing']['useragent_suffix']}".strip()


def gen_useragent(os_string: str | None = None) -> str:
    """Return a random browser User Agent

    See searx/data/useragents.json
    """
    return USER_AGENTS['ua'].format(
        os=os_string or choice(USER_AGENTS['os']),
        version=choice(USER_AGENTS['versions']),
    )


def gen_gsa_useragent() -> str:
    """Return a random GSA User Agent suitable for Google

    See searx/data/gsa_useragents.txt
    """
    return choice(gsa_useragents_loader())


class HTMLTextExtractor(HTMLParser):
    """Internal class to extract text from HTML"""

    def __init__(self):
        HTMLParser.__init__(self)
        self.result: list[str] = []
        self.tags: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        if tag == 'br':
            self.result.append(' ')

    def handle_endtag(self, tag: str) -> None:
        if not self.tags:
            return

        if tag != self.tags[-1]:
            self.result.append(f"</{tag}>")
            return

        self.tags.pop()

    def is_valid_tag(self):
        return not self.tags or self.tags[-1] not in _BLOCKED_TAGS

    def handle_data(self, data: str) -> None:
        if not self.is_valid_tag():
            return
        self.result.append(data)

    def handle_charref(self, name: str) -> None:
        if not self.is_valid_tag():
            return
        if name[0] in ('x', 'X'):
            codepoint = int(name[1:], 16)
        else:
            codepoint = int(name)
        self.result.append(chr(codepoint))

    def handle_entityref(self, name: str) -> None:
        if not self.is_valid_tag():
            return
        # codepoint = htmlentitydefs.name2codepoint[name]
        # self.result.append(chr(codepoint))
        self.result.append(name)

    def get_text(self):
        return ''.join(self.result).strip()

    def error(self, message: str) -> None:
        # error handle is needed in <py3.10
        # https://github.com/python/cpython/pull/8562/files
        raise AssertionError(message)


def html_to_text(html_str: str) -> str:
    """Extract text from a HTML string

    Args:
        * html_str (str): string HTML

    Returns:
        * str: extracted text

    Examples:
        >>> html_to_text('Example <span id="42">#2</span>')
        'Example #2'

        >>> html_to_text('<style>.span { color: red; }</style><span>Example</span>')
        'Example'

        >>> html_to_text(r'regexp: (?&lt;![a-zA-Z]')
        'regexp: (?<![a-zA-Z]'

        >>> html_to_text(r'<p><b>Lorem ipsum </i>dolor sit amet</p>')
        'Lorem ipsum </i>dolor sit amet</p>'

        >>> html_to_text(r'&#x3e &#x3c &#97')
        '> < a'

    """
    if not html_str:
        return ""
    html_str = html_str.replace('\n', ' ').replace('\r', ' ')
    html_str = ' '.join(html_str.split())
    s = HTMLTextExtractor()
    try:
        s.feed(html_str)
        s.close()
    except AssertionError:
        s = HTMLTextExtractor()
        s.feed(escape(html_str, quote=True))
        s.close()
    return s.get_text()


def markdown_to_text(markdown_str: str) -> str:
    """Extract text from a Markdown string

    Args:
        * markdown_str (str): string Markdown

    Returns:
        * str: extracted text

    Examples:
        >>> markdown_to_text('[example](https://example.com)')
        'example'

        >>> markdown_to_text('## Headline')
        'Headline'
    """

    html_str: str = (
        MarkdownIt("commonmark", {"typographer": True}).enable(["replacements", "smartquotes"]).render(markdown_str)
    )
    return html_to_text(html_str)


def extract_text(
    xpath_results: list[ElementType] | ElementType | str | Number | bool | None,
    allow_none: bool = False,
) -> str | None:
    """Extract text from a lxml result

    - If ``xpath_results`` is a list of :py:obj:`ElementType` objects, extract
      the text from each result and concatenate the list in a string.

    - If ``xpath_results`` is a :py:obj:`ElementType` object, extract all the
      text node from it ( :py:obj:`lxml.html.tostring`, ``method="text"`` )

    - If ``xpath_results`` is of type :py:obj:`str` or :py:obj:`Number`,
      :py:obj:`bool` the string value is returned.

    - If ``xpath_results`` is of type ``None`` a :py:obj:`ValueError` is raised,
      except ``allow_none`` is ``True`` where ``None`` is returned.

    """
    if isinstance(xpath_results, list):
        # it's list of result : concat everything using recursive call
        result = ''
        for e in xpath_results:
            result = result + (extract_text(e) or '')
        return result.strip()
    if isinstance(xpath_results, ElementType):
        # it's a element
        text: str = html.tostring(  # type: ignore
            xpath_results,  # pyright: ignore[reportArgumentType]
            encoding='unicode',
            method='text',
            with_tail=False,
        )
        text = text.strip().replace('\n', ' ')  # type: ignore
        return ' '.join(text.split())  # type: ignore
    if isinstance(xpath_results, (str, Number, bool)):
        return str(xpath_results)
    if xpath_results is None and allow_none:
        return None
    if xpath_results is None and not allow_none:
        raise ValueError('extract_text(None, allow_none=False)')
    raise ValueError('unsupported type')


def normalize_url(url: str, base_url: str) -> str:
    """Normalize URL: add protocol, join URL with base_url, add trailing slash if there is no path

    Args:
        * url (str): Relative URL
        * base_url (str): Base URL, it must be an absolute URL.

    Example:
        >>> normalize_url('https://example.com', 'http://example.com/')
        'https://example.com/'
        >>> normalize_url('//example.com', 'http://example.com/')
        'http://example.com/'
        >>> normalize_url('//example.com', 'https://example.com/')
        'https://example.com/'
        >>> normalize_url('/path?a=1', 'https://example.com')
        'https://example.com/path?a=1'
        >>> normalize_url('', 'https://example.com')
        'https://example.com/'
        >>> normalize_url('/test', '/path')
        raise ValueError

    Raises:
        * lxml.etree.ParserError

    Returns:
        * str: normalized URL
    """
    if url.startswith('//'):
        # add http or https to this kind of url //example.com/
        parsed_search_url = urlparse(base_url)
        url = '{0}:{1}'.format(parsed_search_url.scheme or 'http', url)
    elif url.startswith('/'):
        # fix relative url to the search engine
        url = urljoin(base_url, url)

    # fix relative urls that fall through the crack
    if '://' not in url:
        url = urljoin(base_url, url)

    parsed_url = urlparse(url)

    # add a / at this end of the url if there is no path
    if not parsed_url.netloc:
        raise ValueError('Cannot parse url')
    if not parsed_url.path:
        url += '/'

    return url


def extract_url(xpath_results: list[ElementType] | ElementType | str | Number | bool | None, base_url: str) -> str:
    """Extract and normalize URL from lxml Element

    Example:
        >>> def f(s, search_url):
        >>>    return searx.utils.extract_url(html.fromstring(s), search_url)
        >>> f('<span id="42">https://example.com</span>', 'http://example.com/')
        'https://example.com/'
        >>> f('https://example.com', 'http://example.com/')
        'https://example.com/'
        >>> f('//example.com', 'http://example.com/')
        'http://example.com/'
        >>> f('//example.com', 'https://example.com/')
        'https://example.com/'
        >>> f('/path?a=1', 'https://example.com')
        'https://example.com/path?a=1'
        >>> f('', 'https://example.com')
        raise lxml.etree.ParserError
        >>> searx.utils.extract_url([], 'https://example.com')
        raise ValueError

    Raises:
        * ValueError
        * lxml.etree.ParserError

    Returns:
        * str: normalized URL
    """
    if xpath_results == []:
        raise ValueError('Empty url resultset')

    url = extract_text(xpath_results)
    if url:
        return normalize_url(url, base_url)
    raise ValueError('URL not found')


def dict_subset(dictionary: MutableMapping[t.Any, t.Any], properties: set[str]) -> MutableMapping[str, t.Any]:
    """Extract a subset of a dict

    Examples:
        >>> dict_subset({'A': 'a', 'B': 'b', 'C': 'c'}, ['A', 'C'])
        {'A': 'a', 'C': 'c'}
        >>> >> dict_subset({'A': 'a', 'B': 'b', 'C': 'c'}, ['A', 'D'])
        {'A': 'a'}
    """
    return {k: dictionary[k] for k in properties if k in dictionary}


def humanize_bytes(size: int | float, precision: int = 2):
    """Determine the *human readable* value of bytes on 1024 base (1KB=1024B)."""
    s = ['B ', 'KB', 'MB', 'GB', 'TB']

    x = len(s)
    p = 0
    while size > 1024 and p < x:
        p += 1
        size = size / 1024.0
    return "%.*f %s" % (precision, size, s[p])


def humanize_number(size: int | float, precision: int = 0):
    """Determine the *human readable* value of a decimal number."""
    s = ['', 'K', 'M', 'B', 'T']

    x = len(s)
    p = 0
    while size > 1000 and p < x:
        p += 1
        size = size / 1000.0
    return "%.*f%s" % (precision, size, s[p])


def convert_str_to_int(number_str: str) -> int:
    """Convert number_str to int or 0 if number_str is not a number."""
    if number_str.isdigit():
        return int(number_str)
    return 0


def extr(txt: str, begin: str, end: str, default: str = ""):
    """Extract the string between ``begin`` and ``end`` from ``txt``

    :param txt:     String to search in
    :param begin:   First string to be searched for
    :param end:     Second string to be searched for after ``begin``
    :param default: Default value if one of ``begin`` or ``end`` is not
                    found.  Defaults to an empty string.
    :return: The string between the two search-strings ``begin`` and ``end``.
             If at least one of ``begin`` or ``end`` is not found, the value of
             ``default`` is returned.

    Examples:
      >>> extr("abcde", "a", "e")
      "bcd"
      >>> extr("abcde", "a", "z", deafult="nothing")
      "nothing"

    """

    # From https://github.com/mikf/gallery-dl/blob/master/gallery_dl/text.py#L129

    try:
        first = txt.index(begin) + len(begin)
        return txt[first : txt.index(end, first)]
    except ValueError:
        return default


def int_or_zero(num: list[str] | str) -> int:
    """Convert num to int or 0. num can be either a str or a list.
    If num is a list, the first element is converted to int (or return 0 if the list is empty).
    If num is a str, see convert_str_to_int
    """
    if isinstance(num, list):
        if len(num) < 1:
            return 0
        num = num[0]
    return convert_str_to_int(num)


def load_module(filename: str, module_dir: str) -> types.ModuleType:
    modname = splitext(filename)[0]
    modpath = join(module_dir, filename)
    # and https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    spec = importlib.util.spec_from_file_location(modname, modpath)
    if not spec:
        raise ValueError(f"Error loading '{modpath}' module")
    module = importlib.util.module_from_spec(spec)
    if not spec.loader:
        raise ValueError(f"Error loading '{modpath}' module")
    spec.loader.exec_module(module)
    return module


def to_string(obj: t.Any) -> str:
    """Convert obj to its string representation."""
    if isinstance(obj, str):
        return obj
    if hasattr(obj, '__str__'):
        return str(obj)
    return repr(obj)


def ecma_unescape(string: str) -> str:
    """Python implementation of the unescape javascript function

    https://www.ecma-international.org/ecma-262/6.0/#sec-unescape-string
    https://developer.mozilla.org/fr/docs/Web/JavaScript/Reference/Objets_globaux/unescape

    Examples:
        >>> ecma_unescape('%u5409')
        '吉'
        >>> ecma_unescape('%20')
        ' '
        >>> ecma_unescape('%F3')
        'ó'
    """
    # "%u5409" becomes "吉"
    string = _ECMA_UNESCAPE4_RE.sub(lambda e: chr(int(e.group(1), 16)), string)
    # "%20" becomes " ", "%F3" becomes "ó"
    string = _ECMA_UNESCAPE2_RE.sub(lambda e: chr(int(e.group(1), 16)), string)
    return string


def remove_pua_from_str(string: str):
    """Removes unicode's "PRIVATE USE CHARACTER"s (PUA_) from a string.

    .. _PUA: https://en.wikipedia.org/wiki/Private_Use_Areas
    """
    pua_ranges = ((0xE000, 0xF8FF), (0xF0000, 0xFFFFD), (0x100000, 0x10FFFD))
    s: list[str] = []
    for c in string:
        i = ord(c)
        if any(a <= i <= b for (a, b) in pua_ranges):
            continue
        s.append(c)
    return "".join(s)


def get_string_replaces_function(replaces: dict[str, str]) -> Callable[[str], str]:
    rep = {re.escape(k): v for k, v in replaces.items()}
    pattern = re.compile("|".join(rep.keys()))

    def func(text: str):
        return pattern.sub(lambda m: rep[re.escape(m.group(0))], text)

    return func


def get_engine_from_settings(name: str) -> dict[str, dict[str, str]]:
    """Return engine configuration from settings.yml of a given engine name"""

    if 'engines' not in settings:
        return {}

    for engine in settings['engines']:
        if 'name' not in engine:
            continue
        if name == engine['name']:
            return engine

    return {}


def get_xpath(xpath_spec: XPathSpecType) -> XPath:
    """Return cached compiled :py:obj:`lxml.etree.XPath` object.

    ``TypeError``:
      Raised when ``xpath_spec`` is neither a :py:obj:`str` nor a
      :py:obj:`lxml.etree.XPath`.

    ``SearxXPathSyntaxException``:
      Raised when there is a syntax error in the *XPath* selector (``str``).
    """
    if isinstance(xpath_spec, str):
        result = _XPATH_CACHE.get(xpath_spec, None)
        if result is None:
            try:
                result = XPath(xpath_spec)
            except XPathSyntaxError as e:
                raise SearxXPathSyntaxException(xpath_spec, str(e.msg)) from e
            _XPATH_CACHE[xpath_spec] = result
        return result

    if isinstance(xpath_spec, XPath):
        return xpath_spec

    raise TypeError('xpath_spec must be either a str or a lxml.etree.XPath')  # pyright: ignore[reportUnreachable]


def eval_xpath(element: ElementType, xpath_spec: XPathSpecType) -> t.Any:
    """Equivalent of ``element.xpath(xpath_str)`` but compile ``xpath_str`` into
    a :py:obj:`lxml.etree.XPath` object once for all.  The return value of
    ``xpath(..)`` is complex, read `XPath return values`_ for more details.

    .. _XPath return values:
        https://lxml.de/xpathxslt.html#xpath-return-values

    ``TypeError``:
      Raised when ``xpath_spec`` is neither a :py:obj:`str` nor a
      :py:obj:`lxml.etree.XPath`.

    ``SearxXPathSyntaxException``:
      Raised when there is a syntax error in the *XPath* selector (``str``).

    ``SearxEngineXPathException:``
      Raised when the XPath can't be evaluated (masked
      :py:obj:`lxml.etree..XPathError`).
    """
    xpath: XPath = get_xpath(xpath_spec)
    try:
        # https://lxml.de/xpathxslt.html#xpath-return-values
        return xpath(element)
    except XPathError as e:
        arg = ' '.join([str(i) for i in e.args])
        raise SearxEngineXPathException(xpath_spec, arg) from e


def eval_xpath_list(element: ElementType, xpath_spec: XPathSpecType, min_len: int | None = None) -> list[t.Any]:
    """Same as :py:obj:`searx.utils.eval_xpath`, but additionally ensures the
    return value is a :py:obj:`list`.  The minimum length of the list is also
    checked (if ``min_len`` is set)."""

    result: list[t.Any] = eval_xpath(element, xpath_spec)
    if not isinstance(result, list):
        raise SearxEngineXPathException(xpath_spec, 'the result is not a list')
    if min_len is not None and min_len > len(result):
        raise SearxEngineXPathException(xpath_spec, 'len(xpath_str) < ' + str(min_len))
    return result


def eval_xpath_getindex(
    element: ElementType,
    xpath_spec: XPathSpecType,
    index: int,
    default: t.Any = _NOTSET,
) -> t.Any:
    """Same as :py:obj:`searx.utils.eval_xpath_list`, but returns item on
    position ``index`` from the list (index starts with ``0``).

    The exceptions known from :py:obj:`searx.utils.eval_xpath` are thrown. If a
    default is specified, this is returned if an element at position ``index``
    could not be determined.
    """

    result = eval_xpath_list(element, xpath_spec)
    if -len(result) <= index < len(result):
        return result[index]
    if default == _NOTSET:
        # raise an SearxEngineXPathException instead of IndexError to record
        # xpath_spec
        raise SearxEngineXPathException(xpath_spec, 'index ' + str(index) + ' not found')
    return default


def _get_fasttext_model() -> "fasttext.FastText._FastText":  # pyright: ignore[reportPrivateUsage]
    global _FASTTEXT_MODEL  # pylint: disable=global-statement
    if _FASTTEXT_MODEL is None:
        import fasttext  # pylint: disable=import-outside-toplevel

        # Monkey patch: prevent fasttext from showing a (useless) warning when loading a model.
        fasttext.FastText.eprint = lambda x: None  # type: ignore
        _FASTTEXT_MODEL = fasttext.load_model(str(data_dir / 'lid.176.ftz'))  # type: ignore
    return _FASTTEXT_MODEL


def get_embeded_stream_url(url: str):
    """
    Converts a standard video URL into its embed format. Supported services include Youtube,
    Facebook, Instagram, TikTok, Dailymotion, and Bilibili.
    """
    parsed_url = urlparse(url)
    iframe_src = None

    # YouTube
    if parsed_url.netloc in ['www.youtube.com', 'youtube.com'] and parsed_url.path == '/watch' and parsed_url.query:
        video_id = parse_qs(parsed_url.query).get('v', [])
        if video_id:
            iframe_src = 'https://www.youtube-nocookie.com/embed/' + video_id[0]

    # Facebook
    elif parsed_url.netloc in ['www.facebook.com', 'facebook.com']:
        encoded_href = urlencode({'href': url})
        iframe_src = 'https://www.facebook.com/plugins/video.php?allowfullscreen=true&' + encoded_href

    # Instagram
    elif parsed_url.netloc in ['www.instagram.com', 'instagram.com'] and parsed_url.path.startswith('/p/'):
        if parsed_url.path.endswith('/'):
            iframe_src = url + 'embed'
        else:
            iframe_src = url + '/embed'

    # TikTok
    elif (
        parsed_url.netloc in ['www.tiktok.com', 'tiktok.com']
        and parsed_url.path.startswith('/@')
        and '/video/' in parsed_url.path
    ):
        path_parts = parsed_url.path.split('/video/')
        video_id = path_parts[1]
        iframe_src = 'https://www.tiktok.com/embed/' + video_id

    # Dailymotion
    elif parsed_url.netloc in ['www.dailymotion.com', 'dailymotion.com'] and parsed_url.path.startswith('/video/'):
        path_parts = parsed_url.path.split('/')
        if len(path_parts) == 3:
            video_id = path_parts[2]
            iframe_src = 'https://www.dailymotion.com/embed/video/' + video_id

    # Bilibili
    elif parsed_url.netloc in ['www.bilibili.com', 'bilibili.com'] and parsed_url.path.startswith('/video/'):
        path_parts = parsed_url.path.split('/')

        video_id = path_parts[2]
        param_key = None
        if video_id.startswith('av'):
            video_id = video_id[2:]
            param_key = 'aid'
        elif video_id.startswith('BV'):
            param_key = 'bvid'

        iframe_src = (
            f'https://player.bilibili.com/player.html?{param_key}={video_id}&high_quality=1&autoplay=false&danmaku=0'
        )

    return iframe_src


def detect_language(text: str, threshold: float = 0.3, only_search_languages: bool = False) -> str | None:
    """Detect the language of the ``text`` parameter.

    :param str text: The string whose language is to be detected.

    :param float threshold: Threshold filters the returned labels by a threshold
        on probability.  A choice of 0.3 will return labels with at least 0.3
        probability.

    :param bool only_search_languages: If ``True``, returns only supported
        SearXNG search languages.  see :py:obj:`searx.languages`

    :rtype: str, None
    :returns:
        The detected language code or ``None``. See below.

    :raises ValueError: If ``text`` is not a string.

    The language detection is done by using `a fork`_ of the fastText_ library
    (`python fasttext`_). fastText_ distributes the `language identification
    model`_, for reference:

    - `FastText.zip: Compressing text classification models`_
    - `Bag of Tricks for Efficient Text Classification`_

    The `language identification model`_ support the language codes
    (ISO-639-3)::

        af als am an ar arz as ast av az azb ba bar bcl be bg bh bn bo bpy br bs
        bxr ca cbk ce ceb ckb co cs cv cy da de diq dsb dty dv el eml en eo es
        et eu fa fi fr frr fy ga gd gl gn gom gu gv he hi hif hr hsb ht hu hy ia
        id ie ilo io is it ja jbo jv ka kk km kn ko krc ku kv kw ky la lb lez li
        lmo lo lrc lt lv mai mg mhr min mk ml mn mr mrj ms mt mwl my myv mzn nah
        nap nds ne new nl nn no oc or os pa pam pfl pl pms pnb ps pt qu rm ro ru
        rue sa sah sc scn sco sd sh si sk sl so sq sr su sv sw ta te tg th tk tl
        tr tt tyv ug uk ur uz vec vep vi vls vo wa war wuu xal xmf yi yo yue zh

    By using ``only_search_languages=True`` the `language identification model`_
    is harmonized with the SearXNG's language (locale) model.  General
    conditions of SearXNG's locale model are:

    a. SearXNG's locale of a query is passed to the
       :py:obj:`searx.locales.get_engine_locale` to get a language and/or region
       code that is used by an engine.

    b. Most of SearXNG's engines do not support all the languages from `language
       identification model`_ and there is also a discrepancy in the ISO-639-3
       (fasttext) and ISO-639-2 (SearXNG)handling.  Further more, in SearXNG the
       locales like ``zh-TH`` (``zh-CN``) are mapped to ``zh_Hant``
       (``zh_Hans``) while the `language identification model`_ reduce both to
       ``zh``.

    .. _a fork: https://github.com/searxng/fasttext-predict
    .. _fastText: https://fasttext.cc/
    .. _python fasttext: https://pypi.org/project/fasttext/
    .. _language identification model: https://fasttext.cc/docs/en/language-identification.html
    .. _Bag of Tricks for Efficient Text Classification: https://arxiv.org/abs/1607.01759
    .. _`FastText.zip: Compressing text classification models`: https://arxiv.org/abs/1612.03651

    """
    if not isinstance(text, str):
        raise ValueError('text must a str')  # pyright: ignore[reportUnreachable]
    r = _get_fasttext_model().predict(text.replace('\n', ' '), k=1, threshold=threshold)  # type: ignore
    if isinstance(r, tuple) and len(r) == 2 and len(r[0]) > 0 and len(r[1]) > 0:  # type: ignore
        language = r[0][0].split('__label__')[1]  # type: ignore
        if only_search_languages and language not in SEARCH_LANGUAGE_CODES:
            return None
        return language  # type: ignore
    return None


def _j2p_process_escape(match: re.Match[str]) -> str:
    # deal with ECMA escape characters
    _escape = match.group(1) or match.group(2)
    return (
        Rf'\{_escape}'
        if _escape in _JSON_PASSTHROUGH_ESCAPES
        else R'\u00' if _escape == 'x' else '' if _escape == '\n' else _escape
    )


def _j2p_decimal(match: re.Match[str]) -> str:
    return (
        match.group(1)
        + match.group(2)
        + (match.group(3).replace("_", "") or "0")
        + "."
        + (match.group(4).replace("_", "") or "0")
    )


def _j2p_decimal2(match: re.Match[str]) -> str:
    return match.group(1) + match.group(2) + match.group(3).replace("_", "")


def js_obj_str_to_python(js_obj_str: str) -> t.Any:
    """Convert a javascript variable into JSON and then load the value

    It does not deal with all cases, but it is good enough for now.
    chompjs has a better implementation.
    """
    s = js_obj_str_to_json_str(js_obj_str)
    # load the JSON and return the result
    if s == "":
        raise ValueError("js_obj_str can't be an empty string")
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        logger.debug("Internal error: js_obj_str_to_python creates invalid JSON:\n%s", s)
        raise ValueError("js_obj_str_to_python creates invalid JSON") from e


def js_obj_str_to_json_str(js_obj_str: str) -> str:
    if not isinstance(js_obj_str, str):
        raise ValueError("js_obj_str must be of type str")
    if js_obj_str == "":
        raise ValueError("js_obj_str can't be an empty string")

    # when in_string is not None, it contains the character that has opened the string
    # either simple quote or double quote
    in_string = None
    # cut the string:
    # r"""{ a:"f\"irst", c:'sec"ond'}"""
    # becomes
    # ['{ a:', '"', 'f\\', '"', 'irst', '"', ', c:', "'", 'sec', '"', 'ond', "'", '}']
    parts = _JS_STRING_DELIMITERS.split(js_obj_str)
    # does the previous part ends with a backslash?
    blackslash_just_before = False
    for i, p in enumerate(parts):
        if p == in_string and not blackslash_just_before:
            # * the current part matches the character which has opened the string
            # * there is no antislash just before
            # --> the current part close the current string
            in_string = None
            # replace simple quote and ` by double quote
            # since JSON supports only double quote for string
            parts[i] = '"'

        elif in_string:
            # --> we are in a JS string
            # replace the colon by a temporary character
            # so _JS_QUOTE_KEYS_RE doesn't have to deal with colon inside the JS strings
            p = p.replace(':', chr(1))
            # replace JS escape sequences by JSON escape sequences
            p = _JS_STRING_ESCAPE_RE.sub(_j2p_process_escape, p)
            # the JS string is delimited by simple quote.
            # This is not supported by JSON.
            # simple quote delimited string are converted to double quote delimited string
            # here, inside a JS string, we escape the double quote
            if in_string == "'":
                p = p.replace('"', r'\"')
            parts[i] = p
            # deal with the sequence blackslash then quote
            # since js_obj_str splits on quote, we detect this case:
            # * the previous part ends with a black slash
            # * the current part is a single quote
            # when detected the blackslash is removed on the previous part
            if blackslash_just_before and p[:1] == "'":
                parts[i - 1] = parts[i - 1][:-1]

        elif in_string is None and p in ('"', "'", "`"):
            # we are not in string but p is string delimiter
            # --> that's the start of a new string
            in_string = p
            # replace simple quote by double quote
            # since JSON supports only double quote for string
            parts[i] = '"'

        elif in_string is None:
            # we are not in a string
            # replace by null these values:
            # * void 0
            # * void(0)
            # * undefined
            # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/void
            p = _JS_VOID_OR_UNDEFINED_RE.sub("null", p)
            # make sure there is a leading zero in front of float
            p = _JS_DECIMAL_RE.sub(_j2p_decimal, p)
            p = _JS_DECIMAL2_RE.sub(_j2p_decimal2, p)
            # remove extra coma in a list or an object
            # for example [1,2,3,] becomes [1,2,3]
            p = _JS_EXTRA_COMA_RE.sub(lambda match: match.group(1), p)
            parts[i] = p

        # update for the next iteration
        blackslash_just_before = len(p) > 0 and p[-1] == '\\'

    # join the string
    s = ''.join(parts)
    # add quote arround the key
    # { a: 12 }
    # becomes
    # { "a": 12 }
    s = _JS_QUOTE_KEYS_RE.sub(r'\1"\2"\3', s)
    # replace the surogate character by colon and strip whitespaces
    s = s.replace(chr(1), ':').strip()
    return s


def parse_duration_string(duration_str: str) -> timedelta | None:
    """Parse a time string in format MM:SS or HH:MM:SS and convert it to a `timedelta` object.

    Returns None if the provided string doesn't match any of the formats.
    """
    duration_str = duration_str.strip()

    if not duration_str:
        return None

    try:
        # prepending ["00"] here inits hours to 0 if they are not provided
        time_parts = (["00"] + duration_str.split(":"))[:3]
        hours, minutes, seconds = map(int, time_parts)
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)

    except (ValueError, TypeError):
        pass

    return None
