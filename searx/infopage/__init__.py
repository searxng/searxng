# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pyright: basic
"""Render SearXNG instance documentation.

Usage in a Flask app route:

.. code:: python

  from searx import infopage

  _INFO_PAGES = infopage.InfoPageSet(infopage.MistletoePage)

  @app.route('/info/<pagename>', methods=['GET'])
  def info(pagename):

      locale = request.preferences.get_value('locale')
      page = _INFO_PAGES.get_page(pagename, locale)

"""

__all__ = ['InfoPage', 'InfoPageSet']

import os
import os.path
import logging
import typing

import urllib.parse
import jinja2
from flask.helpers import url_for
from markdown_it import MarkdownIt

from .. import get_setting
from ..compat import cached_property
from ..version import GIT_URL
from ..locales import LOCALE_NAMES


logger = logging.getLogger('searx.infopage')
_INFO_FOLDER = os.path.abspath(os.path.dirname(__file__))


class InfoPage:
    """A page of the :py:obj:`online documentation <InfoPageSet>`."""

    def __init__(self, fname):
        self.fname = fname

    @cached_property
    def raw_content(self):
        """Raw content of the page (without any jinja rendering)"""
        with open(self.fname, 'r', encoding='utf-8') as f:
            return f.read()

    @cached_property
    def content(self):
        """Content of the page (rendered in a Jinja conntext)"""
        ctx = self.get_ctx()
        template = jinja2.Environment().from_string(self.raw_content)
        return template.render(**ctx)

    @cached_property
    def title(self):
        """Title of the content (without any markup)"""
        t = ""
        for l in self.raw_content.split('\n'):
            if l.startswith('# '):
                t = l.strip('# ')
        return t

    @cached_property
    def html(self):
        """Render Markdown (CommonMark_) to HTML by using markdown-it-py_.

        .. _CommonMark: https://commonmark.org/
        .. _markdown-it-py: https://github.com/executablebooks/markdown-it-py

        """
        return (
            MarkdownIt("commonmark", {"typographer": True}).enable(["replacements", "smartquotes"]).render(self.content)
        )

    def get_ctx(self):
        """Jinja context to render :py:obj:`InfoPage.content`"""

        def _md_link(name, url):
            url = url_for(url, _external=True)
            return "[%s](%s)" % (name, url)

        def _md_search(query):
            url = '%s?q=%s' % (url_for('search', _external=True), urllib.parse.quote(query))
            return '[%s](%s)' % (query, url)

        ctx = {}
        ctx['GIT_URL'] = GIT_URL
        ctx['get_setting'] = get_setting
        ctx['link'] = _md_link
        ctx['search'] = _md_search

        return ctx

    def __repr__(self):
        return f'<{self.__class__.__name__} fname={self.fname!r}>'


class InfoPageSet:  # pylint: disable=too-few-public-methods
    """Cached rendering of the online documentation a SearXNG instance has.

    :param page_class: render online documentation by :py:obj:`InfoPage` parser.
    :type page_class: :py:obj:`InfoPage`

    :param info_folder: information directory
    :type info_folder: str
    """

    def __init__(
        self, page_class: typing.Optional[typing.Type[InfoPage]] = None, info_folder: typing.Optional[str] = None
    ):
        self.page_class = page_class or InfoPage
        self.folder: str = info_folder or _INFO_FOLDER
        """location of the Markdwon files"""

        self.CACHE: typing.Dict[tuple, typing.Optional[InfoPage]] = {}

        self.locale_default: str = 'en'
        """default language"""

        self.locales: typing.List[str] = [
            locale.replace('_', '-') for locale in os.listdir(_INFO_FOLDER) if locale.replace('_', '-') in LOCALE_NAMES
        ]
        """list of supported languages (aka locales)"""

        self.toc: typing.List[str] = [
            'search-syntax',
            'about',
            'donate',
        ]
        """list of articles in the online documentation"""

    def get_page(self, pagename: str, locale: typing.Optional[str] = None):
        """Return ``pagename`` instance of :py:obj:`InfoPage`

        :param pagename: name of the page, a value from :py:obj:`InfoPageSet.toc`
        :type pagename: str

        :param locale: language of the page, e.g. ``en``, ``zh_Hans_CN``
                       (default: :py:obj:`InfoPageSet.i18n_origin`)
        :type locale: str

        """
        locale = locale or self.locale_default

        if pagename not in self.toc:
            return None
        if locale not in self.locales:
            return None

        cache_key = (pagename, locale)

        if cache_key in self.CACHE:
            return self.CACHE[cache_key]

        # not yet instantiated

        fname = os.path.join(self.folder, locale.replace('-', '_'), pagename) + '.md'
        if not os.path.exists(fname):
            logger.info('file %s does not exists', fname)
            self.CACHE[cache_key] = None
            return None

        page = self.page_class(fname)
        self.CACHE[cache_key] = page
        return page

    def iter_pages(self, locale: typing.Optional[str] = None, fallback_to_default=False):
        """Iterate over all pages of the TOC"""
        locale = locale or self.locale_default
        for page_name in self.toc:
            page_locale = locale
            page = self.get_page(page_name, locale)
            if fallback_to_default and page is None:
                page_locale = self.locale_default
                page = self.get_page(page_name, self.locale_default)
            if page is not None:
                # page is None if the page was deleted by the administrator
                yield page_name, page_locale, page
