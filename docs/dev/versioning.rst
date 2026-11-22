.. _versioning:

==========
Versioning
==========

SearXNG derives its version from git at runtime; there is no version number
stored in the sources.

Version string
==============

:py:obj:`searx.version.VERSION_STRING` is built from the commit date and the
short commit hash::

   <year>.<month>.<day>+<short-hash>

For example ``2026.11.21+c6ee3e9fd``.  A leading zero in the month or day is
removed (``2023.05.06`` becomes ``2023.5.6``).  If the working tree has
uncommitted changes (except ``searx/settings.yml`` and ``utils/brand.env``),
``+dirty`` is appended.

The same value is exposed as:

- ``VERSION_TAG`` -- the version without the ``+dirty`` suffix,
- ``DOCKER_TAG`` -- the version with ``+`` replaced by ``-`` (used for image
  tags).

Frozen versions
===============

When SearXNG runs outside a git repository, the version is read from the
generated module :origin:`searx/version_frozen.py`.  Generate it with:

.. code:: sh

   $ python -m searx.version freeze

See :ref:`make version.freeze` for details.

Git URL and branch
==================

``GIT_URL`` and ``GIT_BRANCH`` are read from the git remote (or from the
``GITHUB_REPOSITORY`` / ``GITHUB_REF_NAME`` environment variables in GitHub
Actions).  They are shown in the ``/config`` endpoint and on the about page.
