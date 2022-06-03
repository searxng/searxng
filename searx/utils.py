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
from babel.core import get_global


from searx import settings
from searx.data import USER_AGENTS
from searx.version import VERSION_TAG
from searx.languages import language_codes
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


class _NotSetClass:  # pylint: disable=too-few-public-methods
    """Internal class for this module, do not create instance of this class.
    Replace the None value, allow explicitly pass None as a function argument"""


_NOTSET = _NotSetClass()


def searx_useragent() -> str:
    """Return the searx User Agent"""
    return 'searx/{searx_version} {suffix}'.format(
        searx_version=VERSION_TAG, suffix=settings['outgoing']['useragent_suffix']
    ).strip()


def gen_useragent(os_string: str = None) -> str:
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


def dict_subset(dictionnary: MutableMapping, properties: Set[str]) -> Dict:
    """Extract a subset of a dict

    Examples:
        >>> dict_subset({'A': 'a', 'B': 'b', 'C': 'c'}, ['A', 'C'])
        {'A': 'a', 'C': 'c'}
        >>> >> dict_subset({'A': 'a', 'B': 'b', 'C': 'c'}, ['A', 'D'])
        {'A': 'a'}
    """
    return {k: dictionnary[k] for k in properties if k in dictionnary}


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
        for l in language_codes:
            if l[0][:2] == lang:
                return (True, l[0][:2], l[3].lower())
        return None
    for l in language_codes:
        if l[1].lower() == lang or l[3].lower() == lang:
            return (True, l[0][:2], l[3].lower())
    return None


def _get_lang_to_lc_dict(lang_list: List[str]) -> Dict[str, str]:
    key = str(lang_list)
    value = _LANG_TO_LC_CACHE.get(key, None)
    if value is None:
        value = {}
        for lang in lang_list:
            value.setdefault(lang.split('-')[0], lang)
        _LANG_TO_LC_CACHE[key] = value
    return value


# babel's get_global contains all sorts of miscellaneous locale and territory related data
# see get_global in: https://github.com/python-babel/babel/blob/master/babel/core.py
def _get_from_babel(lang_code: str, key):
    match = get_global(key).get(lang_code.replace('-', '_'))
    # for some keys, such as territory_aliases, match may be a list
    if isinstance(match, str):
        return match.replace('_', '-')
    return match


def _match_language(lang_code: str, lang_list=[], custom_aliases={}) -> Optional[str]:  # pylint: disable=W0102
    """auxiliary function to match lang_code in lang_list"""
    # replace language code with a custom alias if necessary
    if lang_code in custom_aliases:
        lang_code = custom_aliases[lang_code]

    if lang_code in lang_list:
        return lang_code

    # try to get the most likely country for this language
    subtags = _get_from_babel(lang_code, 'likely_subtags')
    if subtags:
        if subtags in lang_list:
            return subtags
        subtag_parts = subtags.split('-')
        new_code = subtag_parts[0] + '-' + subtag_parts[-1]
        if new_code in custom_aliases:
            new_code = custom_aliases[new_code]
        if new_code in lang_list:
            return new_code

    # try to get the any supported country for this language
    return _get_lang_to_lc_dict(lang_list).get(lang_code)


def match_language(  # pylint: disable=W0102
    locale_code, lang_list=[], custom_aliases={}, fallback: Optional[str] = 'en-US'
) -> Optional[str]:
    """get the language code from lang_list that best matches locale_code"""
    # try to get language from given locale_code
    language = _match_language(locale_code, lang_list, custom_aliases)
    if language:
        return language

    locale_parts = locale_code.split('-')
    lang_code = locale_parts[0]

    # if locale_code has script, try matching without it
    if len(locale_parts) > 2:
        language = _match_language(lang_code + '-' + locale_parts[-1], lang_list, custom_aliases)
        if language:
            return language

    # try to get language using an equivalent country code
    if len(locale_parts) > 1:
        country_alias = _get_from_babel(locale_parts[-1], 'territory_aliases')
        if country_alias:
            language = _match_language(lang_code + '-' + country_alias[0], lang_list, custom_aliases)
            if language:
                return language

    # try to get language using an equivalent language code
    alias = _get_from_babel(lang_code, 'language_aliases')
    if alias:
        language = _match_language(alias, lang_list, custom_aliases)
        if language:
            return language

    if lang_code != locale_code:
        # try to get language from given language without giving the country
        language = _match_language(lang_code, lang_list, custom_aliases)

    return language or fallback


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


def eval_xpath_list(element: ElementBase, xpath_spec: XPathSpecType, min_len: int = None):
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
