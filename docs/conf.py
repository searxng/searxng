# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later

import  sys, os
from pallets_sphinx_themes import ProjectLink

from searx import get_setting
from searx.version import VERSION_STRING, GIT_URL, GIT_BRANCH

# Project --------------------------------------------------------------

project = 'SearXNG'
copyright = '2021 SearXNG team, 2015-2021 Adam Tauber, Noémi Ványi'
author = '2021 SearXNG team, 2015-2021 Adam Tauber'
release, version = VERSION_STRING, VERSION_STRING

SEARX_URL = get_setting('server.base_url') or 'https://example.org/searx'
ISSUE_URL = get_setting('brand.issue_url')
DOCS_URL = get_setting('brand.docs_url')
PUBLIC_INSTANCES = get_setting('brand.public_instances')
CONTACT_URL = get_setting('general.contact_url')
WIKI_URL = get_setting('brand.wiki_url')

# hint: sphinx.ext.viewcode won't highlight when 'highlight_language' [1] is set
#       to string 'none' [2]
#
# [1] https://www.sphinx-doc.org/en/master/usage/extensions/viewcode.html
# [2] https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-highlight_language

highlight_language = 'default'

# General --------------------------------------------------------------

master_doc = "index"
source_suffix = '.rst'
numfig = True

exclude_patterns = ['build-templates/*.rst']

import searx.engines
import searx.plugins
searx.engines.load_engines(searx.settings['engines'])
jinja_contexts = {
    'searx': {
        'engines': searx.engines.engines,
        'plugins': searx.plugins.plugins
    },
}

# usage::   lorem :patch:`f373169` ipsum
extlinks = {}

# upstream links
extlinks['wiki'] = ('https://github.com/searxng/searxng/wiki/%s', ' ')
extlinks['pull'] = ('https://github.com/searxng/searxng/pull/%s', 'PR ')
extlinks['pull-searx'] = ('https://github.com/searx/searx/pull/%s', 'PR ')

# links to custom brand
extlinks['origin'] = (GIT_URL + '/blob/' + GIT_BRANCH + '/%s', 'git://')
extlinks['patch'] = (GIT_URL + '/commit/%s', '#')
extlinks['search'] = (SEARX_URL + '/%s', '#')
extlinks['docs'] = (DOCS_URL + '/%s', 'docs: ')
extlinks['pypi'] = ('https://pypi.org/project/%s', 'PyPi: ')
extlinks['man'] = ('https://manpages.debian.org/jump?q=%s', '')
#extlinks['role'] = (
#    'https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html#role-%s', '')
extlinks['duref'] = (
    'https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#%s', '')
extlinks['durole'] = (
    'https://docutils.sourceforge.io/docs/ref/rst/roles.html#%s', '')
extlinks['dudir'] =  (
    'https://docutils.sourceforge.io/docs/ref/rst/directives.html#%s', '')
extlinks['ctan'] =  (
    'https://ctan.org/pkg/%s', 'CTAN: ')

extensions = [
    'sphinx.ext.imgmath',
    'sphinx.ext.extlinks',
    'sphinx.ext.viewcode',
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "pallets_sphinx_themes",
    "sphinx_issues", # https://github.com/sloria/sphinx-issues/blob/master/README.rst
    "sphinxcontrib.jinja",  # https://github.com/tardyp/sphinx-jinja
    "sphinxcontrib.programoutput",  # https://github.com/NextThought/sphinxcontrib-programoutput
    'linuxdoc.kernel_include',  # Implementation of the 'kernel-include' reST-directive.
    'linuxdoc.rstFlatTable',    # Implementation of the 'flat-table' reST-directive.
    'linuxdoc.kfigure',         # Sphinx extension which implements scalable image handling.
    "sphinx_tabs.tabs", # https://github.com/djungelorm/sphinx-tabs
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "flask": ("https://flask.palletsprojects.com/", None),
    # "werkzeug": ("https://werkzeug.palletsprojects.com/", None),
    "jinja": ("https://jinja.palletsprojects.com/", None),
    "linuxdoc" : ("https://return42.github.io/linuxdoc/", None),
    "sphinx" : ("https://www.sphinx-doc.org/en/master/", None),
}

issues_github_path = "searxng/searxng"

# HTML -----------------------------------------------------------------

sys.path.append(os.path.abspath('_themes'))
sys.path.insert(0, os.path.abspath("../utils/"))
html_theme_path = ['_themes']
html_theme = "searx"

# sphinx.ext.imgmath setup
html_math_renderer = 'imgmath'
imgmath_image_format = 'svg'
imgmath_font_size = 14
# sphinx.ext.imgmath setup END

html_theme_options = {"index_sidebar_logo": True}
html_context = {"project_links": [] }
html_context["project_links"].append(ProjectLink("Source", GIT_URL + '/tree/' + GIT_BRANCH))

if WIKI_URL:
    html_context["project_links"].append(ProjectLink("Wiki", WIKI_URL))
if PUBLIC_INSTANCES:
    html_context["project_links"].append(ProjectLink("Public instances", PUBLIC_INSTANCES))
if ISSUE_URL:
    html_context["project_links"].append(ProjectLink("Issue Tracker", ISSUE_URL))
if CONTACT_URL:
    html_context["project_links"].append(ProjectLink("Contact", CONTACT_URL))

html_sidebars = {
    "**": ["project.html", "relations.html", "searchbox.html"],
}
singlehtml_sidebars = {"index": ["project.html", "localtoc.html"]}
html_static_path = ["static"]
html_logo = "static/img/searx_logo_small.png"
html_title = "Searx Documentation ({})".format(VERSION_STRING)
html_show_sourcelink = False

# LaTeX ----------------------------------------------------------------

latex_documents = [
    (master_doc, "searx-{}.tex".format(VERSION_STRING), html_title, author, "manual")
]
