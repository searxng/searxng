.. _private engines:

============================
Private Engines (``tokens``)
============================

Administrators might find themselves wanting to limit access to some of the
enabled engines on their instances. It might be because they do not want to
expose some private information through :ref:`offline engines`.  Or they would
rather share engines only with their trusted friends or colleagues.

To solve this issue the concept of *private engines* exists.


A new option was added to engines named `tokens`. It expects a list of
strings. If the user making a request presents one of the tokens of an engine,
they can access information about the engine and make search requests.

Example configuration to restrict access to the Arch Linux Wiki engine:

.. code:: yaml

  - name: arch linux wiki
    engine: archlinux
    shortcut: al
    tokens: [ 'my-secret-token' ]


Unless a user has configured the right token, the engine is going
to be hidden from him/her. It is not going to be included in the
list of engines on the Preferences page and in the output of
`/config` REST API call.

Tokens can be added to one's configuration on the Preferences page
under "Engine tokens". The input expects a comma separated list of
strings.

The distribution of the tokens from the administrator to the users
is not carved in stone. As providing access to such engines
implies that the admin knows and trusts the user, we do not see
necessary to come up with a strict process. Instead,
we would like to add guidelines to the documentation of the feature.


Acknowledgment
==============

This development was sponsored by `Search and Discovery Fund
<https://nlnet.nl/discovery>`_ of `NLnet Foundation <https://nlnet.nl/>`_.
