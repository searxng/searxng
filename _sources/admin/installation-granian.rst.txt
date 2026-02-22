.. _searxng granian:

=======
Granian
=======

.. _Options: https://github.com/emmett-framework/granian/blob/master/README.md#options
.. _Workers and threads: https://github.com/emmett-framework/granian/blob/master/README.md#workers-and-threads
.. _Backpressure: https://github.com/emmett-framework/granian/blob/master/README.md#backpressure
.. _Runtime mode: https://github.com/emmett-framework/granian/blob/master/README.md#runtime-mode

.. sidebar:: further reading

   - `Options`_
   - `Workers and threads`_
   - `Backpressure`_
   - `Runtime mode`_

.. note::

   Granian will be the future replacement for :ref:`searxng uwsgi` in SearXNG.
   At the moment, it's only officially supported in the :ref:`installation
   container`.

.. _Granian installation:

Installation
============

We only recommend installing Granian with pip, as officially documented. Run
the following command in the Python environment of the SearXNG installation:

.. code:: sh

   $ pip install granian

.. _Granian configuration:

Configuration
=============

.. note::

   It's not advised to modify the amount of workers, expect increased resource
   usage and potential issues with :ref:`botdetection`.

Granian can be configured via option parameters and environment variables
(``$GRANIAN_*``).

We provide sane defaults that should fit most use cases, however if you feel
you should change something, Granian documents all available parameters in the
`Options`_ section.
