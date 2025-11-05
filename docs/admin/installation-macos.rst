.. _installation macos:

=========================
Installation on macOS
=========================

This guide covers SearXNG installation specifically for macOS systems, including both Apple Silicon (M1/M2/M3) and Intel-based Macs.

.. contents::
   :depth: 2
   :local:
   :backlinks: entry

Prerequisites
=============

System Requirements
-------------------

* macOS 11 (Big Sur) or later (older versions may work but are untested)
* macOS 15.7.1 (Sequoia) tested and confirmed working
* At least 4GB of RAM
* 2GB of free disk space

Required Software
-----------------

Homebrew Package Manager
~~~~~~~~~~~~~~~~~~~~~~~~

If you don't have Homebrew installed::

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

After installation, follow the instructions to add Homebrew to your PATH.

Docker Desktop for Mac
~~~~~~~~~~~~~~~~~~~~~~

Install Docker Desktop::

    brew install --cask docker

Or download directly from: https://www.docker.com/products/docker-desktop

**Important for Apple Silicon users**: Ensure you download the Apple Silicon version of Docker Desktop.

After installation:

1. Launch Docker Desktop from Applications
2. Wait for Docker to start (the whale icon in the menu bar should be steady)
3. Verify Docker is running::

    docker --version
    docker compose version

Installation Methods
====================

Method 1: Docker Installation (Recommended)
--------------------------------------------

This is the easiest method for macOS users.

For complete Docker installation instructions, please refer to the `searxng-docker documentation <https://github.com/searxng/searxng-docker>`_.

macOS-Specific Docker Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using Docker on macOS, keep these platform-specific notes in mind:

**Apple Silicon (M1/M2/M3) Users**

* Ensure you download the Apple Silicon version of Docker Desktop
* Docker Desktop automatically handles ARM64 architecture - no special configuration needed

**Volume Mounting**

Docker Desktop on macOS has specific directory requirements. Keep your projects in:

* ``~/Documents``
* ``~/Desktop``  
* ``~/Downloads``
* Or add custom paths in Docker Desktop → Settings → Resources → File Sharing

**Port Conflicts**

Check for port conflicts before starting::

    lsof -i :8080

If the port is in use, either kill the conflicting process or change the port in ``docker-compose.yml``.

Method 2: Native Installation
------------------------------

For advanced users who prefer running SearXNG natively on macOS.

Step 1: Install Python Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    brew install python3
    pip3 install --upgrade pip
    pip3 install searxng

Step 2: Clone SearXNG Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    cd ~/Documents
    git clone https://github.com/searxng/searxng.git
    cd searxng

Step 3: Install Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    pip3 install -r requirements.txt

Step 4: Run SearXNG
~~~~~~~~~~~~~~~~~~~

::

    python3 searx/webapp.py

Access at: http://localhost:8888

macOS-Specific Considerations
==============================

Apple Silicon (M1/M2/M3) Notes
------------------------------

Docker Desktop for Mac handles architecture differences automatically. No special configuration needed for ARM64 architecture.

File Permissions
----------------

If you encounter permission errors::

    sudo chown -R $(whoami) ~/Documents/searxng-docker/

Firewall Configuration
----------------------

If you're having connection issues:

1. System Settings → Network → Firewall
2. Click "Options"
3. Allow Docker Desktop
4. Allow Python (if using native installation)

Troubleshooting
===============

Docker Not Starting
-------------------

If Docker fails to start:

1. Quit Docker Desktop completely
2. Remove Docker data (optional - WARNING: removes all containers)::

    rm -rf ~/Library/Containers/com.docker.docker
    
3. Restart Docker Desktop

SearXNG Not Accessible
----------------------

If you can't access SearXNG at localhost:8080:

1. Check Docker containers are running::

    docker ps

2. Check logs::

    docker compose logs searxng

3. Verify network settings::

    docker network ls
    docker network inspect searxng-docker_default

Slow Performance on Apple Silicon
----------------------------------

If you experience slow performance:

1. Ensure you're using the ARM64 version of Docker Desktop
2. Increase Docker resources in Docker Desktop → Settings → Resources
3. Allocate at least 4GB RAM and 2 CPUs

Python Version Issues
---------------------

macOS Sequoia 15.7.1 comes with Python 3.13.5. If you encounter compatibility issues::

    brew install python@3.11
    pip3.11 install -r requirements.txt

Updating SearXNG
================

For Docker Installation
-----------------------

::

    cd ~/Documents/searxng-docker
    docker compose pull
    docker compose up -d

For Native Installation
-----------------------

::

    cd ~/Documents/searxng
    git pull origin master
    pip3 install -r requirements.txt --upgrade

Next Steps
==========

* :ref:`searxng settings`
* :ref:`buildhosts`
* Configure engines: See engine documentation
* Set up HTTPS with nginx or Apache

Additional Resources
====================

* Official Documentation: https://docs.searxng.org
* GitHub Issues: https://github.com/searxng/searxng/issues
* Community Chat: #searxng on Matrix

Contributing
============

Found an issue with these macOS instructions? Please report it on GitHub or submit a pull request!

----

**Tested on**: macOS Sequoia 15.7.1 (Build 24G231) with Apple Silicon
