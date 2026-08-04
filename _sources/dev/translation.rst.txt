.. _translation:

===========
Translation
===========

.. _translate.codeberg.org: https://translate.codeberg.org/projects/searxng/
.. _Weblate: https://docs.weblate.org
.. _translations branch: https://github.com/searxng/searxng/tree/translations
.. _orphan branch: https://git-scm.com/docs/git-checkout#Documentation/git-checkout.txt---orphanltnewbranchgt
.. _Weblate repository: https://translate.codeberg.org/projects/searxng/searxng/#repository
.. _wlc: https://docs.weblate.org/en/latest/wlc.html

.. |translated| image:: https://translate.codeberg.org/widgets/searxng/-/searxng/svg-badge.svg
   :target: https://translate.codeberg.org/projects/searxng/

.. sidebar:: |translated|

   - :ref:`searx.babel_extract`
   - Weblate_
   - SearXNG `translations branch`_
   - SearXNG `Weblate repository`_
   - Weblate Client: wlc_
   - Babel Command-Line: `pybabel <http://babel.pocoo.org/en/latest/cmdline.html>`_
   - `weblate workflow <https://docs.weblate.org/en/latest/workflows.html>`_

Translation takes place on translate.codeberg.org_.

Translations which has been added by translators on the translate.codeberg.org_ UI are
committed to Weblate's counterpart of the SearXNG *origin* repository which is
located at ``https://translate.codeberg.org/git/searxng/searxng``.

There is no need to clone this repository, :ref:`SearXNG Weblate workflow` take
care of the synchronization with the *origin*.  To avoid merging commits from
the counterpart directly on the ``master`` branch of *SearXNG origin*, a *pull
request* (PR) is created by this workflow.

Weblate monitors the `translations branch`_, not the ``master`` branch.  This
branch is an `orphan branch`_, decoupled from the master branch (we already know
orphan branches from the ``gh-pages``).  The `translations branch`_ contains
only the

- ``translation/messages.pot`` and the
- ``translation/*/messages.po`` files, nothing else.


.. _SearXNG Weblate workflow:

.. figure:: translation.svg

   SearXNG's PR workflow to be in sync with Weblate

Sync from *origin* to *weblate*: using ``make weblate.push.translations``
  For each commit on the ``master`` branch of SearXNG *origin* the GitHub job
  :origin:`babel / Update translations branch
  <.github/workflows/integration.yml>` checks for updated translations.

Sync from *weblate* to *origin*: using ``make weblate.translations.commit``
  Every Friday, the GitHub workflow :origin:`babel / create PR for additions from
  weblate <.github/workflows/translations-update.yml>` creates a PR with the
  updated translation files:

  - ``translation/messages.pot``,
  - ``translation/*/messages.po`` and
  - ``translation/*/messages.mo``

wlc
===

.. _wlc configuration: https://docs.weblate.org/en/latest/wlc.html#wlc-config
.. _API key: https://translate.codeberg.org/accounts/profile/#api

All weblate integration is done by GitHub workflows, but if you want to use wlc_,
copy this content into `wlc configuration`_ in your HOME ``~/.config/weblate``

.. code-block:: ini

  [keys]
  https://translate.codeberg.org/api/ = APIKEY

Replace ``APIKEY`` by your `API key`_.
