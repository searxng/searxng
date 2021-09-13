.. _makefile:

========
Makefile
========

.. _gnu-make: https://www.gnu.org/software/make/manual/make.html#Introduction

.. sidebar:: build environment

   Before looking deeper at the targets, first read about :ref:`make
   install`.

   To install system requirements follow :ref:`buildhosts`.

All relevant build tasks are implemented in :origin:`manage.sh` and for CI or
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

Python Environment (``make install``)
=====================================

.. sidebar:: activate environment

   ``source ./local/py3/bin/activate``

We do no longer need to build up the virtualenv manually.  Jump into your git
working tree and release a ``make install`` to get a virtualenv with a
*developer install* of SearXNG (:origin:`setup.py`). ::

   $ cd ~/searx-clone
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
:ref:`settings global brand` and :ref:`settings global server` section of your
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

- ``SEARX_URL`` from :ref:`server.base_url <settings global server>` (aka
  ``PUBLIC_URL``)
- ``SEARX_BIND_ADDRESS`` from :ref:`server.bind_address <settings global server>`
- ``SEARX_PORT`` from :ref:`server.port <settings global server>`

.. _make run:

``make run``
============

To get up a running a developer instance simply call ``make run``.  This enables
*debug* option in :origin:`searx/settings.yml`, starts a ``./searx/webapp.py``
instance, disables *debug* option again and opens the URL in your favorite WEB
browser (:man:`xdg-open`)::

   $ make run
   PYENV     OK
   SEARX_DEBUG=1 ./manage.sh pyenv.cmd python ./searx/webapp.py
   ...
   INFO:werkzeug: * Running on http://127.0.0.1:8888/ (Press CTRL+C to quit)

.. _make clean:

``make clean``
==============

Drop all intermediate files, all builds, but keep sources untouched.  Before
calling ``make clean`` stop all processes using :ref:`make install`. ::

   $ make clean
   CLEAN     pyenv
   PYENV     [virtualenv] drop ./local/py3
   CLEAN     docs -- ./build/docs ./dist/docs
   CLEAN     locally installed npm dependencies
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

.. _make test.sh:

``make test.sh``
================

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

To see HTTP requests and more use SEARX_DEBUG::

    make SEARX_DEBUG=1 search.checker.google_news

.. _3xx: https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#3xx_redirection

To filter out HTTP redirects (3xx_)::

    make SEARX_DEBUG=1 search.checker.google_news | grep -A1 "HTTP/1.1\" 3[0-9][0-9]"
    ...
    Engine google news                   Checking
    https://news.google.com:443 "GET /search?q=life&hl=en&lr=lang_en&ie=utf8&oe=utf8&ceid=US%3Aen&gl=US HTTP/1.1" 302 0
    https://news.google.com:443 "GET /search?q=life&hl=en-US&lr=lang_en&ie=utf8&oe=utf8&ceid=US:en&gl=US HTTP/1.1" 200 None
    --
    https://news.google.com:443 "GET /search?q=computer&hl=en&lr=lang_en&ie=utf8&oe=utf8&ceid=US%3Aen&gl=US HTTP/1.1" 302 0
    https://news.google.com:443 "GET /search?q=computer&hl=en-US&lr=lang_en&ie=utf8&oe=utf8&ceid=US:en&gl=US HTTP/1.1" 200 None
    --


``make pybuild``
================

.. _PyPi: https://pypi.org/
.. _twine: https://twine.readthedocs.io/en/latest/

Build Python packages in ``./dist/py``::

  $ make pybuild
  ...
  BUILD     pybuild
  running sdist
  running egg_info
  ...
  running bdist_wheel

  $ ls  ./dist
  searx-0.18.0-py3-none-any.whl  searx-0.18.0.tar.gz

To upload packages to PyPi_, there is also a ``pypi.upload`` target (to test use
``pypi.upload.test``).  Since you are not the owner of :pypi:`searx` you will
never need to upload.
