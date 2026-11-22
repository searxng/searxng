.. _installation freebsd:

===================
FreeBSD (community)
===================

.. attention::

   This page is community-maintained.  FreeBSD is not officially supported;
   the steps below are a starting point, not a tested installation.

SearXNG is a Python application and runs on FreeBSD.  Follow the
:ref:`installation basic` guide, with the following FreeBSD-specific notes.

Python and dependencies
=======================

Install Python 3.11 or newer, ``git`` and the build tools from ports::

   # pkg install python311 py311-pip git

Create a virtual environment and install the requirements as described in
:ref:`installation basic`.

Service
=======

FreeBSD's ``rc.d`` can run the WSGI application directly.  A minimal
``/usr/local/etc/rc.d/searxng`` script::

   #!/bin/sh
   # PROVIDE: searxng
   # REQUIRE: NETWORKING
   # KEYWORD: shutdown

   . /etc/rc.subr

   name="searxng"
   rcvar="searxng_enable"

   : ${searxng_user:="searxng"}
   : ${searxng_chdir:="/usr/local/searxng/searxng-src"}
   : ${searxng_settings:="/usr/local/searxng/config/settings.yml"}

   command="/usr/local/searxng/venv/bin/python"
   command_args="searx/webapp.py"
   procname="${command}"

   load_rc_config $name
   run_rc_command "$1"

Set ``searxng_enable="YES"`` in ``/etc/rc.conf``.

Reverse proxy
=============

The :ref:`installation nginx` or :ref:`installation apache` configuration can
be used unchanged.  When SearXNG binds to a Unix socket, point the proxy at it,
for example::

   location / {
       proxy_pass http://unix:/usr/local/searxng/run/searxng/searxng.sock;
   }

Limiter
=======

If the :ref:`limiter` rejects requests with *too many requests*, check that the
proxy forwards the client address (``X-Forwarded-For`` / ``X-Real-IP``) and
that the limiter's ``real_ip`` / ``trusted_proxies`` settings match your setup.
