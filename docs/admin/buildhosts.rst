.. _buildhosts:

==========
Buildhosts
==========

.. sidebar:: This article needs some work

   If you have any contribution send us your :pull:`PR <../pulls>`, see
   :ref:`how to contribute`.

.. contents::
   :depth: 2
   :local:
   :backlinks: entry

To get best results from build, it's recommend to install additional packages
on build hosts (see :ref:`searxng.sh`).::

  sudo -H ./utils/searxng.sh install buildhost

This will install packages needed by searx:

.. kernel-include:: $DOCS_BUILD/includes/searxng.rst
   :start-after: START distro-packages
   :end-before: END distro-packages

and packages needed to build docuemtation and run tests:

.. kernel-include:: $DOCS_BUILD/includes/searxng.rst
   :start-after: START build-packages
   :end-before: END build-packages

.. _docs build:

Build docs
==========

.. _Graphviz: https://graphviz.gitlab.io
.. _ImageMagick: https://www.imagemagick.org
.. _XeTeX: https://tug.org/xetex/
.. _dvisvgm: https://dvisvgm.de/

.. sidebar:: Sphinx build needs

   - ImageMagick_
   - Graphviz_
   - XeTeX_
   - dvisvgm_

Most of the sphinx requirements are installed from :origin:`setup.py` and the
docs can be build from scratch with ``make docs.html``.  For better math and
image processing additional packages are needed.  The XeTeX_ needed not only for
PDF creation, it's also needed for :ref:`math` when HTML output is build.

To be able to do :ref:`sphinx:math-support` without CDNs, the math are rendered
as images (``sphinx.ext.imgmath`` extension).

Here is the extract from the :origin:`docs/conf.py` file, setting math renderer
to ``imgmath``:

.. literalinclude:: ../conf.py
   :language: python
   :start-after: # sphinx.ext.imgmath setup
   :end-before: # sphinx.ext.imgmath setup END

If your docs build (``make docs.html``) shows warnings like this::

   WARNING: dot(1) not found, for better output quality install \
            graphviz from https://www.graphviz.org
   ..
   WARNING: LaTeX command 'latex' cannot be run (needed for math \
            display), check the imgmath_latex setting

you need to install additional packages on your build host, to get better HTML
output.

.. tabs::

   .. group-tab:: Ubuntu / debian

      .. code-block:: sh

         $ sudo apt install graphviz imagemagick texlive-xetex librsvg2-bin

   .. group-tab:: Arch Linux

      .. code-block:: sh

         $ sudo pacman -S graphviz imagemagick texlive-bin extra/librsvg

   .. group-tab::  Fedora / RHEL

      .. code-block:: sh

         $ sudo dnf install graphviz graphviz-gd texlive-xetex-bin librsvg2-tools


For PDF output you also need:

.. tabs::

   .. group-tab:: Ubuntu / debian

      .. code:: sh

         $ sudo apt texlive-latex-recommended texlive-extra-utils ttf-dejavu

   .. group-tab:: Arch Linux

      .. code:: sh

      	 $ sudo pacman -S texlive-core texlive-latexextra ttf-dejavu

   .. group-tab::  Fedora / RHEL

      .. code:: sh

      	 $ sudo dnf install \
	        texlive-collection-fontsrecommended texlive-collection-latex \
		dejavu-sans-fonts dejavu-serif-fonts dejavu-sans-mono-fonts \
		ImageMagick

.. _sh lint:

Lint shell scripts
==================

.. _ShellCheck: https://github.com/koalaman/shellcheck

To lint shell scripts, we use ShellCheck_ - a shell script static analysis tool.

.. SNIP sh lint requirements

.. tabs::

   .. group-tab:: Ubuntu / debian

      .. code-block:: sh

         $ sudo apt install shellcheck

   .. group-tab:: Arch Linux

      .. code-block:: sh

         $ sudo pacman -S shellcheck

   .. group-tab::  Fedora / RHEL

      .. code-block:: sh

         $ sudo dnf install ShellCheck

.. SNAP sh lint requirements
