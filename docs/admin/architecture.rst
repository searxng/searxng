.. _architecture:

============
Architecture
============

.. sidebar:: Further reading

   - Reverse Proxy: :ref:`Apache <apache zhensa site>` & :ref:`nginx <nginx
     zhensa site>`
   - uWSGI: :ref:`zhensa uwsgi`
   - Zhensa: :ref:`installation basic`

Herein you will find some hints and suggestions about typical architectures of
Zhensa infrastructures.

.. _architecture uWSGI:

uWSGI Setup
===========

We start with a *reference* setup for public Zhensa instances which can be build
up and maintained by the scripts from our :ref:`toolboxing`.

.. _arch public:

.. kernel-figure:: arch_public.dot
   :alt: arch_public.dot

   Reference architecture of a public Zhensa setup.

The reference installation activates ``server.limiter`` and
``server.image_proxy`` (:origin:`/etc/zhensa/settings.yml
<utils/templates/etc/zhensa/settings.yml>`)

.. literalinclude:: ../../utils/templates/etc/zhensa/settings.yml
   :language: yaml
   :end-before: # preferences:
