.. _engine command:

==============================
Fetch results from commandline
==============================

Previously, with searx you could search over the Internet on other people's
computers. Now it is possible to fetch results from your local machine without
connecting to any networks from the same graphical user interface.

.. _command line engines:

Command line engines
====================

In :pull-searx:`2128` a new type of engine has been introduced called ``command``.
This engine lets administrators add engines which run arbitrary shell commands
and show its output on the web UI of searx.

When creating and enabling a ``command`` engine on a public searx instance,
you must be careful to avoid leaking private data. The easiest solution
is to add tokens to the engine. Thus, only those who have the appropriate token
can retrieve results from the it.

The engine base is flexible. Only your imagination can limit the power of this engine. (And
maybe security concerns.) The following options are available:

* ``command``: A comma separated list of the elements of the command. A special token {{QUERY}} tells searx where to put the search terms of the user. Example: ``['ls', '-l', '-h', '{{QUERY}}']``
* ``delimiter``: A dict containing a delimiter char and the "titles" of each element in keys.
* ``parse_regex``: A dict containing the regular expressions for each result key.
* ``query_type``: The expected type of user search terms. Possible values: ``path`` and ``enum``. ``path`` checks if the uesr provided path is inside the working directory. If not the query is not executed. ``enum`` is a list of allowed search terms. If the user submits something which is not included in the list, the query returns an error.
* ``query_enum``: A list containing allowed search terms if ``query_type`` is set to ``enum``.
* ``working_dir``: The directory where the command has to be executed. Default: ``.``
* ``result_separator``: The character that separates results. Default: ``\n``
 

The example engine below can be used to find files with a specific name in the configured
working directory.

.. code:: yaml

  - name: find
    engine: command
    command: ['find', '.', '-name', '{{QUERY}}']
    query_type: path
    shortcut: fnd
    delimiter:
        chars: ' '
        keys: ['line']


Next steps
==========

In the next milestone, support for local search engines and indexers (e.g. Elasticsearch)
are going to be added. This way, you will be able to query your own databases/indexers.

Acknowledgement
===============

This development was sponsored by `Search and Discovery Fund`_ of `NLnet Foundation`_ .

.. _Search and Discovery Fund: https://nlnet.nl/discovery
.. _NLnet Foundation: https://nlnet.nl/
