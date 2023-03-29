# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pyright: basic
"""Utility functions for the engines

"""
import re
import importlib
import importlib.util
import types

from typing import Optional, Union, Any, Set, List, Dict, MutableMapping, Tuple, Callable
from numbers import Number
from os.path import splitext, join
from random import choice
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from lxml import html
from lxml.etree import ElementBase, XPath, XPathError, XPathSyntaxError, _ElementStringResult, _ElementUnicodeResult

from searx import settings
from searx.data import USER_AGENTS, data_dir
from searx.version import VERSION_TAG
from searx.sxng_locales import sxng_locales
from searx.exceptions import SearxXPathSyntaxException, SearxEngineXPathException
from searx import logger


logger = logger.getChild('utils')

XPathSpecType = Union[str, XPath]

_BLOCKED_TAGS = ('script', 'style')

_ECMA_UNESCAPE4_RE = re.compile(r'%u([0-9a-fA-F]{4})', re.UNICODE)
_ECMA_UNESCAPE2_RE = re.compile(r'%([0-9a-fA-F]{2})', re.UNICODE)

_STORAGE_UNIT_VALUE: Dict[str, int] = {
    'TB': 1024 * 1024 * 1024 * 1024,
    'GB': 1024 * 1024 * 1024,
    'MB': 1024 * 1024,
    'TiB': 1000 * 1000 * 1000 * 1000,
    'MiB': 1000 * 1000,
    'KiB': 1000,
}

_XPATH_CACHE: Dict[str, XPath] = {}
_LANG_TO_LC_CACHE: Dict[str, Dict[str, str]] = {}

_FASTTEXT_MODEL: Optional["fasttext.FastText._FastText"] = None
"""fasttext model to predict laguage of a search term"""

SEARCH_LANGUAGE_CODES = frozenset([searxng_locale[0].split('-')[0] for searxng_locale in sxng_locales])
"""Languages supported by most searxng engines (:py:obj:`searx.sxng_locales.sxng_locales`)."""


class _NotSetClass:  # pylint: disable=too-few-public-methods
    """Internal class for this module, do not create instance of this class.
    Replace the None value, allow explicitly pass None as a function argument"""


_NOTSET = _NotSetClass()


def searx_useragent() -> str:
    """Return the searx User Agent"""
    return 'searx/{searx_version} {suffix}'.format(
        searx_version=VERSION_TAG, suffix=settings['outgoing']['useragent_suffix']
    ).strip()


def gen_useragent(os_string: Optional[str] = None) -> str:
    """Return a random browser User Agent

    See searx/data/useragents.json
    """
    return USER_AGENTS['ua'].format(os=os_string or choice(USER_AGENTS['os']), version=choice(USER_AGENTS['versions']))


class _HTMLTextExtractorException(Exception):
    """Internal exception raised when the HTML is invalid"""


class _HTMLTextExtractor(HTMLParser):  # pylint: disable=W0223  # (see https://bugs.python.org/issue31844)
    """Internal class to extract text from HTML"""

    def __init__(self):
        HTMLParser.__init__(self)
        self.result = []
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == 'br':
            self.result.append(' ')

    def handle_endtag(self, tag):
        if not self.tags:
            return

        if tag != self.tags[-1]:
            raise _HTMLTextExtractorException()

        self.tags.pop()

    def is_valid_tag(self):
        return not self.tags or self.tags[-1] not in _BLOCKED_TAGS

    def handle_data(self, data):
        if not self.is_valid_tag():
            return
        self.result.append(data)

    def handle_charref(self, name):
        if not self.is_valid_tag():
            return
        if name[0] in ('x', 'X'):
            codepoint = int(name[1:], 16)
        else:
            codepoint = int(name)
        self.result.append(chr(codepoint))

    def handle_entityref(self, name):
        if not self.is_valid_tag():
            return
        # codepoint = htmlentitydefs.name2codepoint[name]
        # self.result.append(chr(codepoint))
        self.result.append(name)

    def get_text(self):
        return ''.join(self.result).strip()


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
    """
    html_str = html_str.replace('\n', ' ').replace('\r', ' ')
    html_str = ' '.join(html_str.split())
    s = _HTMLTextExtractor()
    try:
        s.feed(html_str)
    except _HTMLTextExtractorException:
        logger.debug("HTMLTextExtractor: invalid HTML\n%s", html_str)
    return s.get_text()


def extract_text(xpath_results, allow_none: bool = False) -> Optional[str]:
    """Extract text from a lxml result

    * if xpath_results is list, extract the text from each result and concat the list
    * if xpath_results is a xml element, extract all the text node from it
      ( text_content() method from lxml )
    * if xpath_results is a string element, then it's already done
    """
    if isinstance(xpath_results, list):
        # it's list of result : concat everything using recursive call
        result = ''
        for e in xpath_results:
            result = result + (extract_text(e) or '')
        return result.strip()
    if isinstance(xpath_results, ElementBase):
        # it's a element
        text: str = html.tostring(xpath_results, encoding='unicode', method='text', with_tail=False)
        text = text.strip().replace('\n', ' ')
        return ' '.join(text.split())
    if isinstance(xpath_results, (_ElementStringResult, _ElementUnicodeResult, str, Number, bool)):
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


def extract_url(xpath_results, base_url) -> str:
    """Extract and normalize URL from lxml Element

    Args:
        * xpath_results (Union[List[html.HtmlElement], html.HtmlElement]): lxml Element(s)
        * base_url (str): Base URL

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


def dict_subset(dictionary: MutableMapping, properties: Set[str]) -> Dict:
    """Extract a subset of a dict

    Examples:
        >>> dict_subset({'A': 'a', 'B': 'b', 'C': 'c'}, ['A', 'C'])
        {'A': 'a', 'C': 'c'}
        >>> >> dict_subset({'A': 'a', 'B': 'b', 'C': 'c'}, ['A', 'D'])
        {'A': 'a'}
    """
    return {k: dictionary[k] for k in properties if k in dictionary}


def get_torrent_size(filesize: str, filesize_multiplier: str) -> Optional[int]:
    """

    Args:
        * filesize (str): size
        * filesize_multiplier (str): TB, GB, .... TiB, GiB...

    Returns:
        * int: number of bytes

    Example:
        >>> get_torrent_size('5', 'GB')
        5368709120
        >>> get_torrent_size('3.14', 'MiB')
        3140000
    """
    try:
        multiplier = _STORAGE_UNIT_VALUE.get(filesize_multiplier, 1)
        return int(float(filesize) * multiplier)
    except ValueError:
        return None


def convert_str_to_int(number_str: str) -> int:
    """Convert number_str to int or 0 if number_str is not a number."""
    if number_str.isdigit():
        return int(number_str)
    return 0


def int_or_zero(num: Union[List[str], str]) -> int:
    """Convert num to int or 0. num can be either a str or a list.
    If num is a list, the first element is converted to int (or return 0 if the list is empty).
    If num is a str, see convert_str_to_int
    """
    if isinstance(num, list):
        if len(num) < 1:
            return 0
        num = num[0]
    return convert_str_to_int(num)


def is_valid_lang(lang) -> Optional[Tuple[bool, str, str]]:
    """Return language code and name if lang describe a language.

    Examples:
        >>> is_valid_lang('zz')
        None
        >>> is_valid_lang('uk')
        (True, 'uk', 'ukrainian')
        >>> is_valid_lang(b'uk')
        (True, 'uk', 'ukrainian')
        >>> is_valid_lang('en')
        (True, 'en', 'english')
        >>> searx.utils.is_valid_lang('Español')
        (True, 'es', 'spanish')
        >>> searx.utils.is_valid_lang('Spanish')
        (True, 'es', 'spanish')
    """
    if isinstance(lang, bytes):
        lang = lang.decode()
    is_abbr = len(lang) == 2
    lang = lang.lower()
    if is_abbr:
        for l in sxng_locales:
            if l[0][:2] == lang:
                return (True, l[0][:2], l[3].lower())
        return None
    for l in sxng_locales:
        if l[1].lower() == lang or l[3].lower() == lang:
            return (True, l[0][:2], l[3].lower())
    return None


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


def to_string(obj: Any) -> str:
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


def get_string_replaces_function(replaces: Dict[str, str]) -> Callable[[str], str]:
    rep = {re.escape(k): v for k, v in replaces.items()}
    pattern = re.compile("|".join(rep.keys()))

    def func(text):
        return pattern.sub(lambda m: rep[re.escape(m.group(0))], text)

    return func


def get_engine_from_settings(name: str) -> Dict:
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
    """Return cached compiled XPath

    There is no thread lock.
    Worst case scenario, xpath_str is compiled more than one time.

    Args:
        * xpath_spec (str|lxml.etree.XPath): XPath as a str or lxml.etree.XPath

    Returns:
        * result (bool, float, list, str): Results.

    Raises:
        * TypeError: Raise when xpath_spec is neither a str nor a lxml.etree.XPath
        * SearxXPathSyntaxException: Raise when there is a syntax error in the XPath
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

    raise TypeError('xpath_spec must be either a str or a lxml.etree.XPath')


def eval_xpath(element: ElementBase, xpath_spec: XPathSpecType):
    """Equivalent of element.xpath(xpath_str) but compile xpath_str once for all.
    See https://lxml.de/xpathxslt.html#xpath-return-values

    Args:
        * element (ElementBase): [description]
        * xpath_spec (str|lxml.etree.XPath): XPath as a str or lxml.etree.XPath

    Returns:
        * result (bool, float, list, str): Results.

    Raises:
        * TypeError: Raise when xpath_spec is neither a str nor a lxml.etree.XPath
        * SearxXPathSyntaxException: Raise when there is a syntax error in the XPath
        * SearxEngineXPathException: Raise when the XPath can't be evaluated.
    """
    xpath = get_xpath(xpath_spec)
    try:
        return xpath(element)
    except XPathError as e:
        arg = ' '.join([str(i) for i in e.args])
        raise SearxEngineXPathException(xpath_spec, arg) from e


def eval_xpath_list(element: ElementBase, xpath_spec: XPathSpecType, min_len: Optional[int] = None):
    """Same as eval_xpath, check if the result is a list

    Args:
        * element (ElementBase): [description]
        * xpath_spec (str|lxml.etree.XPath): XPath as a str or lxml.etree.XPath
        * min_len (int, optional): [description]. Defaults to None.

    Raises:
        * TypeError: Raise when xpath_spec is neither a str nor a lxml.etree.XPath
        * SearxXPathSyntaxException: Raise when there is a syntax error in the XPath
        * SearxEngineXPathException: raise if the result is not a list

    Returns:
        * result (bool, float, list, str): Results.
    """
    result = eval_xpath(element, xpath_spec)
    if not isinstance(result, list):
        raise SearxEngineXPathException(xpath_spec, 'the result is not a list')
    if min_len is not None and min_len > len(result):
        raise SearxEngineXPathException(xpath_spec, 'len(xpath_str) < ' + str(min_len))
    return result


def eval_xpath_getindex(elements: ElementBase, xpath_spec: XPathSpecType, index: int, default=_NOTSET):
    """Call eval_xpath_list then get one element using the index parameter.
    If the index does not exist, either aise an exception is default is not set,
    other return the default value (can be None).

    Args:
        * elements (ElementBase): lxml element to apply the xpath.
        * xpath_spec (str|lxml.etree.XPath): XPath as a str or lxml.etree.XPath.
        * index (int): index to get
        * default (Object, optional): Defaults if index doesn't exist.

    Raises:
        * TypeError: Raise when xpath_spec is neither a str nor a lxml.etree.XPath
        * SearxXPathSyntaxException: Raise when there is a syntax error in the XPath
        * SearxEngineXPathException: if the index is not found. Also see eval_xpath.

    Returns:
        * result (bool, float, list, str): Results.
    """
    result = eval_xpath_list(elements, xpath_spec)
    if -len(result) <= index < len(result):
        return result[index]
    if default == _NOTSET:
        # raise an SearxEngineXPathException instead of IndexError
        # to record xpath_spec
        raise SearxEngineXPathException(xpath_spec, 'index ' + str(index) + ' not found')
    return default


def _get_fasttext_model() -> "fasttext.FastText._FastText":
    global _FASTTEXT_MODEL  # pylint: disable=global-statement
    if _FASTTEXT_MODEL is None:
        import fasttext  # pylint: disable=import-outside-toplevel

        # Monkey patch: prevent fasttext from showing a (useless) warning when loading a model.
        fasttext.FastText.eprint = lambda x: None
        _FASTTEXT_MODEL = fasttext.load_model(str(data_dir / 'lid.176.ftz'))
    return _FASTTEXT_MODEL


def detect_language(text: str, threshold: float = 0.3, only_search_languages: bool = False) -> Optional[str]:
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
       (fastext) and ISO-639-2 (SearXNG)handling.  Further more, in SearXNG the
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
        raise ValueError('text must a str')
    r = _get_fasttext_model().predict(text.replace('\n', ' '), k=1, threshold=threshold)
    if isinstance(r, tuple) and len(r) == 2 and len(r[0]) > 0 and len(r[1]) > 0:
        language = r[0][0].split('__label__')[1]
        if only_search_languages and language not in SEARCH_LANGUAGE_CODES:
            return None
        return language
    return None
