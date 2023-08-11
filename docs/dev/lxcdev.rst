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

   **hint**

   If you have issues with the internet connectivity of your containers read
   section :ref:`internet connectivity docker`.


.. contents::
   :depth: 2
   :local:
   :backlinks: entry


Motivation
==========

Most often in our development cycle, we edit the sources and run some test
and/or builds by using ``make`` :ref:`[ref] <makefile>` before we commit.  This
cycle is simple and perfect but might fail in some aspects we should not
overlook.

  **The environment in which we run all our development processes matters!**

The :ref:`makefile` and the :ref:`make install` encapsulate a lot for us, but
these tools do not have access to all prerequisites.  For example, there may
have dependencies on packages that are installed on developer's desktop, but
usually are not preinstalled on a server or client system.  Another example is;
settings have been made to the software on developer's desktop that would never
be set on a *production* system.

  **Linux Containers are isolate environments**, we use them to not mix up all
  the prerequisites from various projects on developer's desktop.

The scripts from :ref:`searx_utils` can divide in those to install and maintain
software

- :ref:`searxng.sh`

and the script

- :ref:`lxc.sh`

with we can scale our installation, maintenance or even development tasks over a
stack of isolated containers / what we call the:

- :ref:`searxng lxc suite`

.. _lxcdev install searxng:

Gentlemen, start your engines!
==============================

.. _LXD: https://linuxcontainers.org/lxd/introduction/
.. _archlinux: https://www.archlinux.org/

Before you can start with containers, you need to install and initiate LXD_
once:

.. tabs::

  .. group-tab:: desktop (HOST)

     .. code:: bash

        $ snap install lxd
        $ lxd init --auto

And you need to clone from origin or if you have your own fork, clone from your
fork:

.. tabs::

  .. group-tab:: desktop (HOST)

     .. code:: bash

        $ cd ~/Downloads
        $ git clone https://github.com/searxng/searxng.git searxng
        $ cd searxng

.. sidebar:: The ``searxng-archlinux`` container

   is the base of all our exercises here.

The :ref:`lxc-searxng.env` consists of several images, see ``export
LXC_SUITE=(...`` near by :origin:`utils/lxc-searxng.env#L19`.
For this blog post we exercise on a archlinux_ image.  The container of this
image is named ``searxng-archlinux``.

Lets build the container, but be sure that this container does not already
exists, so first lets remove possible old one:

.. tabs::

  .. group-tab:: desktop (HOST)

     .. code:: bash

        $ sudo -H ./utils/lxc.sh remove searxng-archlinux
        $ sudo -H ./utils/lxc.sh build searxng-archlinux


.. sidebar::  further read

   - :ref:`lxc.sh install suite`
   - :ref:`installation nginx`

To install the complete :ref:`SearXNG suite <searxng lxc suite>` and the HTTP
proxy :ref:`installation nginx` into the archlinux container run:

.. tabs::

  .. group-tab:: desktop (HOST)

     .. code:: bash

        $ sudo -H ./utils/lxc.sh install suite searxng-archlinux
        $ sudo -H ./utils/lxc.sh cmd -- FORCE_TIMEOUT=0 ./utils/searxng.sh install nginx
        $ sudo ./utils/lxc.sh show suite | grep SEARXNG_URL
        ...
        [searxng-archlinux]    SEARXNG_URL          : http://n.n.n.140/searxng

.. sidebar:: Fully functional SearXNG suite

   From here on you have a fully functional SearXNG suite (including a
   :ref:`redis db`).

In such a SearXNG suite admins can maintain and access the debug log of the
services quite easy.

In the example above the SearXNG instance in the container is wrapped to
``http://n.n.n.140/searxng`` to the HOST system.  Note, on your HOST system, the
IP of your ``searxng-archlinux`` container is different to this example.  To
test the instance in the container from outside of the container, in your WEB
browser on your desktop just open the URL reported in your installation

.. _working in containers:

In containers, work as usual
============================

Usually you open a root-bash using ``sudo -H bash``.  In case of LXC containers
open the root-bash in the container is done by the ``./utils/lxc.sh cmd
searxng-archlinux`` command:

.. tabs::

  .. group-tab:: desktop (HOST)

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux bash
        INFO:  [searxng-archlinux] bash
        [root@searxng-archlinux SearXNG]$

The prompt ``[root@searxng-archlinux ...]`` signals, that you are the root user
in the container (GUEST).  To debug the running SearXNG instance use:

.. tabs::

  .. group-tab:: ``[root@searxng-archlinux SearXNG]`` (GUEST)

     .. code:: bash

        $ ./utils/searxng.sh instance inspect
        ...
        use [CTRL-C] to stop monitoring the log
        ...

  .. group-tab:: desktop (HOST)

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux ./utils/searxng.sh instance inspect
        ...
        use [CTRL-C] to stop monitoring the log
        ...


Back in the browser on your desktop open the service http://n.n.n.140/searxng
and run your application tests while the debug log is shown in the terminal from
above.  You can stop monitoring using ``CTRL-C``, this also disables the *"debug
option"* in SearXNG's settings file and restarts the SearXNG uwsgi application.

Another point we have to notice is that the service :ref:`SearXNG <searxng.sh>`
runs under dedicated system user account with the same name (compare
:ref:`create searxng user`).  To get a login shell from these accounts, simply
call:

.. tabs::

  .. group-tab:: ``[root@searxng-archlinux SearXNG]`` (GUEST)

     .. code:: bash

        $ ./utils/searxng.sh instance cmd bash -l
        (searx-pyenv) [searxng@searxng-archlinux ~]$ pwd
        /usr/local/searxng

  .. group-tab:: desktop (HOST)

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux ./utils/searxng.sh instance cmd bash -l
        INFO:  [searxng-archlinux] ./utils/searxng.sh instance cmd bash -l
        (searx-pyenv) [searxng@searxng-archlinux ~]$ pwd
        /usr/local/searxng

The prompt ``[searxng@searxng-archlinux]`` signals that you are logged in as system
user ``searxng`` in the ``searxng-archlinux`` container and the python *virtualenv*
``(searxng-pyenv)`` environment is activated.


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

  .. group-tab:: uwsgi@searxng

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux systemctl stop uwsgi@searxng

With the command above, we stopped the SearXNG uWSGI-App in the archlinux
container.

The uWSGI-App for the archlinux distros is configured in
:origin:`utils/templates/etc/uwsgi/apps-archlinux/searxng.ini`, from where at
least you should attend the settings of ``uid``, ``chdir``, ``env`` and
``http``::

  env = SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml
  http = 127.0.0.1:8888

  chdir = /usr/local/searxng/searxng-src/searx
  virtualenv = /usr/local/searxng/searxng-pyenv
  pythonpath = /usr/local/searxng/searxng-src

If you have read the :ref:`Good to know` you remember, that each container
shares the root folder of the repository and the command ``utils/lxc.sh cmd``
handles relative path names **transparent**.

To wrap the SearXNG installation in the container into a developer one, we
simple have to create a symlink to the **transparent** repository from the
desktop.  Now lets replace the repository at ``searxng-src`` in the container
with the working tree from outside of the container:

.. tabs::

  .. group-tab:: ``[root@searxng-archlinux SearXNG]`` (GUEST)

     .. code:: bash

        $ mv /usr/local/searxng/searxng-src  /usr/local/searxng/searxng-src.old
        $ ln -s /share/SearXNG/ /usr/local/searxng/searxng-src

  .. group-tab:: desktop (HOST)

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux \
          mv /usr/local/searxng/searxng-src /usr/local/searxng/searxng-src.old

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux \
          ln -s /share/SearXNG/ /usr/local/searxng/searxng-src

Now we can develop as usual in the working tree of our desktop system.  Every
time the software was changed, you have to restart the SearXNG service (in the
container):

.. tabs::

  .. group-tab:: uwsgi@searxng

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux systemctl restart uwsgi@searxng


Remember: :ref:`working in containers` .. here are just some examples from my
daily usage:

To *inspect* the SearXNG instance (already described above):

.. tabs::

  .. group-tab:: ``[root@searxng-archlinux SearXNG]`` (GUEST)

     .. code:: bash

        $ ./utils/searx.sh inspect service

  .. group-tab:: desktop (HOST)

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux ./utils/searx.sh inspect service

Run :ref:`makefile`, e.g. to test inside the container:

.. tabs::

  .. group-tab:: ``[root@searxng-archlinux SearXNG]`` (GUEST)

     .. code:: bash

        $ make test

  .. group-tab:: desktop (HOST)

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux  make test



To install all prerequisites needed for a :ref:`buildhosts`:

.. tabs::

  .. group-tab:: ``[root@searxng-archlinux SearXNG]`` (GUEST)

     .. code:: bash

        $ ./utils/searxng.sh install buildhost

  .. group-tab:: desktop (HOST)

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux ./utils/searxng.sh install buildhost


To build the docs on a buildhost :ref:`buildhosts`:

.. tabs::

  .. group-tab:: ``[root@searxng-archlinux SearXNG]`` (GUEST)

     .. code:: bash

        $ make docs.html

  .. group-tab:: desktop (HOST)

     .. code:: bash

        $ sudo -H ./utils/lxc.sh cmd searxng-archlinux make docs.html


.. _lxcdev summary:

Summary
=======

We build up a fully functional SearXNG suite in a archlinux container:

.. code:: bash

   $ sudo -H ./utils/lxc.sh build searxng-archlinux
   $ sudo -H ./utils/lxc.sh install suite searxng-archlinux
   ...
   Developer install? (wraps source from HOST into the running instance) [YES/no]

To wrap the suite into a developer one answer ``YES`` (or press Enter).

.. code:: text

   link SearXNG's sources to: /share/SearXNG
   =========================================

   mv -f "/usr/local/searxng/searxng-src" "/usr/local/searxng/searxng-src.backup"
   ln -s "/share/SearXNG" "/usr/local/searxng/searxng-src"
   ls -ld /usr/local/searxng/searxng-src
     |searxng| lrwxrwxrwx 1 searxng searxng ... /usr/local/searxng/searxng-src -> /share/SearXNG

On code modification the instance has to be restarted (see :ref:`uWSGI
maintenance`):

.. code:: bash

   $ sudo -H ./utils/lxc.sh cmd searxng-archlinux systemctl restart uwsgi@searxng

To access HTTP from the desktop we installed nginx for the services inside the
container:

.. code:: bash

   $ sudo -H ./utils/lxc.sh cmd -- FORCE_TIMEOUT=0 ./utils/searxng.sh install nginx

To get information about the SearxNG suite in the archlinux container we can
use:

.. code:: text

   $ sudo -H ./utils/lxc.sh show suite searxng-archlinux
   [searxng-archlinux]  INFO:  (eth0) docs-live:  http:///n.n.n.140:8080/
   [searxng-archlinux]  INFO:  (eth0) IPv6:       http://[fd42:555b:2af9:e121:216:3eff:fe5b:1744]
   [searxng-archlinux]  uWSGI:
   [searxng-archlinux]    SEARXNG_UWSGI_SOCKET : /usr/local/searxng/run/socket
   [searxng-archlinux]  environment /usr/local/searxng/searxng-src/utils/brand.env:
   [searxng-archlinux]    GIT_URL              : https://github.com/searxng/searxng
   [searxng-archlinux]    GIT_BRANCH           : master
   [searxng-archlinux]    SEARXNG_URL          : http:///n.n.n.140/searxng
   [searxng-archlinux]    SEARXNG_PORT         : 8888
   [searxng-archlinux]    SEARXNG_BIND_ADDRESS : 127.0.0.1

