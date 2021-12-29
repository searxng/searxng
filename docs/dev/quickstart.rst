.. _devquickstart:

======================
Development Quickstart
======================

.. _npm: https://www.npmjs.com/
.. _Node.js: https://nodejs.org/

SearXNG loves developers, just clone and start hacking.  All the rest is done for
you simply by using :ref:`make <makefile>`.

.. code:: sh

    git clone https://github.com/searxng/searxng.git searxng

Here is how a minimal workflow looks like:

1. *start* hacking
2. *run* your code: :ref:`make run`
3. *test* your code: :ref:`make test`

If you think at some point something fails, go back to *start*.  Otherwise,
choose a meaningful commit message and we are happy to receive your pull
request. To not end in *wild west* we have some directives, please pay attention
to our ":ref:`how to contribute`" guideline.

If you implement themes, you will need to setup a :ref:`make node.env` once:

.. code:: sh

   make node.env

Before you call *make run* (2.), you need to compile the modified styles and
JavaScript:

.. code:: sh

   make themes.all

Alternatively you can also compile selective the theme you have modified,
e.g. the *simple* theme.

.. code:: sh

   make themes.simple

.. tip::

   To get live builds while modifying CSS & JS use: ``LIVE_THEME=simple make run``

If you finished your *tests* you can start to commit your changes.  To separate
the modified source code from the build products first run:

.. code:: sh

   make static.build.restore

This will restore the old build products and only your changes of the code
remain in the working tree which can now be added & commited.  When all sources
are commited, you can commit the build products simply by:

.. code:: sh

   make static.build.commit

Commiting the build products should be the last step, just before you send us
your PR.  There is also a make target to rewind this last build commit:

.. code:: sh

   make static.build.drop
