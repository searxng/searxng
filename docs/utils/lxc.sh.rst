
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

With the use of *Linux Containers* (LXC_) we can scale our tasks over a stack of
containers, what we call the: *lxc suite*.  The :ref:`lxc-searxng.env` is
loaded by default, every time you start the ``lxc.sh`` script (*you do not need
to care about*).

.. sidebar:: further reading

   - snap_, `snapcraft LXD`_
   - LXC_,  LXD_
   - `LXC/LXD Image Server`_
   - `LXD@github`_

.. contents::
   :depth: 2
   :local:
   :backlinks: entry


.. _lxd install:

Install LXD
===========

Before you can start with containers, you need to install and initiate LXD_
once::

  $ snap install lxd
  $ lxd init --auto

To make use of the containers from the *SearXNG suite*, you have to build the
:ref:`LXC suite containers <lxc.sh help>` initial.  But be warned, **this might
take some time**::

  $ sudo -H ./utils/lxc.sh build

.. sidebar:: hint

   If you have issues with the internet connectivity of your containers read
   section :ref:`internet connectivity docker`.

A cup of coffee later, your LXC suite is build up and you can run whatever task
you want / in a selected or even in all :ref:`LXC suite containers <lxc.sh
help>`.

.. _internet connectivity docker:

Internet Connectivity & Docker
------------------------------

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


.. _searxng lxc suite:

SearXNG LXC suite
=================

The intention of the *SearXNG LXC suite* is to build up a suite of containers
for development tasks or :ref:`buildhosts <Setup SearXNG buildhost>` with a very
small set of simple commands.  At the end of the ``--help`` output the SearXNG
suite from the :ref:`lxc-searxng.env` is introduced::

   $ sudo -H ./utils/lxc.sh --help
   ...
   LXC suite: searxng
     Suite includes installation of SearXNG
     images:     ubu2004 ubu2204 fedora35 archlinux
     containers: searxng-ubu2004 searxng-ubu2204 searxng-fedora35 searxng-archlinux

As shown above there are images and containers build up on this images.  To show
more info about the containers in the *SearXNG LXC suite* call ``show suite``.
If this is the first time you make use of the SearXNG LXC suite, no containers
are installed and the output is::

  $ sudo -H ./utils/lxc.sh show suite

  LXC suite (searxng-*)
  =====================

  +------+-------+------+------+------+-----------+
  | NAME | STATE | IPV4 | IPV6 | TYPE | SNAPSHOTS |
  +------+-------+------+------+------+-----------+

  WARN:  container searxng-ubu2004 does not yet exists
  WARN:  container searxng-ubu2204 does not yet exists
  WARN:  container searxng-fedora35 does not yet exists
  WARN:  container searxng-archlinux does not yet exists

If you do not want to run a command or a build in all containers, **you can
build just one**. Here by example in the container that is build upon the
*archlinux* image::

  $ sudo -H ./utils/lxc.sh build searxng-archlinux
  $ sudo -H ./utils/lxc.sh cmd searxng-archlinux pwd

Otherwise, to apply a command to all containers you can use::

  $ sudo -H ./utils/lxc.sh build
  $ sudo -H ./utils/lxc.sh cmd -- ls -la .

Running commands
----------------

**Inside containers, you can run scripts** from the :ref:`toolboxing` or run
what ever command you need.  By example, to start a bash use::

  $ sudo -H ./utils/lxc.sh cmd searxng-archlinux bash
  INFO:  [searxng-archlinux] bash
  [root@searxng-archlinux SearXNG]#

.. _Good to know:

Good to know
------------

Each container shares the root folder of the repository and the command
``utils/lxc.sh cmd`` **handle relative path names transparent**::

 $ pwd
 /share/SearXNG

 $ sudo -H ./utils/lxc.sh cmd searxng-archlinux pwd
 INFO:  [searxng-archlinux] pwd
 /share/SearXNG

The path ``/share/SearXNG`` will be different on your HOST system.  The commands
in the conatiner are executed by the ``root`` inside of the container.  Compare
output of::

  $ ls -li Makefile
  47712402 -rw-rw-r-- 1 markus markus 2923 Apr 19 13:52 Makefile

  $ sudo -H ./utils/lxc.sh cmd searxng-archlinux ls -li Makefile
  INFO:  [searxng-archlinux] ls -li Makefile
  47712402 -rw-rw-r-- 1 root root 2923 Apr 19 11:52 Makefile
  ...

Since the path ``/share/SearXNG`` of the HOST system is wrapped into the
container under the same name, the shown ``Makefile`` (inode ``47712402``) in
the ouput is always the identical ``/share/SearXNG/Makefile`` from the HOST
system.  In the example shown above the owner of the path in the container is
the ``root`` user of the conatiner (and the timezone in the container is
different to HOST system).


.. _lxc.sh install suite:

Install suite
-------------

.. sidebar::  further read

   - :ref:`working in containers`
   - :ref:`FORCE_TIMEOUT <FORCE_TIMEOUT>`

To install the complete :ref:`SearXNG suite <lxc-searxng.env>` into **all** LXC_
containers leave the container argument empty and run::

  $ sudo -H ./utils/lxc.sh build
  $ sudo -H ./utils/lxc.sh install suite

To *build & install* suite only in one container you can use by example::

  $ sudo -H ./utils/lxc.sh build searxng-archlinux
  $ sudo -H ./utils/lxc.sh install suite searxng-archlinux

The command above installs a SearXNG suite (see :ref:`installation scripts`).
To :ref:`install a nginx <installation nginx>` reverse proxy (or alternatively
use :ref:`apache <installation apache>`)::

  $ sudo -H ./utils/lxc.sh cmd -- FORCE_TIMEOUT=0 ./utils/searxng.sh install nginx

Same operation just in one container of the suite::

  $ sudo -H ./utils/lxc.sh cmd searxng-archlinux FORCE_TIMEOUT=0 ./utils/searxng.sh install nginx

The :ref:`FORCE_TIMEOUT <FORCE_TIMEOUT>` environment is set to zero to run the
script without user interaction.

To get the IP (URL) of the SearXNG service in the containers use ``show suite``
command.  To test instances from containers just open the URLs in your
WEB-Browser::

  $ sudo ./utils/lxc.sh show suite | grep SEARXNG_URL

  [searxng-ubu2110]      SEARXNG_URL          : http://n.n.n.170/searxng
  [searxng-ubu2004]      SEARXNG_URL          : http://n.n.n.160/searxng
  [searxnggfedora35]     SEARXNG_URL          : http://n.n.n.150/searxng
  [searxng-archlinux]    SEARXNG_URL          : http://n.n.n.140/searxng

Clean up
--------

If there comes the time you want to **get rid off all** the containers and
**clean up local images** just type::

  $ sudo -H ./utils/lxc.sh remove
  $ sudo -H ./utils/lxc.sh remove images


.. _Setup SearXNG buildhost:

Setup SearXNG buildhost
=======================

You can **install the SearXNG buildhost environment** into one or all containers.
The installation procedure to set up a :ref:`build host<buildhosts>` takes its
time.  Installation in all containers will take more time (time for another cup
of coffee). ::

  sudo -H ./utils/lxc.sh cmd -- ./utils/searxng.sh install buildhost

To build (live) documentation inside a archlinux_ container::

  sudo -H ./utils/lxc.sh cmd searxng-archlinux make docs.clean docs.live
  ...
  [I 200331 15:00:42 server:296] Serving on http://0.0.0.0:8080

To get IP of the container and the port number *live docs* is listening::

  $ sudo ./utils/lxc.sh show suite | grep docs.live
  ...
  [searxng-archlinux]  INFO:  (eth0) docs.live:  http://n.n.n.140:8080/


.. _lxc.sh help:

Command Help
============

The ``--help`` output of the script is largely self-explanatory:

.. program-output:: ../utils/lxc.sh --help


.. _lxc-searxng.env:

SearXNG suite config
====================

The SearXNG suite is defined in the file :origin:`utils/lxc-searxng.env`:

.. literalinclude:: ../../utils/lxc-searxng.env
   :language: bash
