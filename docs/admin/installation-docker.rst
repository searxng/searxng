
.. _installation docker:

===================
Docker installation
===================

.. _ENTRYPOINT: https://docs.docker.com/engine/reference/builder/#entrypoint
.. _searxng-docker: https://github.com/searxng/searxng-docker
.. _[filtron]: https://hub.docker.com/r/dalf/filtron
.. _[morty]: https://hub.docker.com/r/dalf/morty
.. _[caddy]: https://hub.docker.com/_/caddy

.. sidebar:: info

   - :origin:`Dockerfile`
   - `searxng/searxng @dockerhub <https://hub.docker.com/r/searxng/searxng>`_
   - `Docker overview <https://docs.docker.com/get-started/overview>`_
   - `Docker Cheat Sheet <https://www.docker.com/sites/default/files/d8/2019-09/docker-cheat-sheet.pdf>`_
   - `Alpine Linux <https://alpinelinux.org>`_ `(wiki) <https://en.wikipedia.org/wiki/Alpine_Linux>`__ `apt packages <https://pkgs.alpinelinux.org/packages>`_
   - Alpine's ``/bin/sh`` is :man:`dash`

.. tip::

   If you intend to create a public instance using Docker, use our well
   maintained searxng-docker_ image which includes

   - :ref:`protection <searxng filtron>` `[filtron]`_,
   - a :ref:`result proxy <searxng morty>` `[morty]`_ and
   - a HTTPS reverse proxy `[caddy]`_.

Make sure you have `installed Docker <https://docs.docker.com/get-docker/>`_ and
on Linux, don't forget to add your user to the docker group (log out and log
back in so that your group membership is re-evaluated):

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
stoped.  To get rid of a container use ``container rm``:

.. code:: sh

   $ docker container ls
   CONTAINER ID   IMAGE             COMMAND                  CREATED         ...
   2f998d725993   searxng/searxng   "/sbin/tini -- /usr/…"   7 minutes ago   ...

   $ docker container stop 2f998
   $ docker container rm 2f998

.. sidebar:: Warning

   This might remove all docker items, not only those from SearXNG.

If you won't use docker anymore and want to get rid of all conatiners & images
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

Like in many other distributions, Alpine's `/bin/sh
<https://wiki.ubuntu.com/DashAsBinSh>`__ is :man:`dash`.  Dash is meant to be
`POSIX-compliant <https://pubs.opengroup.org/onlinepubs/9699919799>`__.
Compared to debian, in the Alpine image :man:`bash` is not installed.  The
:origin:`dockerfiles/docker-entrypoint.sh` script is checked *against dash*
(``make tests.shell``).

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
:origin:`dockerfiles/docker-entrypoint.sh`

.. code:: sh

    docker run --rm -it searxng/searxng -h

.. program-output:: ../dockerfiles/docker-entrypoint.sh -h
