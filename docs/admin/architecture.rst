.. _architecture:

============
Architecture
============

.. sidebar:: Further reading

   - Reverse Proxy: :ref:`Apache <apache searx site>` & :ref:`nginx <nginx searx
     site>`
   - Filtron: :ref:`searx filtron`
   - Morty: :ref:`searx morty`
   - uWSGI: :ref:`searx uwsgi`
   - Searx: :ref:`installation basic`

Herein you will find some hints and suggestions about typical architectures of
SearXNG infrastructures.

We start with a contribution from :pull-searx:`@dalf <1776#issuecomment-567917320>`.
It shows a *reference* setup for public SearXNG instances which can build up and
maintained by the scripts from our :ref:`toolboxing`.

.. _arch public:

.. kernel-figure:: arch_public.dot
   :alt: arch_public.dot

   Reference architecture of a public SearXNG setup.
