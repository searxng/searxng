.. _architecture:

============
Architecture
============

.. sidebar:: Further reading

   - Reverse Proxy: :ref:`Apache <apache searxng site>` & :ref:`nginx <nginx
     searxng site>`
   - uWSGI: :ref:`searxng uwsgi`
   - SearXNG: :ref:`installation basic`

Herein you will find some hints and suggestions about typical architectures of
SearXNG infrastructures.

.. _architecture uWSGI:

uWSGI Setup
===========

We start with a *reference* setup for public SearXNG instances which can be build
up and maintained by the scripts from our :ref:`toolboxing`.

.. _arch public:

.. kernel-figure:: arch_public.dot
   :alt: arch_public.dot

   Reference architecture of a public SearXNG setup.

The reference installation activates ``server.limiter`` and
``server.image_proxy`` (:origin:`/etc/searxng/settings.yml
<utils/templates/etc/searxng/settings.yml>`)

.. literalinclude:: ../../utils/templates/etc/searxng/settings.yml
   :language: yaml
   :end-before: # preferences:
