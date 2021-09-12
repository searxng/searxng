.. _devquickstart:

======================
Development Quickstart
======================

.. _npm: https://www.npmjs.com/

SearXNG loves developers, just clone and start hacking.  All the rest is done for
you simply by using :ref:`make <makefile>`.

.. code:: sh

    git clone https://github.com/searxng/searxng.git searx

Here is how a minimal workflow looks like:

1. *start* hacking
2. *run* your code: :ref:`make run`
3. *test* your code: :ref:`make test`

If you think at some point something fails, go back to *start*.  Otherwise,
choose a meaningful commit message and we are happy to receive your pull
request. To not end in *wild west* we have some directives, please pay attention
to our ":ref:`how to contribute`" guideline.

If you implement themes, you will need to compile styles and JavaScript before
*run*.

.. code:: sh

   make themes.all

Don't forget to install npm_ first.

.. tabs::

   .. group-tab:: Ubuntu / debian

      .. code:: sh

         sudo -H apt-get install npm

   .. group-tab:: Arch Linux

      .. code-block:: sh

         sudo -H pacman -S npm

   .. group-tab::  Fedora / RHEL

      .. code-block:: sh

	 sudo -H dnf install npm

If you finished your *tests* you can start to commit your changes.  To separate
the changed code from the build products first run:

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
