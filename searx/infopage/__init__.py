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

__all__ = ['InfoPage', 'MistletoePage', 'InfoPageSet']

import os.path
import logging
from functools import cached_property
import typing

import urllib.parse
import jinja2
from flask.helpers import url_for
import mistletoe

from .. import get_setting
from ..version import GIT_URL

logger = logging.getLogger('doc')


class InfoPage:
    """A page of the :py:obj:`online documentation <InfoPageSet>`."""

    def __init__(self, fname, base_url=None):
        self.fname = fname
        self.base_url = base_url

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

    def get_ctx(self):  # pylint: disable=no-self-use
        """Jinja context to render :py:obj:`InfoPage.content`"""

        def _md_link(name, url):
            url = url_for(url)
            if self.base_url:
                url = self.base_url + url
            return "[%s](%s)" % (name, url)

        def _md_search(query):
            url = '%s?q=%s' % (url_for('search'), urllib.parse.quote(query))
            if self.base_url:
                url = self.base_url + url
            return '[%s](%s)' % (query, url)

        ctx = {}
        ctx['GIT_URL'] = GIT_URL
        ctx['get_setting'] = get_setting
        ctx['link'] = _md_link
        ctx['search'] = _md_search

        return ctx

    def render(self):
        """Render / return content"""
        return self.content


class MistletoePage(InfoPage):
    """A HTML page of the :py:obj:`online documentation <InfoPageSet>`."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @cached_property
    def html(self):
        """HTML representation of this page"""
        return self.render()

    def render(self):
        """Render Markdown (CommonMark_) to HTML by using mistletoe_.

        .. _CommonMark: https://commonmark.org/
        .. _mistletoe: https://github.com/miyuchina/mistletoe

        """
        return mistletoe.markdown(self.content)


_INFO_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'info'))


class InfoPageSet:  # pylint: disable=too-few-public-methods
    """Cached rendering of the online documentation a SearXNG instance has.

    :param page_class: render online documentation by :py:obj:`InfoPage` parser.
    :type page_class: :py:obj:`InfoPage`
    """

    def __init__(self, page_class: typing.Type[InfoPage], base_url=None):
        self.page_class = page_class
        self.base_url = base_url
        self.CACHE: typing.Dict[tuple, InfoPage] = {}

        # future: could be set from settings.xml

        self.folder: str = _INFO_FOLDER
        """location of the Markdwon files"""

        self.i18n_origin: str = 'en'
        """default language"""

        self.l10n: typing.List = [
            'en',
        ]
        """list of supported languages (aka locales)"""

        self.toc: typing.List = [
            'search-syntax',
            'about',
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
        if pagename not in self.toc:
            return None
        if locale is not None and locale not in self.l10n:
            return None

        locale = locale or self.i18n_origin
        cache_key = (pagename, locale)
        page = self.CACHE.get(cache_key)

        if page is not None:
            return page

        # not yet instantiated

        fname = os.path.join(self.folder, locale, pagename) + '.md'
        if not os.path.exists(fname):
            logger.error('file %s does not exists', fname)
            return None

        page = self.page_class(fname, self.base_url)
        self.CACHE[cache_key] = page
        return page

    def all_pages(self, locale: typing.Optional[str] = None):
        """Iterate over all pages"""
        locale = locale or self.i18n_origin
        for pagename in self.toc:
            page = self.get_page(pagename, locale)
            yield pagename, page
