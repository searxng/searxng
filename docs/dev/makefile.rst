.. _makefile:

=======================
Makefile & ``./manage``
=======================

.. _gnu-make: https://www.gnu.org/software/make/manual/make.html#Introduction

All relevant build and development tasks are implemented in the
:origin:`./manage <manage>` script and for CI or IDE integration a small
:origin:`Makefile` wrapper is available.  If you are not familiar with
Makefiles, we recommend to read gnu-make_ introduction.

.. sidebar:: build environment

   Before looking deeper at the targets, first read about :ref:`make
   install`.

   To install developer requirements follow :ref:`buildhosts`.


.. contents::
   :depth: 2
   :local:
   :backlinks: entry

The usage is simple, just type ``make {target-name}`` to *build* a target.
Calling the ``help`` target gives a first overview (``make help``):

.. tabs::

  .. group-tab:: ``make``

     .. program-output:: bash -c "cd ..; make --no-print-directory help"


  .. group-tab:: ``./manage``

     The Makefile targets are implemented for comfort, if you can do without
     tab-completion and need to have a more granular control, use
     :origin:`manage` without the Makefile wrappers.

     .. code:: sh

        $ ./manage help

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
   PYENV     [install] pip install -e 'searx[test]'
   ...
   Successfully installed searxng-2023.7.19+a446dea1b

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
   PYENV     [install] pip install -e 'searx[test]'
   ...
   Successfully installed searxng-2023.7.19+a446dea1b

.. sidebar:: drop environment

   To get rid of the existing environment before re-build use :ref:`clean target
   <make clean>` first.

If you think, something goes wrong with your ./local environment or you change
the :origin:`setup.py` file, you have to call :ref:`make clean`.

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

To install NVM_ and Node.js_ in once you can use :ref:`make nvm.nodejs`.

.. _make nvm:

NVM ``make nvm.install nvm.status``
-----------------------------------

Use ``make nvm.status`` to get the current status of your Node.js_ and nvm_
setup.

.. tabs::

  .. group-tab:: nvm.install

     .. code:: sh

        $ LANG=C make nvm.install
        INFO:  install (update) NVM at ./searxng/.nvm
        INFO:  clone: https://github.com/nvm-sh/nvm.git
          || Cloning into './searxng/.nvm'...
        INFO:  checkout v0.39.4
          || HEAD is now at 8fbf8ab v0.39.4

  .. group-tab:: nvm.status (ubu2004)

     Here is the output you will typically get on a Ubuntu 20.04 system which
     serves only a `no longer active <https://nodejs.org/en/about/releases/>`_
     Release `Node.js v10.19.0 <https://packages.ubuntu.com/focal/nodejs>`_.

     .. code:: sh

        $ make nvm.status
        INFO:  Node.js is installed at /usr/bin/node
        INFO:  Node.js is version v10.19.0
        WARN:  minimal Node.js version is 16.13.0
        INFO:  npm is installed at /usr/bin/npm
        INFO:  npm is version 6.14.4
        WARN:  NVM is not installed

.. _make nvm.nodejs:

``make nvm.nodejs``
-------------------

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
modify (:ref:`make themes`)::

  $ LIVE_THEME=simple make run

.. _make format.python:

``make format.python``
======================

Format Python source code using `Black code style`_.  See ``$BLACK_OPTIONS``
and ``$BLACK_TARGETS`` in :origin:`Makefile`.

.. attention::

   We stuck at Black 22.12.0, please read comment in PR `Bump black from 22.12.0
   to 23.1.0`_

.. _Bump black from 22.12.0 to 23.1.0:
   https://github.com/searxng/searxng/pull/2159#pullrequestreview-1284094735

.. _Black code style:
   https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html

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

``make docs``
=============

Target ``docs`` builds the documentation:

.. code:: bash

   $ make docs
   HTML ./docs --> file://
   DOCS      build build/docs/includes
   ...
   The HTML pages are in dist/docs.

.. _make docs.clean:

``make docs.clean docs.live``
----------------------------------

We describe the usage of the ``doc.*`` targets in the :ref:`How to contribute /
Documentation <contrib docs>` section.  If you want to edit the documentation
read our :ref:`make docs.live` section.  If you are working in your own brand,
adjust your :ref:`settings brand`.


.. _make docs.gh-pages:

``make docs.gh-pages``
----------------------

To deploy on github.io first adjust your :ref:`settings brand`.  For any
further read :ref:`deploy on github.io`.

.. _make test:

``make test``
=============

Runs a series of tests: :ref:`make test.pylint`, ``test.pep8``, ``test.unit``
and ``test.robot``.  You can run tests selective, e.g.::

  $ make test.pep8 test.unit test.shell
  TEST      test.pep8 OK
  ...
  TEST      test.unit OK
  ...
  TEST      test.shell OK

.. _make test.shell:

``make test.shell``
-------------------

:ref:`sh lint` / if you have changed some bash scripting run this test before
commit.

.. _make test.pylint:

``make test.pylint``
--------------------

.. _Pylint: https://www.pylint.org/

Pylint_ is known as one of the best source-code, bug and quality checker for the
Python programming language.  The pylint profile used in the SearXNG project is
found in project's root folder :origin:`.pylintrc`.

.. _make search.checker:

``make search.checker.{engine name}``
=====================================

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

.. _make themes:

``make themes.*``
=================

.. sidebar:: further read

   - :ref:`devquickstart`

The :origin:`Makefile` targets ``make theme.*`` cover common tasks to build the
theme(s).  The ``./manage themes.*`` command line can be used to convenient run
common theme build tasks.

.. program-output:: bash -c "cd ..; ./manage themes.help"

To get live builds while modifying CSS & JS use (:ref:`make run`):

.. code:: sh

   $ LIVE_THEME=simple make run

.. _make static.build:

``make static.build.*``
=======================

.. sidebar:: further read

   - :ref:`devquickstart`

The :origin:`Makefile` targets ``static.build.*`` cover common tasks to build (a
commit of) the static files.  The ``./manage static.build..*`` command line
can be used to convenient run common build tasks of the static files.

.. program-output:: bash -c "cd ..; ./manage static.help"


.. _manage redis.help:

``./manage redis.help``
=======================

The ``./manage redis.*`` command line can be used to convenient run common Redis
tasks (:ref:`Redis developer notes`).

.. program-output:: bash -c "cd ..; ./manage redis.help"


.. _manage go.help:

``./manage go.help``
====================

The ``./manage go.*`` command line can be used to convenient run common `go
(wiki)`_ tasks.

.. _go (wiki): https://en.wikipedia.org/wiki/Go_(programming_language)

.. program-output:: bash -c "cd ..; ./manage go.help"
