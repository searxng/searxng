.. _installation docker:

================
Docker Container
================

.. _ENTRYPOINT: https://docs.docker.com/engine/reference/builder/#entrypoint
.. _searxng/searxng @dockerhub: https://hub.docker.com/r/searxng/searxng
.. _searxng-docker: https://github.com/searxng/searxng-docker
.. _[caddy]: https://hub.docker.com/_/caddy
.. _Redis: https://redis.io/

----

.. sidebar:: info

   - `searxng/searxng @dockerhub`_
   - :origin:`Dockerfile`
   - `Docker overview <https://docs.docker.com/get-started/overview>`_
   - `Docker Cheat Sheet <https://docs.docker.com/get-started/docker_cheatsheet.pdf>`_
   - `Alpine Linux <https://alpinelinux.org>`_
     `(wiki) <https://en.wikipedia.org/wiki/Alpine_Linux>`__
     `apt packages <https://pkgs.alpinelinux.org/packages>`_
   - Alpine's ``/bin/sh`` is :man:`dash`

**If you intend to create a public instance using Docker, use our well maintained
docker container**

- `searxng/searxng @dockerhub`_.

.. sidebar:: hint

   The rest of this article is of interest only to those who want to create and
   maintain their own Docker images.

The sources are hosted at searxng-docker_ and the container includes:

- a HTTPS reverse proxy `[caddy]`_ and
- a Redis_ DB

The `default SearXNG setup <https://github.com/searxng/searxng-docker/blob/master/searxng/settings.yml>`_
of this container:

- enables :ref:`limiter <limiter>` to protect against bots
- enables :ref:`image proxy <image_proxy>` for better privacy
- enables :ref:`cache busting <static_use_hash>` to save bandwidth

----


Get Docker
==========

If you plan to build and maintain a docker image by yourself, make sure you have
`Docker installed <https://docs.docker.com/get-docker/>`_. On Linux don't
forget to add your user to the docker group (log out and log back in so that
your group membership is re-evaluated):

.. code:: sh

   $ sudo usermod -a -G docker $USER


searxng/searxng
===============

.. sidebar:: ``docker run``

   - `-\-rm  <https://docs.docker.com/engine/reference/run/#clean-up---rm>`__
     automatically clean up when container exits
   - `-d <https://docs.docker.com/engine/reference/run/#detached--d>`__ start
     detached container
   - `-v <https://docs.docker.com/engine/reference/run/#volume-shared-filesystems>`__
     mount volume ``HOST:CONTAINER``

The docker image is based on :origin:`Dockerfile` and available from
`searxng/searxng @dockerhub`_.  Using the docker image is quite easy, for
instance you can pull the `searxng/searxng @dockerhub`_ image and deploy a local
instance using `docker run <https://docs.docker.com/engine/reference/run/>`_:

.. code:: sh

   $ mkdir my-instance
   $ cd my-instance
   $ export PORT=8080
   $ docker pull searxng/searxng
   $ docker run --rm \
                -d -p ${PORT}:8080 \
                -v "${PWD}/searxng:/etc/searxng" \
                -e "BASE_URL=http://localhost:$PORT/" \
                -e "INSTANCE_NAME=my-instance" \
                searxng/searxng
   2f998.... # container's ID

The environment variables UWSGI_WORKERS and UWSGI_THREADS overwrite the default
number of UWSGI processes and UWSGI threads specified in `/etc/searxng/uwsgi.ini`.

Open your WEB browser and visit the URL:

.. code:: sh

   $ xdg-open "http://localhost:$PORT"

Inside ``${PWD}/searxng``, you will find ``settings.yml`` and ``uwsgi.ini``.  You
can modify these files according to your needs and restart the Docker image.

.. code:: sh

   $ docker container restart 2f998

Use command ``container ls`` to list running containers, add flag `-a
<https://docs.docker.com/engine/reference/commandline/container_ls>`__ to list
exited containers also.  With ``container stop`` a running container can be
stopped.  To get rid of a container use ``container rm``:

.. code:: sh

   $ docker container ls
   CONTAINER ID   IMAGE             COMMAND                  CREATED         ...
   2f998d725993   searxng/searxng   "/sbin/tini -- /usr/…"   7 minutes ago   ...

   $ docker container stop 2f998
   $ docker container rm 2f998

.. sidebar:: Warning

   This might remove all docker items, not only those from SearXNG.

If you won't use docker anymore and want to get rid of all containers & images
use the following *prune* command:

.. code:: sh

   $ docker stop $(docker ps -aq)       # stop all containers
   $ docker system prune                # make some housekeeping
   $ docker rmi -f $(docker images -q)  # drop all images


shell inside container
----------------------

.. sidebar:: Bashism

   - `A tale of two shells: bash or dash <https://lwn.net/Articles/343924/>`_
   - `How to make bash scripts work in dash <http://mywiki.wooledge.org/Bashism>`_
   - `Checking for Bashisms  <https://dev.to/bowmanjd/writing-bash-scripts-that-are-not-only-bash-checking-for-bashisms-and-testing-with-dash-1bli>`_

To open a shell inside the container:

.. code:: sh

   $ docker exec -it 2f998 sh


Build the image
===============

It's also possible to build SearXNG from the embedded :origin:`Dockerfile`::

   $ git clone https://github.com/searxng/searxng.git
   $ cd searxng
   $ make docker.build
   ...
   Successfully built 49586c016434
   Successfully tagged searxng/searxng:latest
   Successfully tagged searxng/searxng:1.0.0-209-9c823800-dirty

   $ docker images
   REPOSITORY        TAG                        IMAGE ID       CREATED          SIZE
   searxng/searxng   1.0.0-209-9c823800-dirty   49586c016434   13 minutes ago   308MB
   searxng/searxng   latest                     49586c016434   13 minutes ago   308MB
   alpine            3.13                       6dbb9cc54074   3 weeks ago      5.61MB


Command line
============

.. sidebar:: docker run

   Use flags ``-it`` for `interactive processes
   <https://docs.docker.com/engine/reference/run/#foreground>`__.

In the :origin:`Dockerfile` the ENTRYPOINT_ is defined as
:origin:`container/entrypoint.sh`

.. code:: sh

    docker run --rm -it searxng/searxng -h

.. program-output:: ../container/entrypoint.sh -h
