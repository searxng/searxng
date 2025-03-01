==================
Runtime Management
==================

The runtimes are managed with asdf and are activated in this project via the
`.tool-versions <.tool-versions>`_. If you have not yet installed asdf_, then
chapter :ref:`introduce asdf` may be of help to you.

.. contents::
   :depth: 2
   :local:
   :backlinks: entry


Get started
===========

If you have asdf installed you can install the runtimes of this project by:

.. code:: bash

   $ cd /path/to/searxng
   $ asdf install          # will install runtimes listed in .tool-versions
   ...

Manage Versions
===============

If you want to perform a ``test`` with special runtime versions of nodejs,
python or shellcheck, you can patch the ``.tool-versions``:

.. code:: diff

   --- a/.tool-versions
   +++ b/.tool-versions
   @@ -1,2 +1,2 @@
   -python 3.12.0
   -shellcheck 0.9.0
   +python 3.11.6
   +shellcheck 0.8.0

To install use ``asdf install`` again.  If the runtime tools have changed, any
existing (nodejs and python) environments should be cleaned up with a ``make
clean``.

.. code:: bash

   $ asdf install
   ...
   $ make clean test


.. _introduce asdf:

Introduce asdf
==============

To `download asdf`_ and `install asdf`_:

.. code:: bash

   $ git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch <version>
   $ echo '. "$HOME/.asdf/asdf.sh"' >> ~/.bashrc
   $ echo '. "$HOME/.asdf/completions/asdf.bash"' >> ~/.bashrc

Start a new shell and try to `install plugins`_:

.. code:: bash

   $ asdf plugin-list-all | grep -E '(golang|python|nodejs|shellcheck).git'
   golang                        https://github.com/asdf-community/asdf-golang.git
   nodejs                        https://github.com/asdf-vm/asdf-nodejs.git
   python                        https://github.com/danhper/asdf-python.git
   shellcheck                    https://github.com/luizm/asdf-shellcheck.git

   $ asdf plugin add golang https://github.com/asdf-community/asdf-golang.git
   $ asdf plugin add nodejs https://github.com/asdf-vm/asdf-nodejs.git
   $ asdf plugin add python https://github.com/danhper/asdf-python.git
   $ asdf plugin add shellcheck https://github.com/luizm/asdf-shellcheck.git

Each plugin has dependencies, to compile runtimes visit the URLs from above and
look out for the dependencies you need to install on your OS, on Debian for the
runtimes listed above you will need:

.. code:: bash

  $ sudo apt update
  $ sudo apt install \
         dirmngr gpg curl gawk coreutils build-essential libssl-dev zlib1g-dev \
         libbz2-dev libreadline-dev libsqlite3-dev \
         libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

With dependencies installed you can install/compile runtimes:

.. code:: bash

  $ asdf install golang latest
  $ asdf install nodejs latest
  $ asdf install python latest
  $ asdf install shellcheck latest

Python will be compiled and will take a while.

In the repository the version is defined in `.tool-versions`_. Outside the
repository, its recommended that the runtime should use the versions of the OS
(`Fallback to System Version`_) / if not already done register the system
versions global:

.. code:: bash

   $ cd /
   $ asdf global golang system
   $ asdf global nodejs system
   $ asdf global python system
   $ asdf global shellcheck system

.. _asdf: https://asdf-vm.com/
.. _download asdf: https://asdf-vm.com/guide/getting-started.html#_2-download-asdf
.. _install asdf: https://asdf-vm.com/guide/getting-started.html#_3-install-asdf
.. _install plugins: https://asdf-vm.com/guide/getting-started.html#install-the-plugin
.. _Fallback to System Version: https://asdf-vm.com/manage/versions.html#fallback-to-system-version
