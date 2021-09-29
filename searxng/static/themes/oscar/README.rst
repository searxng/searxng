install dependencies
~~~~~~~~~~~~~~~~~~~~

run this command in the directory ``searxng/static/themes/oscar``

``npm install``

compile sources
~~~~~~~~~~~~~~~

run this command in the directory ``searxng/static/themes/oscar``

``grunt``

or in the root directory:

``make grunt``

directory structure
~~~~~~~~~~~~~~~~~~~

see:

- gruntfile.js
- package.json

*************
css directory
*************

- ``bootstrap*``: bootstrap NPM package,
- ``leaflet.*``: leaflet NPM package
- ``leaflet.min.css``: minimized version of ``leaflet.css`` (see gruntfile.js)
- ``logicodev.*``: compiled from ``src/less/logicodev``
- ``logicodev-dark*``: compiled from ``src/less/logicodev-dark``
- ``pointhi*``: compiled from ``src/less/pointhi``
- ``images``: leaflet NPM package

**************
font directory
**************

- from bootstrap NPM package

************
js directory
************

- ``searxng.*``: compiled from ``src/js``
- other files are from NPM packages

*************
img directory
*************

- images for the oscar theme
