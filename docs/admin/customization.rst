.. _customization:

===================
Customization
===================

.. sidebar:: further read

   - :ref:`brand settings  <settings brand>`

.. contents::
   :depth: 2
   :local:
   :backlinks: entry

.. _searxng logo:

Changing the logo
=============

You can change the logo of the simple theme depending on the :ref:`installation` method. 

Docker
------------------------
When running inside of :ref:`installation docker`, you can use the Docker CLI or Docker-Compose

Docker CLI:

.. code:: sh

    docker run -v /path/to/image.png:/usr/local/searxng/searx/static/themes/simple/img/searxng.png -p 8888:8080 searxng/searxng


Docker-Compose (based on `mrpaulblack's solution <https://github.com/searxng/searxng-docker/discussions/57#discussioncomment-2597013>`):

.. code:: yaml
    
    services:
      searxng:
        image: searxng/searxng:latest
        volumes:
          - /path/to/image.png:/usr/local/searxng/searx/static/themes/simple/img/searxng.png

NGINX
------------------------
If you're using :ref:`installation nginx`, you can use the following solution from **roughnecks** in the searxng community chat.

.. code:: nginx

    location /searxng/static/themes/simple/img/searxng.png {
        root /var/www/html/;
        try_files /images/mylogo.png =404;
    }

Caddy
------------------------
If you're using Caddy, you can use the following solution

.. code:: caddy

    searxng.example.com {
        handle_path /static/themes/simple/img/searxng.png {
              root /srv/searxng/
              try_files {path} /banner.png =404
              file_server
        }

        reverse_proxy 127.0.0.1:8888
    }
