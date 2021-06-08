.. _engine command:

====================
Command Line Engines
====================

.. sidebar:: info

   - :origin:`command.py <searx/engines/command.py>`
   - :ref:`offline engines`

With *command engines* administrators can run engines to integrate arbitrary
shell commands.

When creating and enabling a ``command`` engine on a public instance, you must
be careful to avoid leaking private data.  The easiest solution is to limit the
access by setting ``tokens`` as described in section :ref:`private engines`.

The engine base is flexible.  Only your imagination can limit the power of this
engine (and maybe security concerns).  The following options are available:

``command``:
  A comma separated list of the elements of the command.  A special token
  ``{{QUERY}}`` tells where to put the search terms of the user. Example:

  .. code:: yaml

     ['ls', '-l', '-h', '{{QUERY}}']

``delimiter``:
  A mapping containing a delimiter ``char`` and the *titles* of each element in
  ``keys``.

``parse_regex``:
  A dict containing the regular expressions for each result key.

``query_type``:

  The expected type of user search terms.  Possible values: ``path`` and
  ``enum``.

  ``path``:
    Checks if the user provided path is inside the working directory.  If not,
    the query is not executed.

  ``enum``:
    Is a list of allowed search terms.  If the user submits something which is
    not included in the list, the query returns an error.

``query_enum``:
  A list containing allowed search terms if ``query_type`` is set to ``enum``.

``working_dir``:

  The directory where the command has to be executed.  Default: ``./``

``result_separator``:
  The character that separates results. Default: ``\n``

The example engine below can be used to find files with a specific name in the
configured working directory:

.. code:: yaml

  - name: find
    engine: command
    command: ['find', '.', '-name', '{{QUERY}}']
    query_type: path
    shortcut: fnd
    delimiter:
        chars: ' '
        keys: ['line']


Acknowledgment
==============

This development was sponsored by `Search and Discovery Fund
<https://nlnet.nl/discovery>`_ of `NLnet Foundation <https://nlnet.nl/>`_.
