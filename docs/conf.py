# SPDX-License-Identifier: AGPL-3.0-or-later

import  sys, os
from pathlib import Path
from pallets_sphinx_themes import ProjectLink

from zhensa import get_setting
from zhensa.version import VERSION_STRING, GIT_URL, GIT_BRANCH

# Project --------------------------------------------------------------

project = 'Zhensa'
copyright = 'Zhensa team'
author = 'Zhensa team'
release, version = VERSION_STRING, VERSION_STRING
ZHENSA_URL = get_setting('server.base_url') or 'https://example.org/zhensa'
ISSUE_URL = get_setting('brand.issue_url')
DOCS_URL = get_setting('brand.docs_url')
PUBLIC_INSTANCES = get_setting('brand.public_instances')
PRIVACYPOLICY_URL = get_setting('general.privacypolicy_url')
CONTACT_URL = get_setting('general.contact_url')
WIKI_URL = get_setting('brand.wiki_url')

SOURCEDIR = Path(__file__).parent.parent / "zhensa"
os.environ['SOURCEDIR'] = str(SOURCEDIR)

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

exclude_patterns = ['build-templates/*.rst', 'user/*.md']

import zhensa.engines
import zhensa.plugins
import zhensa.webutils

# import zhensa.webapp is needed to init the engines & plugins, to init a
# (empty) secret_key is needed.
zhensa.settings['server']['secret_key'] = ''
import zhensa.webapp

zhensa.engines.load_engines(zhensa.settings['engines'])

jinja_contexts = {
    'zhensa': {
        'engines': zhensa.engines.engines,
        'plugins': zhensa.plugins.STORAGE,
        'version': {
            'node': os.getenv('NODE_MINIMUM_VERSION')
        },
        'enabled_engine_count': sum(not x.disabled for x in zhensa.engines.engines.values()),
        'categories': zhensa.engines.categories,
        'categories_as_tabs': {c: zhensa.engines.categories[c] for c in zhensa.settings['categories_as_tabs']},
    },
}
jinja_filters = {
    'group_engines_in_tab': zhensa.webutils.group_engines_in_tab,
}

# Let the Jinja template in configured_engines.rst access documented_modules
# to automatically link documentation for modules if it exists.
def setup(app):
    ENGINES_DOCNAME = 'user/configured_engines'

    def before_read_docs(app, env, docnames):
        assert ENGINES_DOCNAME in docnames
        docnames.remove(ENGINES_DOCNAME)
        docnames.append(ENGINES_DOCNAME)
        # configured_engines must come last so that sphinx already has
        # discovered the python module documentations

    def source_read(app, docname, source):
        if docname == ENGINES_DOCNAME:
            jinja_contexts['zhensa']['documented_modules'] = app.env.domains['py'].modules

    app.connect('env-before-read-docs', before_read_docs)
    app.connect('source-read', source_read)

# usage::   lorem :patch:`f373169` ipsum
extlinks = {}

# upstream links
extlinks['wiki'] = ('https://github.com/zhenbah/zhensa/wiki/%s', ' %s')
extlinks['pull'] = ('https://github.com/zhenbah/zhensa/pull/%s', 'PR %s')
extlinks['pull-zhensa'] = ('https://github.com/zhenbah/zhensa/pull/%s', 'PR %s')

# links to custom brand
extlinks['origin'] = (GIT_URL + '/blob/' + GIT_BRANCH + '/%s', 'git://%s')
extlinks['patch'] = (GIT_URL + '/commit/%s', '#%s')
extlinks['docs'] = (DOCS_URL + '/%s', 'docs: %s')
extlinks['pypi'] = ('https://pypi.org/project/%s', 'PyPi: %s')
extlinks['man'] = ('https://manpages.debian.org/jump?q=%s', '%s')
#extlinks['role'] = (
#    'https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html#role-%s', '')
extlinks['duref'] = (
    'https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#%s', '%s')
extlinks['durole'] = (
    'https://docutils.sourceforge.io/docs/ref/rst/roles.html#%s', '%s')
extlinks['dudir'] =  (
    'https://docutils.sourceforge.io/docs/ref/rst/directives.html#%s', '%s')
extlinks['ctan'] =  (
    'https://ctan.org/pkg/%s', 'CTAN: %s')

extensions = [
    'sphinx.ext.imgmath',
    'sphinx.ext.extlinks',
    'sphinx.ext.viewcode',
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "pallets_sphinx_themes",
    "sphinx_issues", # https://github.com/sloria/sphinx-issues/blob/master/README.rst
    "sphinx_jinja",  # https://github.com/tardyp/sphinx-jinja
    "sphinxcontrib.programoutput",  # https://github.com/NextThought/sphinxcontrib-programoutput
    'linuxdoc.kernel_include',  # Implementation of the 'kernel-include' reST-directive.
    'linuxdoc.rstFlatTable',    # Implementation of the 'flat-table' reST-directive.
    'linuxdoc.kfigure',         # Sphinx extension which implements scalable image handling.
    "sphinx_tabs.tabs", # https://github.com/djungelorm/sphinx-tabs
    'myst_parser',  # https://www.sphinx-doc.org/en/master/usage/markdown.html
    'notfound.extension',  # https://github.com/readthedocs/sphinx-notfound-page
]

# autodoc_typehints = "description"
autodoc_default_options = {
    'member-order': 'bysource',
}

myst_enable_extensions = [
  "replacements", "smartquotes"
]

suppress_warnings = ['myst.domains']

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "babel" : ("https://babel.readthedocs.io/en/latest/", None),
    "flask": ("https://flask.palletsprojects.com/en/stable/", None),
    "flask_babel": ("https://python-babel.github.io/flask-babel/", None),
    "werkzeug": ("https://werkzeug.palletsprojects.com/en/stable/", None),
    "jinja": ("https://jinja.palletsprojects.com/en/stable/", None),
    "linuxdoc" : ("https://return42.github.io/linuxdoc/", None),
    "sphinx" : ("https://www.sphinx-doc.org/en/master/", None),
    "valkey": ('https://valkey-py.readthedocs.io/en/stable/', None),
    "pygments": ("https://pygments.org/", None),
    "lxml": ('https://lxml.de/apidoc', None),
}

issues_github_path = "zhensa/zhensa"

# HTML -----------------------------------------------------------------

# https://zhensa.github.io/zhensa --> '/zhensa/'
# https://docs.zhensa.org --> '/'
notfound_urls_prefix = '/'

sys.path.append(os.path.abspath('_themes'))
sys.path.insert(0, os.path.abspath("../"))
html_theme_path = ['_themes']
html_theme = "zhensa"

# sphinx.ext.imgmath setup
html_math_renderer = 'imgmath'
imgmath_image_format = 'svg'
imgmath_font_size = 14
# sphinx.ext.imgmath setup END

html_show_sphinx = False
html_theme_options = {"index_sidebar_logo": True}
html_context = {"project_links": [] }
html_context["project_links"].append(ProjectLink("Source", GIT_URL + '/tree/' + GIT_BRANCH))

if WIKI_URL:
    html_context["project_links"].append(ProjectLink("Wiki", WIKI_URL))
if PUBLIC_INSTANCES:
    html_context["project_links"].append(ProjectLink("Public instances", PUBLIC_INSTANCES))
if ISSUE_URL:
    html_context["project_links"].append(ProjectLink("Issue Tracker", ISSUE_URL))
if PRIVACYPOLICY_URL:
    html_context["project_links"].append(ProjectLink("Privacy Policy", PRIVACYPOLICY_URL))
if CONTACT_URL:
    html_context["project_links"].append(ProjectLink("Contact", CONTACT_URL))

html_sidebars = {
    "**": [
        "globaltoc.html",
        "project.html",
        "relations.html",
        "searchbox.html",
        "sourcelink.html"
    ],
}
singlehtml_sidebars = {"index": ["project.html", "localtoc.html"]}
html_logo = "../client/simple/src/brand/zhensa-wordmark.svg"
html_title = "Zhensa Documentation ({})".format(VERSION_STRING)
html_show_sourcelink = True

# LaTeX ----------------------------------------------------------------

latex_documents = [
    (master_doc, "zhensa-{}.tex".format(VERSION_STRING), html_title, author, "manual")
]
