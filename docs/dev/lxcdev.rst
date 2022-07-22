.. _lxcdev:

==============================
Developing in Linux Containers
==============================

.. _LXC: https://linuxcontainers.org/lxc/introduction/

In this article we will show, how you can make use of Linux Containers (LXC_) in
*distributed and heterogeneous development cycles* (TL;DR; jump to the
:ref:`lxcdev summary`).

.. sidebar:: Audience

   This blog post is written for experienced admins and developers.  Readers
   should have a serious meaning about the terms: *distributed*, *merge* and
   *linux container*.

.. contents:: Contents
   :depth: 2
   :local:
   :backlinks: entry


Motivation
==========

Usually in our development cycle, we edit the sources and run some test and/or
builds by using ``make`` :ref:`[ref] <makefile>` before we commit.  This cycle
is simple and perfect but might fail in some aspects we should not overlook.

  **The environment in which we run all our development processes matters!**

The :ref:`makefile` and the :ref:`make install` encapsulate a lot for us, but
they do not have access to all prerequisites.  For example, there may have
dependencies on packages that are installed on the developer's desktop, but
usually are not preinstalled on a server or client system.  Another example is;
settings have been made to the software on developer's desktop that would never
be set on a *production* system.

  **Linux Containers are isolate environments and not to mix up all the
  prerequisites from various projects on developer's desktop is always a good
  choice.**

The scripts from :ref:`searx_utils` can divide in those to install and maintain
software:

- :ref:`searxng.sh`

and the script :ref:`lxc.sh`, with we can scale our installation, maintenance or
even development tasks over a stack of isolated containers / what we call the:

  **SearXNG LXC suite**

.. hint::

   If you see any problems with the internet connectivity of your
   containers read section :ref:`internet connectivity docker`.


Gentlemen, start your engines!
==============================

.. _LXD: https://linuxcontainers.org/lxd/introduction/
.. _archlinux: https://www.archlinux.org/

Before you can start with containers, you need to install and initiate LXD_
once:

.. tabs::

  .. group-tab:: desktop

     .. code:: bash

        $ snap install lxd
        $ lxd init --auto

And you need to clone from origin or if you have your own fork, clone from your
fork:

.. tabs::

  .. group-tab:: desktop

     .. code:: bash

        $ cd ~/Downloads
        $ git clone https://github.com/searxng/searxng.git searxng
        $ cd searxng

The :ref:`lxc-searxng.env` consists of several images, see ``export
LXC_SUITE=(...`` near by :origin:`utils/lxc-searxng.env#L19`.  For this blog post
we exercise on a archlinux_ image.  The container of this image is named
``searxng-archlinux``.  Lets build the container, but be sure that this container
does not already exists, so first lets remove possible old one:

.. tabs::

  .. group-tab:: desktop

     .. code:: bash

        $ sudo -H ./utils/lxc.sh remove searxng-archlinux
        $ sudo -H ./utils/lxc.sh build searxng-archlinux

.. sidebar:: The ``searxng-archlinux`` container

   is the base of all our exercises here.

In this container we install all services :ref:`including searx, morty & filtron
<lxc.sh install suite>` in once:

.. tabs::

  .. group-tab:: desktop

     .. code:: bash

        $ sudo -H ./utils/lxc.sh install suite searxng-archlinux

To proxy HTTP from filtron and morty in the container to the outside of the
container, install nginx into the container.  Once for the bot blocker filtron:

.. tabs::

  .. group-tab:: desktop

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux \
          ./utils/filtron.sh nginx install
        ...
        INFO:  got 429 from http://10.174.184.156/searx

and once for the content sanitizer (content proxy morty):

.. tabs::

  .. group-tab:: desktop

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux \
          ./utils/morty.sh nginx install
        ...
        INFO:  got 200 from http://10.174.184.156/morty/

.. sidebar:: Fully functional SearXNG suite

   From here on you have a fully functional SearXNG suite running with bot
   blocker (filtron) and WEB content sanitizer (content proxy morty), both are
   needed for a *privacy protecting* search engine.

On your system, the IP of your ``searxng-archlinux`` container differs from
http://10.174.184.156/searx, just open the URL reported in your installation
protocol in your WEB browser from the desktop to test the instance from outside
of the container.

In such a earXNG suite admins can maintain and access the debug log of the
different services quite easy.

.. _working in containers:

In containers, work as usual
============================

Usually you open a root-bash using ``sudo -H bash``.  In case of LXC containers
open the root-bash in the container using ``./utils/lxc.sh cmd
searxng-archlinux``:

.. tabs::

  .. group-tab:: desktop

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux bash
        INFO:  [searxng-archlinux] bash
        [root@searxng-archlinux searx]# pwd
        /share/searxng

The prompt ``[root@searxng-archlinux ...]`` signals, that you are the root user in
the searxng-container.  To debug the running SearXNG instance use:

.. tabs::

  .. group-tab:: root@searxng-archlinux

     .. code:: bash

        $ ./utils/searx.sh inspect service
        ...
        use [CTRL-C] to stop monitoring the log
        ...

Back in the browser on your desktop open the service http://10.174.184.156/searx
and run your application tests while the debug log is shown in the terminal from
above.  You can stop monitoring using ``CTRL-C``, this also disables the *"debug
option"* in SearXNG's settings file and restarts the SearXNG uwsgi application.
To debug services from filtron and morty analogous use:

Another point we have to notice is that the service (:ref:`SearXNG <searxng.sh>`
runs under dedicated system user account with the same name (compare
:ref:`create searxng user`).  To get a shell from theses accounts, simply call:

.. tabs::

  .. group-tab:: root@searxng-archlinux

     .. code:: bash

        $ ./utils/searxng.sh instance cmd bash

To get in touch, open a shell from the service user (searxng@searxng-archlinux):

.. tabs::

  .. group-tab:: desktop

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux ./utils/searxng.sh instance cmd bash
        INFO:  [searxng-archlinux] ./utils/searxng.sh instance cmd bash
        [searxng@searxng-archlinux ~]$

The prompt ``[searxng@searxng-archlinux]`` signals that you are logged in as system
user ``searx`` in the ``searxng-archlinux`` container and the python *virtualenv*
``(searxng-pyenv)`` environment is activated.

.. tabs::

  .. group-tab:: searxng@searxng-archlinux

     .. code:: bash

        (searxng-pyenv) [searxng@searxng-archlinux ~]$ pwd
        /usr/local/searxng


Wrap production into developer suite
====================================

In this section we will see how to change the *"Fully functional SearXNG suite"*
from a LXC container (which is quite ready for production) into a developer
suite.  For this, we have to keep an eye on the :ref:`installation basic`:

- SearXNG setup in: ``/etc/searxng/settings.yml``
- SearXNG user's home: ``/usr/local/searxng``
- virtualenv in: ``/usr/local/searxng/searxng-pyenv``
- SearXNG software in: ``/usr/local/searxng/searxng-src``

With the use of the :ref:`searxng.sh` the SearXNG service was installed as
:ref:`uWSGI application <searxng uwsgi>`.  To maintain this service, we can use
``systemctl`` (compare :ref:`uWSGI maintenance`).

.. tabs::

  .. group-tab:: desktop

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux \
          systemctl stop uwsgi@searxng

With the command above, we stopped the SearXNG uWSGI-App in the archlinux
container.

The uWSGI-App for the archlinux dsitros is configured in
:origin:`utils/templates/etc/uwsgi/apps-archlinux/searxng.ini`, from where at
least you should attend the settings of ``uid``, ``chdir``, ``env`` and
``http``::

  env = SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml
  http = 127.0.0.1:8888

  chdir = /usr/local/searxng/searxng-src/searx
  virtualenv = /usr/local/searxng/searxng-pyenv
  pythonpath = /usr/local/searxng/searxng-src

If you have read the :ref:`"Good to know section" <lxc.sh>` you remember, that
each container shares the root folder of the repository and the command
``utils/lxc.sh cmd`` handles relative path names **transparent**.  To wrap the
SearXNG installation into a developer one, we simple have to create a smylink to
the **transparent** reposetory from the desktop.  Now lets replace the
repository at ``searxng-src`` in the container with the working tree from outside
of the container:

.. tabs::

  .. group-tab:: container becomes a developer suite

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux \
          mv /usr/local/searxng/searxng-src /usr/local/searxng/searxng-src.old

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux \
          ln -s /share/searx/ /usr/local/searxng/searxng-src

Now we can develop as usual in the working tree of our desktop system.  Every
time the software was changed, you have to restart the SearXNG service (in the
conatiner):

.. tabs::

  .. group-tab:: desktop

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux \
          systemctl restart uwsgi@searx


Remember: :ref:`working in containers` .. here are just some examples from my
daily usage:

.. tabs::

  .. group-tab:: desktop

     To *inspect* the SearXNG instance (already described above):

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux \
          ./utils/searx.sh inspect service

     Run :ref:`makefile`, e.g. to test inside the container:

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux \
          make test

     To install all prerequisites needed for a :ref:`buildhosts`:

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux \
          ./utils/searxng.sh install buildhost

     To build the docs on a buildhost :ref:`buildhosts`:

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux \
          make docs.html

.. _lxcdev summary:

Summary
=======

We build up a fully functional SearXNG suite in a archlinux container:

.. code:: bash

   $ sudo -H ./utils/lxc.sh install suite searxng-archlinux

To access HTTP from the desktop we installed nginx for the services inside the
conatiner:

.. tabs::

  .. group-tab:: [root@searxng-archlinux]

     .. code:: bash

        $ ./utils/filtron.sh nginx install
        $ ./utils/morty.sh nginx install

To wrap the suite into a developer one, we created a symbolic link to the
repository which is shared **transparent** from the desktop's file system into
the container :

.. tabs::

  .. group-tab:: [root@searxng-archlinux]

     .. code:: bash

	$ mv /usr/local/searxng/searxng-src /usr/local/searxng/searxng-src.old
	$ ln -s /share/searx/ /usr/local/searxng/searxng-src
	$ systemctl restart uwsgi@searx

To get information about the searxNG suite in the archlinux container we can
use:

.. tabs::

  .. group-tab:: desktop

     .. code:: bash

        $ sudo -H ./utils/lxc.sh show suite searxng-archlinux
        ...
        [searxng-archlinux]  INFO:  (eth0) filtron:    http://10.174.184.156:4004/ http://10.174.184.156/searx
        [searxng-archlinux]  INFO:  (eth0) morty:      http://10.174.184.156:3000/
        [searxng-archlinux]  INFO:  (eth0) docs.live:  http://10.174.184.156:8080/
        [searxng-archlinux]  INFO:  (eth0) IPv6:       http://[fd42:573b:e0b3:e97e:216:3eff:fea5:9b65]
        ...

