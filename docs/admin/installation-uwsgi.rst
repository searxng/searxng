.. _searxng uwsgi:

=====
uWSGI
=====

.. sidebar:: further reading

   - `systemd.unit`_
   - `uWSGI Emperor`_

.. contents:: Contents
   :depth: 2
   :local:
   :backlinks: entry


.. _systemd.unit: https://www.freedesktop.org/software/systemd/man/systemd.unit.html
.. _One service per app in systemd:
    https://uwsgi-docs.readthedocs.io/en/latest/Systemd.html#one-service-per-app-in-systemd
.. _uWSGI Emperor:
    https://uwsgi-docs.readthedocs.io/en/latest/Emperor.html
.. _uwsgi ini file:
   https://uwsgi-docs.readthedocs.io/en/latest/Configuration.html#ini-files
.. _systemd unit template:
   http://0pointer.de/blog/projects/instances.html


Origin uWSGI
============

.. _Tyrant mode:
   https://uwsgi-docs.readthedocs.io/en/latest/Emperor.html#tyrant-mode-secure-multi-user-hosting

How uWSGI is implemented by distributors varies. The uWSGI project itself
recommends two methods:

1. `systemd.unit`_ template file as described here `One service per app in systemd`_:

  There is one `systemd unit template`_ on the system installed and one `uwsgi
  ini file`_ per uWSGI-app placed at dedicated locations.  Take archlinux and a
  ``searxng.ini`` as example::

    systemd template unit: /usr/lib/systemd/system/uwsgi@.service
            contains: [Service]
                      ExecStart=/usr/bin/uwsgi --ini /etc/uwsgi/%I.ini

    SearXNG application:   /etc/uwsgi/searxng.ini
            links to: /etc/uwsgi/apps-available/searxng.ini

  The SearXNG app (template ``/etc/uwsgi/%I.ini``) can be maintained as known
  from common systemd units:

  .. code:: sh

     $ systemctl enable  uwsgi@searxng
     $ systemctl start   uwsgi@searxng
     $ systemctl restart uwsgi@searxng
     $ systemctl stop    uwsgi@searxng

2. The `uWSGI Emperor`_ which fits for maintaining a large range of uwsgi
   apps and there is a `Tyrant mode`_ to secure multi-user hosting.

  The Emperor mode is a special uWSGI instance that will monitor specific
  events.  The Emperor mode (the service) is started by a (common, not template)
  systemd unit.

  The Emperor service will scan specific directories for `uwsgi ini file`_\s
  (also know as *vassals*).  If a *vassal* is added, removed or the timestamp is
  modified, a corresponding action takes place: a new uWSGI instance is started,
  reload or stopped.  Take Fedora and a ``searxng.ini`` as example::

    to install & start SearXNG instance create --> /etc/uwsgi.d/searxng.ini
    to reload the instance edit timestamp      --> touch /etc/uwsgi.d/searxng.ini
    to stop instance remove ini                --> rm /etc/uwsgi.d/searxng.ini


Distributors
============

The `uWSGI Emperor`_ mode and `systemd unit template`_ is what the distributors
mostly offer their users, even if they differ in the way they implement both
modes and their defaults.  Another point they might differ in is the packaging of
plugins (if so, compare :ref:`install packages`) and what the default python
interpreter is (python2 vs. python3).

While archlinux does not start a uWSGI service by default, Fedora (RHEL) starts
a Emperor in `Tyrant mode`_ by default (you should have read :ref:`uWSGI Tyrant
mode pitfalls`).  Worth to know; debian (ubuntu) follow a complete different
approach, read see :ref:`Debian's uWSGI layout`.

.. _Debian's uWSGI layout:

Debian's uWSGI layout
---------------------

.. _uwsgi.README.Debian:
    https://salsa.debian.org/uwsgi-team/uwsgi/-/raw/debian/latest/debian/uwsgi.README.Debian

Be aware, Debian's uWSGI layout is quite different from the standard uWSGI
configuration.  Your are familiar with :ref:`Debian's Apache layout`? .. they do a
similar thing for the uWSGI infrastructure. The folders are::

    /etc/uwsgi/apps-available/
    /etc/uwsgi/apps-enabled/

The `uwsgi ini file`_ is enabled by a symbolic link::

  ln -s /etc/uwsgi/apps-available/searxng.ini /etc/uwsgi/apps-enabled/

More details can be found in the uwsgi.README.Debian_
(``/usr/share/doc/uwsgi/README.Debian.gz``).  Some commands you should know on
Debian:

.. code:: none

    Commands recognized by init.d script
    ====================================

    You can issue to init.d script following commands:
      * start        | starts daemon
      * stop         | stops daemon
      * reload       | sends to daemon SIGHUP signal
      * force-reload | sends to daemon SIGTERM signal
      * restart      | issues 'stop', then 'start' commands
      * status       | shows status of daemon instance (running/not running)

    'status' command must be issued with exactly one argument: '<confname>'.

    Controlling specific instances of uWSGI
    =======================================

    You could control specific instance(s) by issuing:

        SYSTEMCTL_SKIP_REDIRECT=1 service uwsgi <command> <confname> <confname>...

    where:
      * <command> is one of 'start', 'stop' etc.
      * <confname> is the name of configuration file (without extension)

    For example, this is how instance for /etc/uwsgi/apps-enabled/hello.xml is
    started:

        SYSTEMCTL_SKIP_REDIRECT=1 service uwsgi start hello


.. _uWSGI maintenance:

uWSGI maintenance
=================

.. tabs::

   .. group-tab:: Ubuntu / debian

      .. kernel-include:: $DOCS_BUILD/includes/searxng.rst
         :start-after: START searxng uwsgi-description ubuntu-20.04
         :end-before: END searxng uwsgi-description ubuntu-20.04

   .. hotfix: a bug group-tab need this comment

   .. group-tab:: Arch Linux

      .. kernel-include:: $DOCS_BUILD/includes/searxng.rst
         :start-after: START searxng uwsgi-description arch
         :end-before: END searxng uwsgi-description arch

   .. hotfix: a bug group-tab need this comment

   .. group-tab::  Fedora / RHEL

      .. kernel-include:: $DOCS_BUILD/includes/searxng.rst
         :start-after: START searxng uwsgi-description fedora
         :end-before: END searxng uwsgi-description fedora


.. _uwsgi setup:

uWSGI setup
===========

Create the configuration ini-file according to your distribution and restart the
uwsgi application.  As shown below, the :ref:`installation scripts` installs by
default:

- a uWSGI setup that listens on a socket and
- enables :ref:`cache busting <static_use_hash>`.

.. tabs::

   .. group-tab:: Ubuntu / debian

      .. kernel-include:: $DOCS_BUILD/includes/searxng.rst
         :start-after: START searxng uwsgi-appini ubuntu-20.04
         :end-before: END searxng uwsgi-appini ubuntu-20.04

   .. hotfix: a bug group-tab need this comment

   .. group-tab:: Arch Linux

      .. kernel-include:: $DOCS_BUILD/includes/searxng.rst
         :start-after: START searxng uwsgi-appini arch
         :end-before: END searxng uwsgi-appini arch

   .. hotfix: a bug group-tab need this comment

   .. group-tab::  Fedora / RHEL

      .. kernel-include:: $DOCS_BUILD/includes/searxng.rst
         :start-after: START searxng uwsgi-appini fedora
         :end-before: END searxng uwsgi-appini fedora


.. _uWSGI Tyrant mode pitfalls:

Pitfalls of the Tyrant mode
===========================

The implementation of the process owners and groups in the `Tyrant mode`_ is
somewhat unusual and requires special consideration.  In `Tyrant mode`_ mode the
Emperor will run the vassal using the UID/GID of the vassal configuration file
(user and group of the app ``.ini`` file).

.. _#2099@uWSGI: https://github.com/unbit/uwsgi/issues/2099
.. _#752@uWSGI: https://github.com/unbit/uwsgi/pull/752
.. _#2425uWSGI: https://github.com/unbit/uwsgi/issues/2425

Without option ``emperor-tyrant-initgroups=true`` in ``/etc/uwsgi.ini`` the
process won't get the additional groups, but this option is not available in
2.0.x branch (see `#2099@uWSGI`_) the feature `#752@uWSGI`_ has been merged (on
Oct. 2014) to the master branch of uWSGI but had never been released; the last
major release is from Dec. 2013, since the there had been only bugfix releases
(see `#2425uWSGI`_). To shorten up:

  **In Tyrant mode, there is no way to get additional groups, and the uWSGI
  process misses additional permissions that may be needed.**

For example on Fedora (RHEL): If you try to install a redis DB with socket
communication and you want to connect to it from the SearXNG uWSGI, you will see a
*Permission denied* in the log of your instance::

  ERROR:searx.shared.redis: [searxng (993)] can't connect redis DB ...
  ERROR:searx.shared.redis:   Error 13 connecting to unix socket: /usr/local/searxng-redis/run/redis.sock. Permission denied.
  ERROR:searx.plugins.limiter: init limiter DB failed!!!

Even if your *searxng* user of the uWSGI process is added to additional groups
to give access to the socket from the redis DB::

  $ groups searxng
  searxng : searxng searxng-redis

To see the effective groups of the uwsgi process, you have to look at the status
of the process, by example::

  $ ps -aef | grep '/usr/sbin/uwsgi --ini searxng.ini'
  searxng       93      92  0 12:43 ?        00:00:00 /usr/sbin/uwsgi --ini searxng.ini
  searxng      186      93  0 12:44 ?        00:00:01 /usr/sbin/uwsgi --ini searxng.ini

Here you can see that the additional "Groups" of PID 186 are unset (missing gid
of ``searxng-redis``)::

  $ cat /proc/186/task/186/status
  ...
  Uid:      993     993     993     993
  Gid:      993     993     993     993
  FDSize:   128
  Groups:
  ...
