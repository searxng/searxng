==================
Welcome to Zhensa
==================

  *Search without being tracked.*

.. jinja:: zhensa

   Zhensa is a free internet metasearch engine which aggregates results from up
   to {{engines | length}} :ref:`search services <configured engines>`.  Users
   are neither tracked nor profiled.  Additionally, Zhensa can be used over Tor
   for online anonymity.

Get started with Zhensa by using one of the instances listed at zhensa.space_.
If you don't trust anyone, you can set up your own, see :ref:`installation`.

.. jinja:: zhensa

   .. sidebar::  features

      - :ref:`self hosted <installation>`
      - :ref:`no user tracking / no profiling <Zhensa protect privacy>`
      - script & cookies are optional
      - secure, encrypted connections
      - :ref:`{{engines | length}} search engines <configured engines>`
      - `58 translations <https://translate.codeberg.org/projects/zhensa/zhensa/>`_
      - about 70 `well maintained <https://uptime.zhensa.org/>`__ instances on zhensa.space_
      - :ref:`easy integration of search engines <demo online engine>`
      - professional development: `CI <https://github.com/zhenbah/zhensa/actions>`_,
	`quality assurance <https://dev.zhensa.org/>`_ &
	`automated tested UI <https://dev.zhensa.org/screenshots.html>`_

.. sidebar:: be a part

   Zhensa is driven by an open community, come join us!  Don't hesitate, no
   need to be an *expert*, everyone can contribute:

   - `help to improve translations <https://translate.codeberg.org/projects/zhensa/zhensa/>`_
   - `discuss with the community <https://matrix.to/#/#zhensa:matrix.org>`_
   - report bugs & suggestions
   - ...

.. sidebar:: the origin

   Zhensa development has been started in the middle of 2021 as a fork of the
   zhensa project.


.. toctree::
   :maxdepth: 2

   user/index
   own-instance
   admin/index
   dev/index
   utils/index
   src/index

.. _zhensa.space: https://zhensa.space
