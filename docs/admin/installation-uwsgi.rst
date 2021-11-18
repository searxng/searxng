.. _searxng uwsgi:

=====
uwsgi
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

How uWSGI is implemented by distributors is different.  uWSGI itself
recommend two methods

`systemd.unit`_ template files as described here `One service per app in systemd`_.

  There is one `systemd unit template`_ and one `uwsgi ini file`_ per uWSGI-app
  placed at dedicated locations.  Take archlinux and a searxng.ini as example::

    unit template    -->  /usr/lib/systemd/system/uwsgi@.service
    uwsgi ini files  -->  /etc/uwsgi/searxng.ini

  The SearXNG app can be maintained as know from common systemd units::

    systemctl enable  uwsgi@searx
    systemctl start   uwsgi@searx
    systemctl restart uwsgi@searx
    systemctl stop    uwsgi@searx

The `uWSGI Emperor`_ mode which fits for maintaining a large range of uwsgi apps.

  The Emperor mode is a special uWSGI instance that will monitor specific
  events.  The Emperor mode (service) is started by a (common, not template)
  systemd unit.  The Emperor service will scan specific directories for `uwsgi
  ini file`_\s (also know as *vassals*).  If a *vassal* is added, removed or the
  timestamp is modified, a corresponding action takes place: a new uWSGI
  instance is started, reload or stopped.  Take Fedora and a searxng.ini as
  example::

    to start a new SearXNG instance create --> /etc/uwsgi.d/searxng.ini
    to reload the instance edit timestamp  --> touch /etc/uwsgi.d/searxng.ini
    to stop instance remove ini            --> rm /etc/uwsgi.d/searxng.ini

Distributors
============

The `uWSGI Emperor`_ mode and `systemd unit template`_ is what the distributors
mostly offer their users, even if they differ in the way they implement both
modes and their defaults.  Another point they might differ is the packaging of
plugins (if so, compare :ref:`install packages`) and what the default python
interpreter is (python2 vs. python3).

Fedora starts a Emperor by default, while archlinux does not start any uwsgi
service by default.  Worth to know; debian (ubuntu) follow a complete different
approach.  *debian*: your are familiar with the apache infrastructure? .. they
do similar for the uWSGI infrastructure (with less comfort), the folders are::

    /etc/uwsgi/apps-available/
    /etc/uwsgi/apps-enabled/

The `uwsgi ini file`_ is enabled by a symbolic link::

  ln -s /etc/uwsgi/apps-available/searxng.ini /etc/uwsgi/apps-enabled/

From debian's documentation (``/usr/share/doc/uwsgi/README.Debian.gz``): You
could control specific instance(s) by issuing::

  service uwsgi <command> <confname> <confname> ...

  sudo -H service uwsgi start searx
  sudo -H service uwsgi stop  searx

My experience is, that this command is a bit buggy.

.. _uwsgi configuration:

Alltogether
===========

Create the configuration ini-file according to your distribution (see below) and
restart the uwsgi application.

.. tabs::

   .. group-tab:: Ubuntu / debian

      .. kernel-include:: $DOCS_BUILD/includes/searx.rst
         :start-after: START searxng uwsgi-description ubuntu-20.04
         :end-before: END searxng uwsgi-description ubuntu-20.04

   .. hotfix: a bug group-tab need this comment

   .. group-tab:: Arch Linux

      .. kernel-include:: $DOCS_BUILD/includes/searx.rst
         :start-after: START searxng uwsgi-description arch
         :end-before: END searxng uwsgi-description arch

   .. hotfix: a bug group-tab need this comment

   .. group-tab::  Fedora / RHEL

      .. kernel-include:: $DOCS_BUILD/includes/searx.rst
         :start-after: START searxng uwsgi-description fedora
         :end-before: END searxng uwsgi-description fedora


.. tabs::

   .. group-tab:: Ubuntu / debian

      .. kernel-include:: $DOCS_BUILD/includes/searx.rst
         :start-after: START searxng uwsgi-appini ubuntu-20.04
         :end-before: END searxng uwsgi-appini ubuntu-20.04

   .. hotfix: a bug group-tab need this comment

   .. group-tab:: Arch Linux

      .. kernel-include:: $DOCS_BUILD/includes/searx.rst
         :start-after: START searxng uwsgi-appini arch
         :end-before: END searxng uwsgi-appini arch

   .. hotfix: a bug group-tab need this comment

   .. group-tab::  Fedora / RHEL

      .. kernel-include:: $DOCS_BUILD/includes/searx.rst
         :start-after: START searxng uwsgi-appini fedora
         :end-before: END searxng uwsgi-appini fedora
