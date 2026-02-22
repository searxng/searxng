.. _how to contribute:

=================
How to contribute
=================

.. contents::
   :depth: 2
   :local:
   :backlinks: entry

Prime directives: Privacy, Hackability
======================================

SearXNG has two prime directives, **privacy-by-design and hackability** .  The
hackability comes in three levels:

- support of search engines
- plugins to alter search behaviour
- hacking SearXNG itself

Note the lack of "world domination" among the directives.  SearXNG has no
intention of wide mass-adoption, rounded corners, etc.  The prime directive
"privacy" deserves a separate chapter, as it's quite uncommon unfortunately.

Privacy-by-design
-----------------

SearXNG was born out of the need for a **privacy-respecting** search tool which
can be extended easily to maximize both its search and its privacy protecting
capabilities.

Some widely used search engine features may work differently,
may be turned off by default, or may not be implemented at all in SearXNG
**as a consequence of a privacy-by-design approach**.

Following this approach, features reducing the privacy preserving aspects of SearXNG should be
switched off by default or should not be implemented at all.  There are plenty of
search engines already providing such features.  If a feature reduces
SearXNG's efficacy in protecting a user's privacy, the user must be informed about
the effect of choosing to enable it.  Features that protect privacy but differ from the
expectations of the user should also be carefully explained to them.

Also, if you think that something works weird with SearXNG, it might be because
the tool you are using is designed in a way that interferes with SearXNG's privacy aspects.
Submitting a bug report to the vendor of the tool that misbehaves might be a good
feedback for them to reconsider the disrespect to their customers (e.g., ``GET`` vs ``POST``
requests in various browsers).

Remember the other prime directive of SearXNG is to be hackable, so if the above
privacy concerns do not fancy you, simply fork it.

  *Happy hacking.*

Code
====

.. _PEP8: https://www.python.org/dev/peps/pep-0008/
.. _Structural split of changes:
    https://wiki.openstack.org/wiki/GitCommitMessages#Structural_split_of_changes

.. sidebar:: Create good commits!

   - :ref:`create commit`

In order to submit a patch, please follow the steps below:

- Follow coding conventions.

  - PEP8_ standards apply, except the convention of line length
  - Maximum line length is 120 characters

- The cardinal rule for creating good commits is to ensure there is only one
  *logical change* per commit / read `Structural split of changes`_

- Check if your code breaks existing tests.  If so, update the tests or fix your
  code.

- If your code can be unit-tested, add unit tests.

- Add yourself to the :origin:`AUTHORS.rst` file.

- Choose meaningful commit messages, see :ref:`create commit`

- Create a pull request.

For more help on getting started with SearXNG development, see :ref:`devquickstart`.


Translation
===========

Translation currently takes place on :ref:`weblate <translation>`.


.. _contrib docs:

Documentation
=============

.. _Sphinx: https://www.sphinx-doc.org
.. _reST: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html

.. sidebar:: The reST sources

   has been moved from ``gh-branch`` into ``master`` (:origin:`docs`).

The documentation is built using Sphinx_.  So in order to be able to generate
the required files, you have to install it on your system.  Much easier, use
our :ref:`makefile`.

Here is an example which makes a complete rebuild:

.. code:: sh

   $ make docs.clean docs.html
   ...
   The HTML pages are in dist/docs.

.. _make docs.live:

Live build
----------

.. _sphinx-autobuild:
   https://github.com/executablebooks/sphinx-autobuild/blob/master/README.md

.. sidebar:: docs.clean

   It is recommended to assert a complete rebuild before deploying (use
   ``docs.clean``).

Live build is like WYSIWYG.  It's the recommended way to go if you want to edit the documentation.
The Makefile target ``docs.live`` builds the docs, opens
URL in your favorite browser and rebuilds every time a reST file has been
changed (:ref:`make docs.clean`).

.. code:: sh

   $ make docs.live
   ...
   The HTML pages are in dist/docs.
   ... Serving on http://0.0.0.0:8000
   ... Start watching changes

Live builds are implemented by sphinx-autobuild_.  Use environment
``$(SPHINXOPTS)`` to pass arguments to the sphinx-autobuild_ command.  You can
pass any argument except for the ``--host`` option (which is always set to ``0.0.0.0``).
E.g., to find and use a free port, use:

.. code:: sh

   $ SPHINXOPTS="--port 0" make docs.live
   ...
   ... Serving on http://0.0.0.0:50593
   ...


.. _deploy on github.io:

deploy on github.io
-------------------

To deploy documentation at :docs:`github.io <.>` use Makefile target :ref:`make
docs.gh-pages`, which builds the documentation and runs all the needed git add,
commit and push:

.. code:: sh

   $ make docs.clean docs.gh-pages

.. attention::

   If you are working in your own brand, don't forget to adjust your
   :ref:`settings brand`.
