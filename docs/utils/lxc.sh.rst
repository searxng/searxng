
.. _snap: https://snapcraft.io
.. _snapcraft LXD: https://snapcraft.io/lxd
.. _LXC/LXD Image Server: https://uk.images.linuxcontainers.org/
.. _LXC: https://linuxcontainers.org/lxc/introduction/
.. _LXD: https://linuxcontainers.org/lxd/introduction/
.. _`LXD@github`: https://github.com/lxc/lxd

.. _archlinux: https://www.archlinux.org/

.. _lxc.sh:

================
``utils/lxc.sh``
================

.. sidebar:: further reading

   - snap_, `snapcraft LXD`_
   - LXC_,  LXD_
   - `LXC/LXD Image Server`_
   - `LXD@github`_

With the use of *Linux Containers* (LXC_) we can scale our tasks over a stack of
containers, what we call the: *lxc suite*.  The *SearXNG suite*
(:origin:`lxc-searxng.env <utils/lxc-searxng.env>`) is loaded by default, every time
you start the ``lxc.sh`` script (*you do not need to care about*).

Before you can start with containers, you need to install and initiate LXD_
once::

  $ snap install lxd
  $ lxd init --auto

To make use of the containers from the *SearXNG suite*, you have to build the
:ref:`LXC suite containers <lxc.sh help>` initial.  But be warned, **this might
take some time**::

  $ sudo -H ./utils/lxc.sh build

A cup of coffee later, your LXC suite is build up and you can run whatever task
you want / in a selected or even in all :ref:`LXC suite containers <lxc.sh
help>`.

.. hint::

   If you see any problems with the internet connectivity of your
   containers read section :ref:`internet connectivity docker`.

If you do not want to build all containers, **you can build just one**::

  $ sudo -H ./utils/lxc.sh build searxng-archlinux

*Good to know ...*

Each container shares the root folder of the repository and the command
``utils/lxc.sh cmd`` **handles relative path names transparent**, compare output
of::

  $ sudo -H ./utils/lxc.sh cmd -- ls -la Makefile
  ...

In the containers, you can run what ever you want, e.g. to start a bash use::

  $ sudo -H ./utils/lxc.sh cmd searxng-archlinux bash
  INFO:  [searxng-archlinux] bash
  [root@searxng-archlinux SearXNG]#

If there comes the time you want to **get rid off all** the containers and
**clean up local images** just type::

  $ sudo -H ./utils/lxc.sh remove
  $ sudo -H ./utils/lxc.sh remove images

.. _internet connectivity docker:

Internet Connectivity & Docker
==============================

.. sidebar::  further read

   - `Docker blocking network of existing LXC containers <https://github.com/docker/for-linux/issues/103>`__
   - `Docker and IPtables (fralef.me) <https://fralef.me/docker-and-iptables.html>`__
   - `Docker and iptables (docker.com) <https://docs.docker.com/network/iptables/#docker-on-a-router/>`__

There is a conflict in the ``iptables`` setup of Docker & LXC.  If you have
docker installed, you may find that the internet connectivity of your LXD
containers no longer work.

Whenever docker is started (reboot) it sets the iptables policy for the
``FORWARD`` chain to ``DROP`` `[ref]
<https://docs.docker.com/network/iptables/#docker-on-a-router>`__::

  $ sudo -H iptables-save | grep FORWARD
  :FORWARD ACCEPT [7048:7851230]
  :FORWARD DROP [7048:7851230]

A handy solution of this problem might be to reset the policy for the
``FORWARD`` chain after the network has been initialized.  For this create a
file in the ``if-up`` section of the network (``/etc/network/if-up.d/iptable``)
and insert the following lines::

  #!/bin/sh
  iptables -F FORWARD
  iptables -P FORWARD ACCEPT

Don't forget to set the execution bit::

  sudo chmod ugo+x /etc/network/if-up.d/iptable

Reboot your system and check the iptables rules::

  $ sudo -H iptables-save | grep FORWARD
  :FORWARD ACCEPT [7048:7851230]
  :FORWARD ACCEPT [7048:7851230]


.. _lxc.sh install suite:

Install suite
=============

To install the complete :ref:`SearXNG suite (includes searx, morty & filtron)
<lxc-searxng.env>` into all LXC_ use::

  $ sudo -H ./utils/lxc.sh install suite

The command above installs a SearXNG suite (see :ref:`installation scripts`).
To :ref:`install a nginx <installation nginx>` reverse proxy (or alternatively
use :ref:`apache <installation apache>`)::

    sudo -H ./utils/lxc.sh cmd -- FORCE_TIMEOUT=0 ./utils/searxng.sh install nginx

To get the IP (URL) of the SearXNG service in the containers use ``show suite``
command.  To test instances from containers just open the URLs in your
WEB-Browser::

  $ sudo ./utils/lxc.sh show suite | grep SEARXNG_URL

  [searxng-ubu2110]      SEARXNG_URL          : http://n.n.n.147/searxng
  [searxng-ubu2004]      SEARXNG_URL          : http://n.n.n.246/searxng
  [searxnggfedora35]     SEARXNG_URL          : http://n.n.n.140/searxng
  [searxng-archlinux]    SEARXNG_URL          : http://n.n.n.165/searxng


Running commands
================

**Inside containers, you can use make or run scripts** from the
:ref:`toolboxing`.  By example: to setup a :ref:`buildhosts` and run the
Makefile target ``test`` in the archlinux_ container::

  sudo -H ./utils/lxc.sh cmd searxng-archlinux ./utils/searxng.sh install buildhost
  sudo -H ./utils/lxc.sh cmd searxng-archlinux make test


Setup SearXNG buildhost
=======================

You can **install the SearXNG buildhost environment** into one or all containers.
The installation procedure to set up a :ref:`build host<buildhosts>` takes its
time.  Installation in all containers will take more time (time for another cup
of coffee).::

  sudo -H ./utils/lxc.sh cmd -- ./utils/searxng.sh install buildhost

To build (live) documentation inside a archlinux_ container::

  sudo -H ./utils/lxc.sh cmd searxng-archlinux make docs.clean docs.live
  ...
  [I 200331 15:00:42 server:296] Serving on http://0.0.0.0:8080

To get IP of the container and the port number *live docs* is listening::

  $ sudo ./utils/lxc.sh show suite | grep docs.live
  ...
  [searxng-archlinux]  INFO:  (eth0) docs.live:  http://n.n.n.12:8080/


.. _lxc.sh help:

Overview
========

The ``--help`` output of the script is largely self-explanatory:

.. program-output:: ../utils/lxc.sh --help


.. _lxc-searxng.env:

SearXNG suite
=============

.. literalinclude:: ../../utils/lxc-searxng.env
   :language: bash
