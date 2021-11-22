.. START create user

.. tabs::

  .. group-tab:: bash

    .. code-block:: sh

      $ sudo -H useradd --shell /bin/bash --system \\
          --home-dir \"$SERVICE_HOME\" \\
          --comment \"Privacy-respecting metasearch engine\" $SERVICE_USER

      $ sudo -H mkdir \"$SERVICE_HOME\"
      $ sudo -H chown -R \"$SERVICE_GROUP:$SERVICE_GROUP\" \"$SERVICE_HOME\"

.. END create user

.. START install go

.. tabs::

  .. group-tab:: os: linux / arch: amd64


    .. code-block:: bash

       $ cat > \"$GO_ENV\" <<EOF
       export GOPATH=${SERVICE_HOME}/go-apps
       export PATH=\$PATH:${SERVICE_HOME}/local/go/bin:\$GOPATH/bin
       EOF
       $ sudo -i -u \"${SERVICE_USER}\"
       (${SERVICE_USER}) $ echo 'source $GO_ENV' >> ~/.profile
       (${SERVICE_USER}) $ mkdir ${SERVICE_HOME}/local
       (${SERVICE_USER}) $ wget --progress=bar -O \"${GO_VERSION}.linux-amd64.tar.gz\" \\
                   \"${GO_DL_URL}/${GO_VERSION}.linux-amd64.tar.gz\"
       (${SERVICE_USER}) $ tar -C ${SERVICE_HOME}/local -xzf \"${GO_VERSION}.linux-amd64.tar.gz\"
       (${SERVICE_USER}) $ which go
       ${SERVICE_HOME}/local/go/bin/go

.. END install go

.. START install filtron

.. tabs::

  .. group-tab:: bash

    .. code-block:: bash

       $ sudo -i -u \"${SERVICE_USER}\"
       (${SERVICE_USER}) $ go get -v -u github.com/searxng/filtron

.. END install filtron
