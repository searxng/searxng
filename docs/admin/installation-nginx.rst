.. _installation nginx:

==================
Install with nginx
==================

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

.. sidebar:: further reading

   - nginx_
   - `nginx beginners guide`_
   - `nginx server configuration`_
   - `Getting Started wiki`_
   - `uWSGI support from nginx`_

.. contents:: Contents
   :depth: 2
   :local:
   :backlinks: entry

----

**Install** :ref:`nginx searxng site` using :ref:`filtron.sh <filtron.sh overview>`

.. code:: bash

   $ sudo -H ./utils/filtron.sh nginx install

**Install** :ref:`nginx searxng site` using :ref:`morty.sh <morty.sh overview>`

.. code:: bash

   $ sudo -H ./utils/morty.sh nginx install

----


The nginx HTTP server
=====================

If nginx_ is not installed (uwsgi will not work with the package nginx-light),
install it now.

.. tabs::

   .. group-tab:: Ubuntu / debian

      .. code:: sh

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
`nginx server configuration`_.  How this default intro site is configured,
depends on the linux distribution:

.. tabs::

   .. group-tab:: Ubuntu / debian

      .. code:: sh

         less /etc/nginx/nginx.conf

      there is a line including site configurations from:

      .. code:: nginx

         include /etc/nginx/sites-enabled/*;

   .. group-tab:: Arch Linux

      .. code-block:: sh

         less /etc/nginx/nginx.conf

      in there is a configuration section named ``server``:

      .. code-block:: nginx

         server {
             listen       80;
             server_name  localhost;
             # ...
         }

   .. group-tab::  Fedora / RHEL

      .. code-block:: sh

         less /etc/nginx/nginx.conf

      there is a line including site configurations from:

      .. code:: nginx

          include /etc/nginx/conf.d/*.conf;

.. _nginx searxng site:

A nginx SearXNG site
====================

.. sidebar:: public to the internet?

   If your SearXNG instance is public, stop here and first install :ref:`filtron
   reverse proxy <filtron.sh>` and :ref:`result proxy morty <morty.sh>`, see
   :ref:`installation scripts`.  If already done, follow setup: *SearXNG via
   filtron plus morty*.

Now you have to create a configuration for the SearXNG site.  If nginx_ is new to
you, the `nginx beginners guide`_ is a good starting point and the `Getting
Started wiki`_ is always a good resource *to keep in the pocket*.

.. tabs::

   .. group-tab:: Ubuntu / debian

      Create configuration at ``/etc/nginx/sites-available/searxng`` and place a
      symlink to sites-enabled:

      .. code:: sh

         sudo -H ln -s /etc/nginx/sites-available/searxng /etc/nginx/sites-enabled/searxng

   .. group-tab:: Arch Linux

      In the ``/etc/nginx/nginx.conf`` file, replace the configuration section
      named ``server``.

   .. group-tab::  Fedora / RHEL

      Create configuration at ``/etc/nginx/conf.d/searxng`` and place a
      symlink to sites-enabled:

.. _nginx searxng via filtron plus morty:

.. tabs::

   .. group-tab:: SearXNG via filtron plus morty

      Use this setup, if your instance is public to the internet, compare
      figure: :ref:`architecture <arch public>` and :ref:`installation scripts`.

      1. Configure a reverse proxy for :ref:`filtron <filtron.sh>`, listening on
         *localhost 4004* (:ref:`filtron route request`):

      .. code:: nginx

	 # https://example.org/searx

	 location /searx {
	     proxy_pass         http://127.0.0.1:4004/;

	     proxy_set_header   Host             $host;
	     proxy_set_header   Connection       $http_connection;
	     proxy_set_header   X-Real-IP        $remote_addr;
	     proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
	     proxy_set_header   X-Scheme         $scheme;
	     proxy_set_header   X-Script-Name    /searx;
	 }

	 location /searx/static/ {
	     alias /usr/local/searx/searx-src/searx/static/;
	 }


      2. Configure reverse proxy for :ref:`morty <searxng morty>`, listening on
         *localhost 3000*:

      .. code:: nginx

	 # https://example.org/morty

	 location /morty {
             proxy_pass         http://127.0.0.1:3000/;

             proxy_set_header   Host             $host;
             proxy_set_header   Connection       $http_connection;
             proxy_set_header   X-Real-IP        $remote_addr;
             proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
             proxy_set_header   X-Scheme         $scheme;
         }

      For a fully result proxification add :ref:`morty's <searxng morty>` **public
      URL** to your :origin:`searx/settings.yml`:

      .. code:: yaml

         result_proxy:
             # replace example.org with your server's public name
             url : https://example.org/morty
             key : !!binary "insert_your_morty_proxy_key_here"

         server:
             image_proxy : True


   .. group-tab:: proxy or uWSGI

      Be warned, with this setup, your instance isn't :ref:`protected <searxng
      filtron>`.  Nevertheless it is good enough for intranet usage and it is a
      excellent example of; *how different services can be set up*.  The next
      example shows a reverse proxy configuration wrapping the :ref:`searx-uWSGI
      application <uwsgi configuration>`, listening on ``http =
      127.0.0.1:8888``.

      .. code:: nginx

	 # https://hostname.local/

	 location / {
	     proxy_pass http://127.0.0.1:8888;

             proxy_set_header Host $host;
             proxy_set_header Connection       $http_connection;
             proxy_set_header X-Forwarded-For  $proxy_add_x_forwarded_for;
             proxy_set_header X-Scheme         $scheme;
             proxy_buffering                   off;
         }

      Alternatively you can use the `uWSGI support from nginx`_ via unix
      sockets.  For socket communication, you have to activate ``socket =
      /run/uwsgi/app/searx/socket`` and comment out the ``http =
      127.0.0.1:8888`` configuration in your :ref:`uwsgi ini file <uwsgi
      configuration>`.

      The example shows a nginx virtual ``server`` configuration, listening on
      port 80 (IPv4 and IPv6 http://[::]:80).  The uWSGI app is configured at
      location ``/`` by importing the `uwsgi_params`_ and passing requests to
      the uWSGI socket (``uwsgi_pass``).  The ``server``\'s root points to the
      :ref:`searx-src clone <searx-src>` and wraps directly the
      :origin:`searx/static/` content at ``location /static``.

      .. code:: nginx

         server {
             # replace hostname.local with your server's name
             server_name hostname.local;

             listen 80;
             listen [::]:80;

             location / {
                 include uwsgi_params;
                 uwsgi_pass unix:/run/uwsgi/app/searx/socket;
             }

             root /usr/local/searx/searx-src/searx;
             location /static { }
         }

      If not already exists, create a folder for the unix sockets, which can be
      used by the SearXNG account:

      .. code:: bash

         mkdir -p /run/uwsgi/app/searx/
         sudo -H chown -R searx:searx /run/uwsgi/app/searx/

   .. group-tab:: \.\. at subdir URL

      Be warned, with these setups, your instance isn't :ref:`protected <searxng
      filtron>`.  The examples are just here to demonstrate how to export the
      SearXNG application from a subdirectory URL ``https://example.org/searx/``.

      .. code:: nginx

	 # https://hostname.local/searx

         location /searx {
             proxy_pass http://127.0.0.1:8888;

             proxy_set_header Host $host;
             proxy_set_header Connection       $http_connection;
             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
             proxy_set_header X-Scheme $scheme;
             proxy_set_header X-Script-Name /searx;
             proxy_buffering off;
         }

         location /searx/static/ {
             alias /usr/local/searx/searx-src/searx/static/;
         }

      The ``X-Script-Name /searx`` is needed by the SearXNG implementation to
      calculate relative URLs correct.  The next example shows a uWSGI
      configuration.  Since there are no HTTP headers in a (u)WSGI protocol, the
      value is shipped via the SCRIPT_NAME_ in the WSGI environment.

      .. code:: nginx

	 # https://hostname.local/searx

         location /searx {
             uwsgi_param SCRIPT_NAME /searx;
             include uwsgi_params;
             uwsgi_pass unix:/run/uwsgi/app/searx/socket;
         }

         location /searx/static/ {
             alias /usr/local/searx/searx-src/searx/;
         }

      For SearXNG to work correctly the ``base_url`` must be set in the
      :origin:`searx/settings.yml`.

      .. code:: yaml

         server:
             # replace example.org with your server's public name
             base_url : https://example.org/searx/


Restart service:

.. tabs::

   .. group-tab:: Ubuntu / debian

      .. code:: sh

         sudo -H systemctl restart nginx
         sudo -H service uwsgi restart searx

   .. group-tab:: Arch Linux

      .. code:: sh

         sudo -H systemctl restart nginx
         sudo -H systemctl restart uwsgi@searx

   .. group-tab:: Fedora

      .. code:: sh

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
