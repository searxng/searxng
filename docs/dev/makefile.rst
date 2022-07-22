.. _makefile:

========
Makefile
========

.. _gnu-make: https://www.gnu.org/software/make/manual/make.html#Introduction

.. sidebar:: build environment

   Before looking deeper at the targets, first read about :ref:`make
   install`.

   To install system requirements follow :ref:`buildhosts`.

All relevant build tasks are implemented in :origin:`manage` and for CI or
IDE integration a small ``Makefile`` wrapper is available.  If you are not
familiar with Makefiles, we recommend to read gnu-make_ introduction.

The usage is simple, just type ``make {target-name}`` to *build* a target.
Calling the ``help`` target gives a first overview (``make help``):

.. program-output:: bash -c "cd ..; make --no-print-directory help"

.. contents:: Contents
   :depth: 2
   :local:
   :backlinks: entry

.. _make install:

Python environment (``make install``)
=====================================

.. sidebar:: activate environment

   ``source ./local/py3/bin/activate``

We do no longer need to build up the virtualenv manually.  Jump into your git
working tree and release a ``make install`` to get a virtualenv with a
*developer install* of SearXNG (:origin:`setup.py`). ::

   $ cd ~/searxng-clone
   $ make install
   PYENV     [virtualenv] installing ./requirements*.txt into local/py3
   ...
   PYENV     OK
   PYENV     [install] pip install -e 'searx[test]'
   ...
   Successfully installed argparse-1.4.0 searx
   BUILDENV  INFO:searx:load the default settings from ./searx/settings.yml
   BUILDENV  INFO:searx:Initialisation done
   BUILDENV  build utils/brand.env

If you release ``make install`` multiple times the installation will only
rebuild if the sha256 sum of the *requirement files* fails.  With other words:
the check fails if you edit the requirements listed in
:origin:`requirements-dev.txt` and :origin:`requirements.txt`). ::

   $ make install
   PYENV     OK
   PYENV     [virtualenv] requirements.sha256 failed
             [virtualenv] - 6cea6eb6def9e14a18bf32f8a3e...  ./requirements-dev.txt
             [virtualenv] - 471efef6c73558e391c3adb35f4...  ./requirements.txt
   ...
   PYENV     [virtualenv] installing ./requirements*.txt into local/py3
   ...
   PYENV     OK
   PYENV     [install] pip install -e 'searx[test]'
   ...
   Successfully installed argparse-1.4.0 searx
   BUILDENV  INFO:searx:load the default settings from ./searx/settings.yml
   BUILDENV  INFO:searx:Initialisation done
   BUILDENV  build utils/brand.env

.. sidebar:: drop environment

   To get rid of the existing environment before re-build use :ref:`clean target
   <make clean>` first.

If you think, something goes wrong with your ./local environment or you change
the :origin:`setup.py` file, you have to call :ref:`make clean`.

.. _make buildenv:

``make buildenv``
=================

Rebuild instance's environment with the modified settings from the
:ref:`settings brand` and :ref:`settings server` section of your
:ref:`settings.yml <settings location>`.

We have all SearXNG setups are centralized in the :ref:`settings.yml` file.
This setup is available as long we are in a *installed instance*.  E.g. the
*installed instance* on the server or the *installed developer instance* at
``./local`` (the later one is created by a :ref:`make install <make
install>` or :ref:`make run <make run>`).

Tasks running outside of an *installed instance*, especially those tasks and
scripts running at (pre-) installation time do not have access to the SearXNG
setup (from a *installed instance*).  Those tasks need a *build environment*.

The ``make buildenv`` target will update the *build environment* in:

- :origin:`utils/brand.env`

Tasks running outside of an *installed instance*, need the following settings
from the YAML configuration:

- ``SEARXNG_URL`` from :ref:`server.base_url <settings  server>` (aka
  ``PUBLIC_URL``)
- ``SEARXNG_BIND_ADDRESS`` from :ref:`server.bind_address <settings server>`
- ``SEARXNG_PORT`` from :ref:`server.port <settings server>`

.. _make node.env:

Node.js environment (``make node.env``)
=======================================

.. _Node.js: https://nodejs.org/
.. _nvm: https://github.com/nvm-sh
.. _npm: https://www.npmjs.com/

.. jinja:: searx

   Node.js_ version {{version.node}} or higher is required to build the themes.
   If the requirement is not met, the build chain uses nvm_ (Node Version
   Manager) to install latest LTS of Node.js_ locally: there is no need to
   install nvm_ or npm_ on your system.

Use ``make nvm.status`` to get the current status of you Node.js_ and nvm_ setup.

Here is the output you will typically get on a Ubuntu 20.04 system which serves
only a `no longer active <https://nodejs.org/en/about/releases/>`_ Release
`Node.js v10.19.0 <https://packages.ubuntu.com/focal/nodejs>`_.

::

  $ make nvm.status
  INFO:  Node.js is installed at /usr/bin/node
  INFO:  Node.js is version v10.19.0
  WARN:  minimal Node.js version is 16.13.0
  INFO:  npm is installed at /usr/bin/npm
  INFO:  npm is version 6.14.4
  WARN:  NVM is not installed
  INFO:  to install NVM and Node.js (LTS) use: manage nvm install --lts

To install you can also use :ref:`make nvm.nodejs`

.. _make nvm.nodejs:

``make nvm.nodejs``
===================

Install latest Node.js_ LTS locally (uses nvm_)::

  $ make nvm.nodejs
  INFO:  install (update) NVM at /share/searxng/.nvm
  INFO:  clone: https://github.com/nvm-sh/nvm.git
  ...
  Downloading and installing node v16.13.0...
  ...
  INFO:  Node.js is installed at searxng/.nvm/versions/node/v16.13.0/bin/node
  INFO:  Node.js is version v16.13.0
  INFO:  npm is installed at searxng/.nvm/versions/node/v16.13.0/bin/npm
  INFO:  npm is version 8.1.0
  INFO:  NVM is installed at searxng/.nvm

.. _make run:

``make run``
============

To get up a running a developer instance simply call ``make run``.  This enables
*debug* option in :origin:`searx/settings.yml`, starts a ``./searx/webapp.py``
instance and opens the URL in your favorite WEB browser (:man:`xdg-open`)::

   $ make run

Changes to theme's HTML templates (jinja2) are instant.  Changes to the CSS & JS
sources of the theme need to be rebuild.  You can do that by running::

  $ make themes.all

Alternatively to ``themes.all`` you can run *live builds* of the theme you are
modify::

  $ LIVE_THEME=simple make run

.. _make clean:

``make clean``
==============

Drops all intermediate files, all builds, but keep sources untouched.  Before
calling ``make clean`` stop all processes using the :ref:`make install` or
:ref:`make node.env`. ::

   $ make clean
   CLEAN     pyenv
   PYENV     [virtualenv] drop local/py3
   CLEAN     docs -- build/docs dist/docs
   CLEAN     themes -- locally installed npm dependencies
   ...
   CLEAN     test stuff
   CLEAN     common files

.. _make docs:

``make docs docs.autobuild docs.clean``
=======================================

We describe the usage of the ``doc.*`` targets in the :ref:`How to contribute /
Documentation <contrib docs>` section.  If you want to edit the documentation
read our :ref:`make docs.live` section.  If you are working in your own brand,
adjust your :ref:`settings global`.

.. _make docs.gh-pages:

``make docs.gh-pages``
======================

To deploy on github.io first adjust your :ref:`settings global`.  For any
further read :ref:`deploy on github.io`.

.. _make test:

``make test``
=============

Runs a series of tests: :ref:`make test.pylint`, ``test.pep8``, ``test.unit``
and ``test.robot``.  You can run tests selective, e.g.::

  $ make test.pep8 test.unit test.sh
  TEST      test.pep8 OK
  ...
  TEST      test.unit OK
  ...
  TEST      test.sh OK

.. _make test.shell:

``make test.shell``
===================

:ref:`sh lint` / if you have changed some bash scripting run this test before
commit.

.. _make test.pylint:

``make test.pylint``
====================

.. _Pylint: https://www.pylint.org/

Pylint_ is known as one of the best source-code, bug and quality checker for the
Python programming language.  The pylint profile used in the SearXNG project is
found in project's root folder :origin:`.pylintrc`.

.. _make search.checker:

``search.checker.{engine name}``
================================

To check all engines::

    make search.checker

To check a engine with whitespace in the name like *google news* replace space
by underline::

    make search.checker.google_news

To see HTTP requests and more use SEARXNG_DEBUG::

    make SEARXNG_DEBUG=1 search.checker.google_news

.. _3xx: https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#3xx_redirection

To filter out HTTP redirects (3xx_)::

    make SEARXNG_DEBUG=1 search.checker.google_news | grep -A1 "HTTP/1.1\" 3[0-9][0-9]"
    ...
    Engine google news                   Checking
    https://news.google.com:443 "GET /search?q=life&hl=en&lr=lang_en&ie=utf8&oe=utf8&ceid=US%3Aen&gl=US HTTP/1.1" 302 0
    https://news.google.com:443 "GET /search?q=life&hl=en-US&lr=lang_en&ie=utf8&oe=utf8&ceid=US:en&gl=US HTTP/1.1" 200 None
    --
    https://news.google.com:443 "GET /search?q=computer&hl=en&lr=lang_en&ie=utf8&oe=utf8&ceid=US%3Aen&gl=US HTTP/1.1" 302 0
    https://news.google.com:443 "GET /search?q=computer&hl=en-US&lr=lang_en&ie=utf8&oe=utf8&ceid=US:en&gl=US HTTP/1.1" 200 None
    --
