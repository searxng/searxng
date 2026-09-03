.. _settings categories_as_tabs:

=======================
``categories_as_tabs:``
=======================

A list of the categories that are displayed as tabs in the user interface.
Categories not listed here can still be searched with the :ref:`search-syntax`.

.. code:: yaml

  categories_as_tabs:
    general:
    images:
    videos:
    news:
    map:
    music:
    it:
    science:
    files:
    social media:
    adult:

Engines are added to ``categories:`` (compare :ref:`engine categories`), the
categories listed in ``categories_as_tabs`` are shown as tabs in the UI.  If
there are no active engines in a category, the tab is not displayed (e.g. if a
user disables all engines in a category).

.. note::

   The ``adult`` tab groups the 18+ engines (:ref:`eporner engine` and
   :ref:`erome engine`).  Operators of public or SFW (safe for work) instances
   should set ``disabled: true`` on these engines in ``settings.yml``; with no
   active engine left in the category the tab disappears automatically.  The
   engines can still be queried individually by bang (``!ep``, ``!ero``) or all
   at once via ``!adult`` / the tab -- which is exactly what SFW instances want
   to avoid by disabling them.


On the preferences page (``/preferences``) -- under *engines* -- there is an
additional tab, called *other*.  In this tab are all engines listed that are not
in one of the UI tabs (not included in ``categories_as_tabs``).
