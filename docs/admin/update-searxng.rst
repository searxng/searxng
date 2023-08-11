.. _searxng maintenance:

===================
SearXNG maintenance
===================

.. sidebar:: further read

   - :ref:`toolboxing`
   - :ref:`uWSGI maintenance`

.. contents::
   :depth: 2
   :local:
   :backlinks: entry

.. _update searxng:

How to update
=============

How to update depends on the :ref:`installation` method.  If you have used the
:ref:`installation scripts`, use the ``update`` command from the :ref:`searxng.sh`
script.

.. code:: sh

    sudo -H ./utils/searxng.sh instance update

.. _inspect searxng:

How to inspect & debug
======================

How to debug depends on the :ref:`installation` method.  If you have used the
:ref:`installation scripts`, use the ``inspect`` command from the :ref:`searxng.sh`
script.

.. code:: sh

    sudo -H ./utils/searxng.sh instance inspect

.. _migrate and stay tuned:

Migrate and stay tuned!
=======================

.. sidebar:: info

   - :pull:`1332`
   - :pull:`456`
   - :pull:`A comment about rolling release <446#issuecomment-954730358>`

SearXNG is a *rolling release*; each commit to the master branch is a release.
SearXNG is growing rapidly, the services and opportunities are change every now
and then, to name just a few:

- Bot protection has been switched from filtron to SearXNG's :ref:`limiter
  <limiter>`, this requires a :ref:`Redis <settings redis>` database.

- The image proxy morty is no longer needed, it has been replaced by the
  :ref:`image proxy <image_proxy>` from SearXNG.

- To save bandwidth :ref:`cache busting <static_use_hash>` has been implemented.
  To get in use, the ``static-expires`` needs to be set in the :ref:`uwsgi
  setup`.

To stay tuned and get in use of the new features, instance maintainers have to
update the SearXNG code regularly (see :ref:`update searxng`).  As the above
examples show, this is not always enough, sometimes services have to be set up
or reconfigured and sometimes services that are no longer needed should be
uninstalled.

.. hint::

   First of all: SearXNG is installed by the script :ref:`searxng.sh`.  If you
   have old filtron, morty or searx setup you should consider complete
   uninstall/reinstall.

Here you will find a list of changes that affect the infrastructure.  Please
check to what extent it is necessary to update your installations:

:pull:`1595`: ``[fix] uWSGI: increase buffer-size``
  Re-install uWSGI (:ref:`searxng.sh`) or fix your uWSGI ``searxng.ini``
  file manually.


remove obsolete services
------------------------

If your searx instance was installed *"Step by step"* or by the *"Installation
scripts"*, you need to undo the installation procedure completely.  If you have
morty & filtron installed, it is recommended to uninstall these services also.
In case of scripts, to uninstall use the scripts from the origin you installed
searx from or try::

  $ sudo -H ./utils/filtron.sh remove all
  $ sudo -H ./utils/morty.sh   remove all
  $ sudo -H ./utils/searx.sh   remove all

.. hint::

   If you are migrate from searx take into account that the ``.config.sh`` is no
   longer used.

If you upgrade from searx or from before :pull:`1332` has been merged and you
have filtron and/or morty installed, don't forget to remove HTTP sites.

Apache::

  $ sudo -H ./utils/filtron.sh apache remove
  $ sudo -H ./utils/morty.sh apache remove

nginx::

  $ sudo -H ./utils/filtron.sh nginx remove
  $ sudo -H ./utils/morty.sh nginx remove



Check after Installation
------------------------

Once you have done your installation, you can run a SearXNG *check* procedure,
to see if there are some left overs.  In this example there exists a *old*
``/etc/searx/settings.yml``::

   $ sudo -H ./utils/searxng.sh instance check

   SearXNG checks
   --------------
   ERROR: settings.yml in /etc/searx/ is deprecated, move file to folder /etc/searxng/
   INFO:  [OK] (old) account 'searx' does not exists
   INFO:  [OK] (old) account 'filtron' does not exists
   INFO:  [OK] (old) account 'morty' does not exists
   ...
   INFO    searx.redisdb                 : connecting to Redis db=0 path='/usr/local/searxng-redis/run/redis.sock'
   INFO    searx.redisdb                 : connected to Redis
