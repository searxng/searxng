.. _installation nginx:

=====
NGINX
=====

.. _nginx:
   https://docs.nginx.com/nginx/admin-guide/
.. _nginx server configuration:
   https://docs.nginx.com/nginx/admin-guide/web-server/web-server/#setting-up-virtual-servers
.. _nginx beginners guide:
   https://nginx.org/en/docs/beginners_guide.html
.. _Getting Started wiki:
   https://www.nginx.com/resources/wiki/start/
.. _uWSGI support from nginx:
   https://uwsgi-docs.readthedocs.io/en/latest/Nginx.html
.. _uwsgi_params:
   https://uwsgi-docs.readthedocs.io/en/latest/Nginx.html#configuring-nginx
.. _SCRIPT_NAME:
   https://werkzeug.palletsprojects.com/en/1.0.x/wsgi/#werkzeug.wsgi.get_script_name

This section explains how to set up a SearXNG instance using the HTTP server nginx_.
If you have used the :ref:`installation scripts` and do not have any special preferences
you can install the :ref:`SearXNG site <nginx searxng site>` using
:ref:`searxng.sh <searxng.sh overview>`:

.. code:: bash

   $ sudo -H ./utils/searxng.sh install nginx

If you have special interests or problems with setting up nginx, the following
section might give you some guidance.


.. sidebar:: further reading

   - nginx_
   - `nginx beginners guide`_
   - `nginx server configuration`_
   - `Getting Started wiki`_
   - `uWSGI support from nginx`_


.. contents::
   :depth: 2
   :local:
   :backlinks: entry


The nginx HTTP server
=====================

If nginx_ is not installed, install it now.

.. tabs::

   .. group-tab:: Ubuntu / debian

      .. code:: bash

         sudo -H apt-get install nginx

   .. group-tab:: Arch Linux

      .. code-block:: sh

         sudo -H pacman -S nginx-mainline
         sudo -H systemctl enable nginx
         sudo -H systemctl start nginx

   .. group-tab::  Fedora / RHEL

      .. code-block:: sh

         sudo -H dnf install nginx
         sudo -H systemctl enable nginx
         sudo -H systemctl start nginx

Now at http://localhost you should see a *Welcome to nginx!* page, on Fedora you
see a *Fedora Webserver - Test Page*.  The test page comes from the default
`nginx server configuration`_.  How this default site is configured,
depends on the linux distribution:

.. tabs::

   .. group-tab:: Ubuntu / debian

      .. code:: bash

         less /etc/nginx/nginx.conf

      There is one line that includes site configurations from:

      .. code:: nginx

         include /etc/nginx/sites-enabled/*;

   .. group-tab:: Arch Linux

      .. code-block:: sh

         less /etc/nginx/nginx.conf

      There is a configuration section named ``server``:

      .. code-block:: nginx

         server {
             listen       80;
             server_name  localhost;
             # ...
         }

   .. group-tab::  Fedora / RHEL

      .. code-block:: sh

         less /etc/nginx/nginx.conf

      There is one line that includes site configurations from:

      .. code:: nginx

          include /etc/nginx/conf.d/*.conf;


.. _nginx searxng site:

NGINX's SearXNG site
====================

Now you have to create a configuration file (``searxng.conf``) for the SearXNG
site.  If nginx_ is new to you, the `nginx beginners guide`_ is a good starting
point and the `Getting Started wiki`_ is always a good resource *to keep in the
pocket*.

Depending on what your SearXNG installation is listening on, you need a http or socket
communication to upstream.

.. tabs::

   .. group-tab:: socket

      .. kernel-include:: $DOCS_BUILD/includes/searxng.rst
         :start-after: START nginx socket
         :end-before: END nginx socket

   .. group-tab:: http

      .. kernel-include:: $DOCS_BUILD/includes/searxng.rst
         :start-after: START nginx http
         :end-before: END nginx http

The :ref:`installation scripts` installs the :ref:`reference setup
<use_default_settings.yml>` and a :ref:`uwsgi setup` that listens on a socket by default.

.. tabs::

   .. group-tab:: Ubuntu / debian

      Create configuration at ``/etc/nginx/sites-available/`` and place a
      symlink to ``sites-enabled``:

      .. code:: bash

         sudo -H ln -s /etc/nginx/sites-available/searxng.conf \
                       /etc/nginx/sites-enabled/searxng.conf

   .. group-tab:: Arch Linux

      In the ``/etc/nginx/nginx.conf`` file, in the ``server`` section add a
      `include <https://nginx.org/en/docs/ngx_core_module.html#include>`_
      directive:

      .. code:: nginx

         server {
             # ...
             include /etc/nginx/default.d/*.conf;
             # ...
         }

      Create two folders, one for the *available sites* and one for the *enabled sites*:

      .. code:: bash

         mkdir -p /etc/nginx/default.d
         mkdir -p /etc/nginx/default.apps-available

      Create configuration at ``/etc/nginx/default.apps-available`` and place a
      symlink to ``default.d``:

      .. code:: bash

         sudo -H ln -s /etc/nginx/default.apps-available/searxng.conf \
                       /etc/nginx/default.d/searxng.conf

   .. group-tab::  Fedora / RHEL

      Create a folder for the *available sites*:

      .. code:: bash

         mkdir -p /etc/nginx/default.apps-available

      Create configuration at ``/etc/nginx/default.apps-available`` and place a
      symlink to ``conf.d``:

      .. code:: bash

         sudo -H ln -s /etc/nginx/default.apps-available/searxng.conf \
                       /etc/nginx/conf.d/searxng.conf

Restart services:

.. tabs::

   .. group-tab:: Ubuntu / debian

      .. code:: bash

         sudo -H systemctl restart nginx
         sudo -H service uwsgi restart searxng

   .. group-tab:: Arch Linux

      .. code:: bash

         sudo -H systemctl restart nginx
         sudo -H systemctl restart uwsgi@searxng

   .. group-tab:: Fedora / RHEL

      .. code:: bash

         sudo -H systemctl restart nginx
         sudo -H touch /etc/uwsgi.d/searxng.ini


Disable logs
============

For better privacy you can disable nginx logs in ``/etc/nginx/nginx.conf``.

.. code:: nginx

    http {
        # ...
        access_log /dev/null;
        error_log  /dev/null;
        # ...
    }
