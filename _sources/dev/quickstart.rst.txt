.. _devquickstart:

======================
Development Quickstart
======================

.. _npm: https://www.npmjs.com/
.. _Node.js: https://nodejs.org/
.. _Biome: https://biomejs.dev/
.. _Stylelint: https://stylelint.io/

.. sidebar:: further read

   - :ref:`makefile`
   - :ref:`buildhosts`

SearXNG loves developers; Developers do not need to worry about tool chains, the
usual developer tasks can be comfortably executed via :ref:`make <makefile>`.

Don't hesitate, just clone SearXNG's sources and start hacking right now ..

.. code:: bash

    git clone https://github.com/searxng/searxng.git searxng

For the developer environment, `mise en place`_ is recommended:

.. code:: sh

   $ curl https://mise.run | sh

The tools required for a developer environment are provided via `mise.toml`_,
trust the project:

.. code:: sh

   $ mise trust

.. _mise.toml:
    https://github.com/searxng/searxng/blob/master/mise.toml
.. _mise en place:
    https://mise.jdx.dev/getting-started.html

Here is how a minimal workflow looks like:

1. *start* hacking
2. *run* your code: :ref:`make run`
3. *format & test* your code: :ref:`make format` and :ref:`make test`

If you think at some point something fails, go back to *start*.  Otherwise,
choose a meaningful commit message and we are happy to receive your pull
request. To not end in *wild west* we have some directives, please pay attention
to our ":ref:`how to contribute`" guideline.

.. _pdb: https://docs.python.org/3/library/pdb.html#module-pdb

If you want to debug with the *good old Python Debugger* pdb_: Alternatively to
``make run`` (2.) which starts a :ref:`searxng granian` server you can jump
into the developer environment and start a python based HTTP server by::

    $ ./manage dev.env
    ...
    (dev.env)$ SEARXNG_DEBUG=1 python -m searx.webapp

Since this is a pure Python solution, you can set breakpoints in your code with
``pdb.set_trace()`` and the debugger will wait for you in the terminal prompt.


.. sidebar:: further read

   - :ref:`make nvm`
   - :ref:`make themes`

If you implement themes, you will need to setup a :ref:`Node.js environment
<make node.env>`.  Before you call *make run* (2.), you need to compile the
modified styles and JavaScript: ``make node.clean themes.all``.  If Biome_
or Stylelint_ reports issues, try ``make themes.fix``.

Alternatively you can also compile selective the theme you have modified,
e.g. the *simple* theme.

.. code:: bash

   make themes.simple

.. tip::

   To get live builds while modifying CSS & JS use: ``LIVE_THEME=simple make run``

.. sidebar:: further read

   - :ref:`make static.build`

If you finished your *tests* you can start to commit your changes.  To separate
the modified source code from the build products first run:

.. code:: bash

   make static.build.restore

This will restore the old build products and only your changes of the code
remain in the working tree which can now be added & committed.  When all sources
are committed, you can commit the build products simply by:

.. code:: bash

   make static.build.commit

Committing the build products should be the last step, just before you send us
your PR.  There is also a make target to rewind this last build commit:

.. code:: bash

   make static.build.drop
